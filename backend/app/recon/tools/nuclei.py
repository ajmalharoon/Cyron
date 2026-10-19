"""ProjectDiscovery nuclei — template-driven vulnerability scanner. The
template severity is trusted directly rather than re-derived."""
from app.recon.base import FindingDraft, ToolRunner, json_lines


class NucleiRunner(ToolRunner):
    name = "Nuclei"
    binary = "nuclei"

    def build_command(self, target: str) -> list[str]:
        base = target if target.startswith("http") else f"https://{target}"
        return [self.binary, "-u", base, "-jsonl", "-silent"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for row in json_lines(stdout):
            info = row.get("info", {})
            out.append(FindingDraft(
                title=info.get("name", "Nuclei finding"),
                description=f"The template {row.get('template-id')} matched on {row.get('matched-at', target)}.",
                severity=info.get("severity", "info"),
                recommendation=(info.get("remediation") or "").strip() or None,
            ))
        return out
