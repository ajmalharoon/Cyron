"""Censys — second internet-wide exposure search engine, cross-checked
against Shodan and FOFA for assets the organisation may not know about."""
import json

import httpx

from app.config import get_settings
from app.recon.base import ApiToolRunner, FindingDraft


class CensysRunner(ApiToolRunner):
    name = "Censys"

    def is_available(self) -> bool:
        s = get_settings()
        return bool(s.censys_api_id and s.censys_api_secret)

    async def fetch(self, target: str) -> tuple[str, int]:
        s = get_settings()
        async with httpx.AsyncClient(timeout=20, auth=(s.censys_api_id, s.censys_api_secret)) as client:
            resp = await client.get(
                "https://search.censys.io/api/v2/hosts/search",
                params={"q": target},
            )
            return resp.text, resp.status_code

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return out
        for hit in data.get("result", {}).get("hits", []):
            out.append(FindingDraft(
                title=f"Censys: {hit.get('ip')}",
                description=f"Censys lists a certificate or service for {target} at {hit.get('ip')}.",
            ))
        return out
