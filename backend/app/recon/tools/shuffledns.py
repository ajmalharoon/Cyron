"""ProjectDiscovery shuffleDNS — massively parallel DNS resolution/brute-force,
layered on massdns. Used here to confirm which discovered subdomains resolve."""
from app.recon.base import FindingDraft, ToolRunner


class ShuffleDnsRunner(ToolRunner):
    name = "shuffleDNS"
    binary = "shuffledns"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, "-d", target, "-silent"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        return [
            FindingDraft(
                title=f"Resolved host: {line.strip()}",
                description=f"shuffleDNS confirmed that {line.strip()} resolves.",
            )
            for line in stdout.splitlines() if line.strip()
        ]
