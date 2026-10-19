"""OWASP ZAP — API client against the `zap` container's daemon (the
official zaproxy/zap-stable image, run as its own docker-compose service —
see tool-services' note in docker-compose.yml). Reused by both the
API-reconnaissance phase (--spider only, to enumerate routes) and the
web-security-analysis phase (--full with the active scanner), selected by
the `active_scan` flag."""
import httpx

from app.recon.base import ApiToolRunner, FindingDraft
from app.config import get_settings

SEVERITY_MAP = {"3": "high", "2": "medium", "1": "low", "0": "info"}


class ZapRunner(ApiToolRunner):
    name = "OWASP ZAP"
    zap_base = "http://zap:8080"

    def __init__(self, active_scan: bool = False):
        self.active_scan = active_scan
        self.name = "OWASP ZAP (active scan)" if active_scan else "OWASP ZAP (spider)"

    def is_available(self) -> bool:
        try:
            httpx.get(f"{self.zap_base}/JSON/core/view/version/", timeout=2)
            return True
        except httpx.HTTPError:
            return False

    async def fetch(self, target: str) -> tuple[str, int]:
        base = target if target.startswith("http") else f"https://{target}"
        async with httpx.AsyncClient(timeout=60) as client:
            await client.get(f"{self.zap_base}/JSON/spider/action/scan/", params={"url": base})
            if self.active_scan:
                await client.get(f"{self.zap_base}/JSON/ascan/action/scan/", params={"url": base})
            resp = await client.get(f"{self.zap_base}/JSON/core/view/alerts/", params={"baseurl": base})
            return resp.text, resp.status_code

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        import json
        out = []
        try:
            alerts = json.loads(stdout).get("alerts", [])
        except json.JSONDecodeError:
            return out
        for a in alerts:
            out.append(FindingDraft(
                title=a.get("alert", "ZAP alert"),
                description=a.get("description", "")[:400] or f"ZAP raised an alert on {target}.",
                severity=SEVERITY_MAP.get(str(a.get("risk", "0")), "info"),
                recommendation=(a.get("solution") or "")[:300] or None,
            ))
        return out
