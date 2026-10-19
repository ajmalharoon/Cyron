"""GetAllUrls — Cyron's second historical-URL source, backed by
tomnomnom/waybackurls, which queries the Wayback Machine's CDX API directly."""
from app.recon.base import FindingDraft, ToolRunner


class GetAllUrlsRunner(ToolRunner):
    name = "GetAllUrls"
    binary = "waybackurls"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, target]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        return [
            FindingDraft(
                title=f"Archived URL: {url.strip()}",
                description=f"GetAllUrls found {url.strip()} in the Wayback Machine's archive.",
            )
            for url in stdout.splitlines() if url.strip()
        ]
