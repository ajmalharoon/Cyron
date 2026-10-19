"""FOFA — third internet-wide exposure search engine, mainly useful for
coverage of assets hosted in networks the other two index less completely."""
import base64
import json

import httpx

from app.config import get_settings
from app.recon.base import ApiToolRunner, FindingDraft


class FofaRunner(ApiToolRunner):
    name = "FOFA"

    def is_available(self) -> bool:
        s = get_settings()
        return bool(s.fofa_email and s.fofa_api_key)

    async def fetch(self, target: str) -> tuple[str, int]:
        s = get_settings()
        qbase64 = base64.b64encode(f'host="{target}"'.encode()).decode()
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                "https://fofa.info/api/v1/search/all",
                params={"email": s.fofa_email, "key": s.fofa_api_key, "qbase64": qbase64},
            )
            return resp.text, resp.status_code

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return out
        for row in data.get("results", []):
            ip = row[0] if row else "unknown"
            out.append(FindingDraft(
                title=f"FOFA: {ip}",
                description=f"FOFA lists an asset for {target} at {ip}.",
                severity="medium",
                recommendation="Confirm this asset is in your inventory, or take it down.",
            ))
        return out
