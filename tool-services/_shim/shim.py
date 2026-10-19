#!/usr/bin/env python3
"""Generic tool-runner shim, identical in every tool container. It exposes
one tiny HTTP API over a CLI binary already installed in that image:

    GET  /health            -> {"status": "ok", "tool": "<name>"}
    POST /run {"args": [...], "timeout": 300}
                             -> {"stdout": "...", "stderr": "...", "returncode": 0}

The backend's ToolRunner.build_command() already returns the exact argv
(binary name included) that used to be passed to a local subprocess — this
shim runs that same argv inside the tool's own container instead, so no
tool module's build_command()/parse() needed to change. Deliberately
stdlib-only (no Flask/FastAPI) so every one of the ~25 tool images stays
small and has nothing extra to install.

Trust model: this shim executes whatever argv it's given, with no allow-
list. That's intentional and unchanged from before — Cyron is a single-
operator tool, and the backend was always trusted to decide what runs.
Putting each tool in its own container is about dependency isolation
(mismatched Go/Python/Ruby toolchains, one tool's install breaking
another's) and resource isolation, not about sandboxing the backend
itself. Do not expose a tool container's port outside the compose
network (the provided docker-compose.yml never publishes one to the
host) and do not point CYRON_API_BASE or these tool services at anything
other than a trusted backend.
"""
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOOL_NAME = os.environ.get("CYRON_TOOL_NAME", "tool")
DEFAULT_TIMEOUT = int(os.environ.get("CYRON_TOOL_TIMEOUT", "300"))


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 (stdlib's naming convention)
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "tool": TOOL_NAME})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if self.path != "/run":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON body"})
            return

        args = body.get("args")
        if not isinstance(args, list) or not args:
            self._send_json(400, {"error": "'args' must be a non-empty list"})
            return
        timeout = body.get("timeout") or DEFAULT_TIMEOUT

        try:
            proc = subprocess.run(args, capture_output=True, timeout=timeout, text=True)
            self._send_json(200, {
                "stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode,
            })
        except subprocess.TimeoutExpired:
            self._send_json(200, {"error": f"{TOOL_NAME} timed out after {timeout}s"})
        except FileNotFoundError as exc:
            self._send_json(200, {"error": f"{TOOL_NAME} binary not found: {exc}"})
        except Exception as exc:  # noqa: BLE001 — report, never crash the shim
            self._send_json(200, {"error": f"{TOOL_NAME} failed: {exc}"})

    def log_message(self, fmt, *args):  # quiet, structured-ish access log
        print(f"[{TOOL_NAME}] {self.address_string()} {fmt % args}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"[{TOOL_NAME}] shim listening on :{port}")
    server.serve_forever()
