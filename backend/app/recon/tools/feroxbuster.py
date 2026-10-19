"""Feroxbuster — recursive content discovery, complementing ffuf/Gobuster
with automatic recursion into discovered directories."""
import json

from app.recon.base import FindingDraft, ToolRunner


class FeroxbusterRunner(ToolRunner):
    name = "Feroxbuster"
    binary = "feroxbuster"
    wordlist = "/usr/share/wordlists/dirb/common.txt"

    def build_command(self, target: str) -> list[str]:
        base = target if target.startswith("http") else f"https://{target}"
        return [self.binary, "-u", base, "-w", self.wordlist, "--json", "-q"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for line in stdout.splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("type") == "response":
                out.append(FindingDraft(
                    title=f"Path found: {row.get('url')} ({row.get('status')})",
                    description=f"Feroxbuster found {row.get('url')}, status {row.get('status')}.",
                ))
        return out
