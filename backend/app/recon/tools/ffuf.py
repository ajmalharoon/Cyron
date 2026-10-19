"""ffuf — fast web fuzzer, used here for directory/file discovery against a
wordlist. Reports anything that doesn't 404."""
import json

from app.recon.base import FindingDraft, ToolRunner

SENSITIVE = {"admin", ".git", ".env", "backup", "config"}


class FfufRunner(ToolRunner):
    name = "ffuf"
    binary = "ffuf"
    wordlist = "/usr/share/wordlists/dirb/common.txt"

    def build_command(self, target: str) -> list[str]:
        base = target if target.startswith("http") else f"https://{target}"
        return [self.binary, "-u", f"{base}/FUZZ", "-w", self.wordlist, "-of", "json", "-o", "-", "-s"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            data = json.loads(stdout or "{}")
        except json.JSONDecodeError:
            return out
        for r in data.get("results", []):
            path, status = r.get("input", {}).get("FUZZ", ""), r.get("status")
            hit = any(s in path.lower() for s in SENSITIVE)
            out.append(FindingDraft(
                title=f"Path found: /{path} ({status})",
                description=f"ffuf found /{path} on {target}, which answered with status {status}.",
                severity="medium" if hit else "info",
                recommendation="Restrict this path or confirm it should be public." if hit else None,
            ))
        return out
