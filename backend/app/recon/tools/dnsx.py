"""ProjectDiscovery dnsx — DNS resolution and record lookups. Reused for
both asset/subdomain discovery (resolve candidate hosts) and DNS recon
(pull record types) depending on the extra_args passed by the registry."""
from app.recon.base import FindingDraft, ToolRunner, json_lines


class DnsxRunner(ToolRunner):
    name = "dnsx"
    binary = "dnsx"

    def __init__(self, record_types: list[str] | None = None):
        self.record_types = record_types or ["a", "mx", "txt", "ns"]

    def build_command(self, target: str) -> list[str]:
        flags = [f"-{t}" for t in self.record_types]
        return [self.binary, "-d", target, *flags, "-json", "-silent"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for row in json_lines(stdout):
            for rtype in self.record_types:
                values = row.get(rtype)
                if not values:
                    continue
                for v in values if isinstance(values, list) else [values]:
                    sev = "low" if rtype == "txt" and "dmarc" not in str(v).lower() else "info"
                    out.append(FindingDraft(
                        title=f"{rtype.upper()} record: {v}",
                        description=f"dnsx resolved a {rtype.upper()} record for {row.get('host', target)}: {v}.",
                        severity=sev,
                    ))
        return out
