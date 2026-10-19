"""ProjectDiscovery katana — crawler built for API/endpoint discovery,
following JS-rendered links that a plain crawler would miss."""
from app.recon.base import FindingDraft, ToolRunner


class KatanaRunner(ToolRunner):
    name = "Katana"
    binary = "katana"

    def build_command(self, target: str) -> list[str]:
        base = target if target.startswith("http") else f"https://{target}"
        return [self.binary, "-u", base, "-silent", "-jc"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        return [
            FindingDraft(
                title=f"Endpoint crawled: {url.strip()}",
                description=f"Katana found {url.strip()} while crawling {target}.",
            )
            for url in stdout.splitlines() if url.strip()
        ]
