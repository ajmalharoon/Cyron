"""Masscan — very fast, internet-scale port scanner. Used here for broad
coverage across large ranges before Nmap/Naabu narrow in."""
import json

from app.recon.base import FindingDraft, ToolRunner


class MasscanRunner(ToolRunner):
    name = "Masscan"
    binary = "masscan"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, target, "-p1-65535", "--rate", "1000", "-oJ", "-"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            rows = json.loads(stdout or "[]")
        except json.JSONDecodeError:
            return out
        for row in rows:
            for p in row.get("ports", []):
                out.append(FindingDraft(
                    title=f"Port {p.get('port')}/{p.get('proto')} open",
                    description=f"masscan found port {p.get('port')}/{p.get('proto')} open on {target}.",
                ))
        return out
