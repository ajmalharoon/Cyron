"""ProjectDiscovery subfinder — fast passive-source subdomain enumeration."""
from app.recon.base import FindingDraft, ToolRunner, json_lines


class SubfinderRunner(ToolRunner):
    name = "subfinder"
    binary = "subfinder"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, "-d", target, "-json", "-silent"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for row in json_lines(stdout):
            host = row.get("host")
            if host:
                out.append(FindingDraft(
                    title=f"Subdomain discovered: {host}",
                    description=f"subfinder found the subdomain {host} via public sources.",
                ))
        return out
