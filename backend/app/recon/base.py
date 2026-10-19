"""Shared contract every tool module implements, plus the HTTP-backed
runner most of them use. A tool module is deliberately small: it only
describes how to build a command line and how to turn that tool's output
into FindingDrafts. Everything else (the call to the tool's own container,
timeouts, logging, persistence) lives here so it's identical for every
tool.

Every recon tool (nmap, amass, subfinder, ...) runs in its own container —
see /tool-services/ and docker-compose.yml — reached over HTTP through the
generic shim every one of those images runs (/tool-services/_shim/shim.py).
build_command() still returns the exact argv it always did; ToolRunner.run()
just sends that argv to http://<binary>:8080/run instead of spawning it as a
local subprocess. The compose network's service name for a tool is its
binary name (e.g. "nmap", "amass", "subfinder"), which is also the value of
each ToolRunner subclass's `binary` attribute, so no extra per-tool wiring
is needed to find the right container."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import httpx

from app.config import get_settings
from app.utils.logger import get_logger

log = get_logger(__name__)

TOOL_SERVICE_PORT = 8080


@dataclass
class FindingDraft:
    title: str
    description: str
    severity: str = "info"  # info | low | medium | high
    recommendation: str | None = None
    raw: str | None = None


@dataclass
class ToolResult:
    tool: str
    ran: bool
    findings: list[FindingDraft] = field(default_factory=list)
    error: str | None = None


class ToolRunner:
    """Base class for a tool that runs in its own container. Subclass and
    implement build_command() + parse() — exactly as before; only where the
    command actually executes has changed. For an API-backed source
    (Shodan, Censys, FOFA, NVD) subclass ApiToolRunner instead."""

    name: str = "tool"
    binary: str = "tool"

    def build_command(self, target: str) -> list[str]:
        raise NotImplementedError

    def parse(self, stdout: str, stderr: str, returncode: int, target: str) -> list[FindingDraft]:
        raise NotImplementedError

    async def run(self, target: str) -> ToolResult:
        settings = get_settings()
        cmd = self.build_command(target)
        url = f"http://{self.binary}:{TOOL_SERVICE_PORT}/run"
        log.info("tool.start", extra={"tool": self.name, "cmd": " ".join(cmd), "service": self.binary})

        try:
            async with httpx.AsyncClient(timeout=settings.tool_timeout_seconds + 15) as client:
                resp = await client.post(url, json={"args": cmd, "timeout": settings.tool_timeout_seconds})
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError:
            log.warning("tool.unavailable", extra={"tool": self.name, "service": self.binary})
            return ToolResult(
                tool=self.name, ran=False,
                error=f"the {self.binary} service is unreachable — is it running in docker compose?",
            )
        except httpx.HTTPError as exc:
            log.error("tool.error", extra={"tool": self.name, "error": str(exc)})
            return ToolResult(tool=self.name, ran=False, error=str(exc))

        if data.get("error"):
            log.warning("tool.failed", extra={"tool": self.name, "error": data["error"]})
            return ToolResult(tool=self.name, ran=False, error=data["error"])

        stdout, stderr, returncode = data.get("stdout", ""), data.get("stderr", ""), data.get("returncode", 0)
        try:
            findings = self.parse(stdout, stderr, returncode, target)
        except Exception as exc:  # a parser bug should not fail the whole scan
            log.error("tool.parse_error", extra={"tool": self.name, "error": str(exc)})
            return ToolResult(tool=self.name, ran=True, error=f"parse error: {exc}")

        log.info("tool.done", extra={"tool": self.name, "findings": len(findings)})
        return ToolResult(tool=self.name, ran=True, findings=findings)


class ApiToolRunner(ToolRunner):
    """Base for tools that are really an HTTP API client (Shodan, Censys,
    FOFA, NVD). Subclass and implement is_available() (check the relevant
    API key is set) and fetch(). run() is overridden so no subprocess is
    spawned."""

    async def fetch(self, target: str) -> tuple[str, int]:
        raise NotImplementedError

    async def run(self, target: str) -> ToolResult:
        if not self.is_available():
            log.warning("tool.unavailable", extra={"tool": self.name})
            return ToolResult(tool=self.name, ran=False, error="API key not configured")
        try:
            body, status = await self.fetch(target)
        except Exception as exc:
            log.error("tool.api_error", extra={"tool": self.name, "error": str(exc)})
            return ToolResult(tool=self.name, ran=False, error=str(exc))
        try:
            findings = self.parse(body, "", status, target)
        except Exception as exc:
            return ToolResult(tool=self.name, ran=True, error=f"parse error: {exc}")
        return ToolResult(tool=self.name, ran=True, findings=findings)


def json_lines(text: str) -> list[dict]:
    """Parse newline-delimited JSON, skipping any line that isn't valid
    JSON (many Go recon tools print one JSON object per line with --json)."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows
