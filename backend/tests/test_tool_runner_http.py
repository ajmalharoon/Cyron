"""ToolRunner.run() now calls a sibling container's HTTP shim instead of
spawning a local subprocess. These tests fake that HTTP call (no real
network, no real container) to check the three paths that matter: a normal
successful run, the tool's own container reporting an error, and the
container being unreachable."""
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.recon.base import FindingDraft, ToolRunner


class _EchoRunner(ToolRunner):
    """A minimal concrete ToolRunner for exercising the base class's run()
    without depending on any real tool module."""
    name = "Echo"
    binary = "echo"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, target]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        return [FindingDraft(title="saw output", description=stdout.strip())]


def _fake_response(json_body: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, json=json_body, request=httpx.Request("POST", "http://echo:8080/run"))


@pytest.mark.asyncio
async def test_run_parses_a_successful_shim_response():
    runner = _EchoRunner()
    fake = _fake_response({"stdout": "hello target.example", "stderr": "", "returncode": 0})
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        result = await runner.run("target.example")
    assert result.ran is True
    assert result.error is None
    assert len(result.findings) == 1
    assert result.findings[0].description == "hello target.example"


@pytest.mark.asyncio
async def test_run_surfaces_a_shim_reported_error():
    runner = _EchoRunner()
    fake = _fake_response({"error": "echo binary not found: [Errno 2] No such file or directory"})
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake)):
        result = await runner.run("target.example")
    assert result.ran is False
    assert "not found" in result.error


@pytest.mark.asyncio
async def test_run_handles_an_unreachable_container():
    runner = _EchoRunner()
    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=httpx.ConnectError("refused"))):
        result = await runner.run("target.example")
    assert result.ran is False
    assert "unreachable" in result.error
    assert "echo" in result.error
