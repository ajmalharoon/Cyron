# Cyron architecture

## Overview

Cyron is four pieces: a static frontend, a FastAPI backend, Postgres, and a
container per recon tool. The frontend never talks to a recon tool
directly, and as of this build, neither does the backend as a local
subprocess — every scan goes through the backend, which owns the database
and the report, and calls out to each tool's own container over HTTP.

```
┌────────────┐     REST + WebSocket     ┌─────────────┐      asyncpg      ┌────────────┐
│  frontend  │ ───────────────────────▶ │   backend   │ ─────────────────▶│  postgres  │
│  (nginx,   │ ◀─────────────────────── │  (FastAPI)  │ ◀──────────────── │            │
│  static)   │                          └──────┬──────┘                   └────────────┘
└────────────┘                                 │
                                        HTTP, one call per tool
                                                │
              ┌─────────────────────────────────┴─────────────────────────────────┐
              │  27 tool containers (tool-services/), each: shim.py + one binary   │
              │  nmap · amass · subfinder · nuclei · gitleaks · kube-bench · ...   │
              │  + zap (official zaproxy/zap-stable image, its own daemon API)     │
              │  + Shodan · Censys · FOFA · NVD — outbound API calls, no container │
              └──────────────────────────────────────────────────────────────────┘
```

## Why one container per tool

The backend used to spawn every recon tool as a local subprocess inside its
own image. That collapsed under the tools' combined dependencies: Go
binaries, a Ruby gem, Rust via cargo, Python scripts cloned from GitHub,
and a couple of prebuilt release binaries, all wanting their own base image
and toolchain. One shared image meant either a bloated image with every
toolchain installed, or constant version collisions between them.

Splitting each tool into its own container sidesteps that entirely — each
image only ever needs its own tool's dependencies — at the cost of 27
images to build and 27 services in `docker-compose.yml`. Every one of those
images runs the exact same file, `tool-services/_shim/shim.py`: a small,
dependency-free HTTP server (stdlib only, no Flask/FastAPI, so it adds
nothing to any image) exposing:

```
GET  /health            -> {"status": "ok", "tool": "<name>"}
POST /run {"args": [...], "timeout": 300}
                         -> {"stdout": "...", "stderr": "...", "returncode": 0}
```

`ToolRunner.build_command(target)` still returns the exact argv it always
did (binary name included) — `ToolRunner.run()` just POSTs that argv to
`http://<binary>:8080/run` instead of spawning it locally, then calls the
same `self.parse(stdout, stderr, returncode, target)` as before. No tool
module's `build_command()` or `parse()` needed to change for this; only
`run()` on the shared base class did.

**The compose service name must equal the tool's `binary` attribute** —
that's the hostname Docker's embedded DNS resolves and the one
`ToolRunner.run()` looks up. For 25 of the 27 tools the obvious name and
the binary are the same thing (`nmap`, `amass`, `subfinder`, ...). Two
aren't: Kiterunner's own release ships a binary literally named `kr`
(`KiterunnerRunner.binary = "kr"`), and ScoutSuite's installs as `scout`
(`ScoutSuiteRunner.binary = "scout"`) — so in `docker-compose.yml` those
services are named `kr` and `scout`, built from the `tool-services/kiterunner/`
and `tool-services/scoutsuite/` directories respectively. The directory name
is just where the Dockerfile lives; the service name is what has to match.

**Trust model, unchanged.** The shim executes whatever argv it's given,
with no allow-list — that's the same trust the backend always had when it
spawned these as local subprocesses; putting each tool in its own container
is about dependency and resource isolation, not about sandboxing the
backend. None of the 27 tool services (or `zap`) publish a port to the
host in the provided compose file — only the backend, on the same compose
network, can reach them.

**Four tools install a pinned release binary**, not "latest": `gitleaks`,
`trufflehog`, `kube-bench`, and `kiterunner` all ship as GitHub release
tarballs with no stable "latest" download URL that resolves predictably
inside a Dockerfile `RUN` layer, so each Dockerfile pins an exact version
that was confirmed to actually download when this project was built
(2026-10). `kube-bench`'s tarball also ships a `cfg/` directory of CIS
benchmark policy YAML files it reads at runtime relative to its own working
directory — that Dockerfile extracts the whole tarball and sets `WORKDIR`
accordingly, not just the binary.

## Request lifecycle

1. The operator fills in the target field, confirms authorization, picks
   Active or Passive (or runs both), and optionally deselects individual
   tool chips per phase. The frontend calls `POST /api/scans` with that
   selection as `tools: {phase_id: [tool_label, ...]}` — a phase absent
   from that map runs every tool it has.
2. The backend creates a `Target` (if new) and a `ScanRun` row with
   `status="pending"`, and schedules `recon.runner.run_scan()` as a
   background task. The request returns immediately with the new scan's id.
3. `run_scan()` walks `recon/registry.py`'s `PHASES` list in order, filtered
   to the scan's selected modes and, if given, the tool selection. For each
   phase it creates a `PhaseResult` row, calls each selected tool's
   container over HTTP, and persists each tool's findings as `Finding` rows
   as they're parsed — one tool's failure (a parse error, a container
   that's down) never blocks the rest of the phase or the scan.
4. Every phase/tool transition is published on `core.events.bus`, which fans
   it out to anyone subscribed to `WS /ws/scans/{id}` — this is what drives
   the frontend's live run log.
5. The frontend separately polls `GET /api/scans/{id}` every ~1.2s for
   authoritative phase status (the socket is for human-readable log lines,
   not state sync — if the socket drops, polling still gets you to a
   correct final state).
6. Once `status="completed"`, the frontend fetches `GET
   /api/scans/{id}/findings` and `GET /api/scans/{id}/report`, and renders
   the 3D/2D maps and the report.

## Why findings aren't tagged with their phase in the API

`FindingOut` intentionally doesn't carry a `phase_id` — the findings table's
only foreign key is to `phase_result_id`, and the API exposes findings as a
flat, scan-wide list ordered by creation time. The frontend reconstructs the
phase → findings grouping itself, by matching each finding's `created_at`
against the `[started_at, finished_at]` window of each `PhaseResult` (also
returned on `GET /api/scans/{id}`). This works exactly, not approximately,
because `run_scan()` runs phases strictly sequentially — no two phases are
ever open at once, so every finding's timestamp falls inside exactly one
phase's window. If the runner ever becomes concurrent (see below), this
grouping would need to move to the API instead.

## The tool framework

Every tool module in `backend/app/recon/tools/` subclasses one of two base
classes in `backend/app/recon/base.py`:

- **`ToolRunner`** — calls the tool's own container. A subclass implements
  `build_command(target)` (the argv list) and `parse(stdout, stderr,
  returncode, target)` (turns tool output into `FindingDraft`s). The base
  class's `run()` POSTs that argv to `http://<binary>:8080/run`, handles
  the container being unreachable or timing out, and turns an unexpected
  parse exception into a logged, non-fatal `ToolResult` rather than
  crashing the scan.
- **`ApiToolRunner`** — same contract, but for tools that are really an HTTP
  API client (Shodan, Censys, FOFA, the NVD CVE database, OWASP ZAP's
  daemon). Subclasses implement `fetch(target)` instead of a command line,
  and `run()` calls `fetch()` directly rather than any tool container.

`recon/registry.py` is the only place that wires a tool to a phase. Adding a
tool that needs its own container means: write the module, add a matching
Dockerfile under `tool-services/<name>/` whose compose service name equals
the module's `binary` attribute, add one line to the matching `Phase(...)`
entry in the registry, and add the service to `docker-compose.yml`. Nothing
else — the API, the job runner, and the frontend all read the registry, so
a new tool just appears as a chip in its phase.

## Severity and the exposure score

Severity (`high` / `medium` / `low` / `info`) comes from each tool's own
parser — either passed straight through (Nuclei's template severity, ZAP's
risk rating) or assigned by a small, documented heuristic (an open port on
a watch-list, a secret-shaped string, an expiring certificate). The scan's
exposure score is `min(100, high×14 + medium×6 + low×2)`, computed once in
`recon/runner.py` and again, identically, in `reports/generator.py`. Both
are Cyron's own judgement, not CVSS — the report's own "Risk rating method"
and "Limitations" sections say so explicitly, and an analyst should confirm
every finding before acting on it.

## Known limitations / where to harden next

- **Background tasks, not a queue.** `BackgroundTasks` runs the scan in the
  same process as the API. That's fine for one operator; for concurrent
  multi-user scans, move `run_scan()` to a real queue (Celery/RQ + Redis)
  so a slow scan can't starve the API event loop.
- **Single in-memory event bus.** `core/events.py` only works within one
  backend process. Running more than one backend replica needs Redis
  pub/sub (or similar) instead.
- **Single operator key.** `core/security.py` is a single bearer token, not
  a user system. Put Cyron behind your own auth layer for multi-user use.
- **Parsers are a starting point.** Tool output formats drift between
  versions; the parsers here cover the common case (JSON output where a
  tool supports `--json`, line-based otherwise) and should be hardened
  against the actual installed tool versions before relying on them outside
  a lab.
- **27 images is a real build cost.** First `docker compose build` compiles
  several Go/Rust toolchains from source and will take a while; after that,
  Docker's layer cache makes it fast. Pinned release versions (gitleaks,
  trufflehog, kube-bench, kiterunner) will eventually go stale — bump the
  version in that tool's Dockerfile when you need something newer.
- **naabu and masscan want raw sockets.** Both are given `NET_ADMIN` and
  `NET_RAW` in `docker-compose.yml` for their SYN-scan modes; without those
  capabilities (e.g. on a platform that won't grant them) they fall back to
  a slower connect-scan rather than failing outright.
