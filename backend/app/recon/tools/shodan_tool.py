"""Shodan — internet-wide exposure search, used to see what Shodan already
knows about the target without sending it any traffic ourselves."""
import json

import httpx

from app.config import get_settings
from app.recon.base import ApiToolRunner, FindingDraft


class ShodanRunner(ApiToolRunner):
    name = "Shodan"

    def is_available(self) -> bool:
        return bool(get_settings().shodan_api_key)

    async def fetch(self, target: str) -> tuple[str, int]:
        key = get_settings().shodan_api_key
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                "https://api.shodan.io/shodan/host/search",
                params={"key": key, "query": f"hostname:{target}"},
            )
            return resp.text, resp.status_code

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return out
        for match in data.get("matches", []):
            out.append(FindingDraft(
                title=f"Shodan: {match.get('ip_str')}:{match.get('port')}",
                description=f"Shodan lists {match.get('ip_str')}:{match.get('port')} for {target}, "
                             f"running {match.get('product', 'an unidentified service')}.",
            ))
        return out
