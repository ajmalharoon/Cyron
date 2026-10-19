"""CVE and vulnerability intelligence — queries the NVD REST API directly
(covers "NVD data" and "CVE database" from the project brief, which are the
same underlying source) for CVEs matching a product/version string."""
import json

import httpx

from app.config import get_settings
from app.recon.base import ApiToolRunner, FindingDraft

SEV_MAP = {"CRITICAL": "high", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}


class CveIntelRunner(ApiToolRunner):
    name = "NVD / CVE database"

    def is_available(self) -> bool:
        return True  # NVD's public API works without a key, just rate-limited

    async def fetch(self, target: str) -> tuple[str, int]:
        settings = get_settings()
        headers = {"apiKey": settings.nvd_api_key} if settings.nvd_api_key else {}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0",
                params={"keywordSearch": target, "resultsPerPage": 10},
                headers=headers,
            )
            return resp.text, resp.status_code

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return out
        for item in data.get("vulnerabilities", []):
            cve = item.get("cve", {})
            cve_id = cve.get("id", "CVE-unknown")
            descs = cve.get("descriptions", [{}])
            summary = next((d["value"] for d in descs if d.get("lang") == "en"), "")
            metrics = cve.get("metrics", {})
            sev = "info"
            for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                if key in metrics:
                    sev = SEV_MAP.get(metrics[key][0]["cvssData"].get("baseSeverity", ""), "info")
                    break
            out.append(FindingDraft(
                title=cve_id,
                description=f"{cve_id}: {summary[:250]}",
                severity=sev,
                recommendation="Patch the affected component to a version that fixes this CVE.",
            ))
        return out
