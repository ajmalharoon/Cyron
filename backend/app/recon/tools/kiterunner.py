"""Kiterunner — API-route bruteforcer that matches requests against known
OpenAPI route wordlists, good at finding undocumented API endpoints."""
from app.recon.base import FindingDraft, ToolRunner


class KiterunnerRunner(ToolRunner):
    name = "kiterunner"
    binary = "kr"
    wordlist = "/usr/share/kiterunner/routes-large.kite"

    def build_command(self, target: str) -> list[str]:
        base = target if target.startswith("http") else f"https://{target}"
        return [self.binary, "scan", base, "-w", self.wordlist, "-x", "20"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit():
                out.append(FindingDraft(
                    title=f"API route found: {parts[-1]} ({parts[0]})",
                    description=f"kiterunner found the route {parts[-1]} on {target}, status {parts[0]}.",
                ))
        return out
