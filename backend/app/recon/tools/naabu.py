"""ProjectDiscovery naabu — fast SYN/CONNECT port scanner, used for a quick
first pass before Nmap does the detailed service scan."""
from app.recon.base import FindingDraft, ToolRunner, json_lines


class NaabuRunner(ToolRunner):
    name = "Naabu"
    binary = "naabu"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, "-host", target, "-json", "-silent"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for row in json_lines(stdout):
            port = row.get("port")
            if port:
                out.append(FindingDraft(
                    title=f"Port {port}/tcp open",
                    description=f"naabu found port {port} open on {row.get('host', target)}.",
                ))
        return out
