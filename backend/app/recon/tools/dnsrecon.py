"""DNSRecon — standard DNS enumeration, including a zone-transfer check,
which is the main thing Cyron highlights from its output."""
from app.recon.base import FindingDraft, ToolRunner


class DnsReconRunner(ToolRunner):
    name = "DNSRecon"
    binary = "dnsrecon"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, "-d", target, "-a"]  # -a: also attempt zone transfer

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        if "AXFR" in stdout and "failed" not in stdout.lower():
            out.append(FindingDraft(
                title="DNS zone transfer succeeded",
                description=f"A name server for {target} allowed a zone transfer (AXFR), which lists every "
                             "record in the zone to anyone who asks.",
                severity="high",
                recommendation="Restrict zone transfers to known secondary name servers only.",
            ))
        else:
            out.append(FindingDraft(
                title="DNS zone transfer refused",
                description=f"Name servers for {target} refused a zone transfer, which is the expected behaviour.",
            ))
        return out
