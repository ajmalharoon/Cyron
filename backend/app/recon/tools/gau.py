"""GAU (getallurls by lc) — pulls known URLs for a domain from sources like
the Wayback Machine, Common Crawl and AlienVault OTX."""
from app.recon.base import FindingDraft, ToolRunner

SENSITIVE_HINTS = ("admin", "backup", ".git", ".env", "config", ".sql", ".zip")


class GauRunner(ToolRunner):
    name = "GAU"
    binary = "gau"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, target]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for url in {u.strip() for u in stdout.splitlines() if u.strip()}:
            hit = any(h in url.lower() for h in SENSITIVE_HINTS)
            out.append(FindingDraft(
                title=f"Historical URL: {url}",
                description=f"GAU found {url} in historical/archive sources.",
                severity="medium" if hit else "info",
                recommendation="Confirm this path is no longer reachable, or restrict it." if hit else None,
            ))
        return out
