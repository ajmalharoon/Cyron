"""Gobuster — the third content-discovery tool in the rotation, run in dir mode."""
from app.recon.base import FindingDraft, ToolRunner


class GobusterRunner(ToolRunner):
    name = "Gobuster"
    binary = "gobuster"
    wordlist = "/usr/share/wordlists/dirb/common.txt"

    def build_command(self, target: str) -> list[str]:
        base = target if target.startswith("http") else f"https://{target}"
        return [self.binary, "dir", "-u", base, "-w", self.wordlist, "-q"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("/"):
                out.append(FindingDraft(
                    title=f"Path found: {line.split(' ')[0]}",
                    description=f"Gobuster found {line} on {target}.",
                ))
        return out
