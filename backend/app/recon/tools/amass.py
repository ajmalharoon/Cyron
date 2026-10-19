"""OWASP Amass — active subdomain & asset enumeration (passive sources too,
but Cyron runs it in Active mode since it can also brute-force and resolve)."""
from app.recon.base import FindingDraft, ToolRunner, json_lines


class AmassRunner(ToolRunner):
    name = "OWASP Amass"
    binary = "amass"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, "enum", "-d", target, "-json", "-passive"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for row in json_lines(stdout):
            name = row.get("name")
            if not name:
                continue
            hot = name.split(".")[0] in {"dev", "staging", "test", "old", "backup", "internal"}
            out.append(FindingDraft(
                title=f"Subdomain discovered: {name}",
                description=f"Amass resolved the subdomain {name}.",
                severity="medium" if hot else "info",
                recommendation="Confirm this subdomain is still needed and keep an inventory of owned assets."
                if hot else None,
            ))
        return out
