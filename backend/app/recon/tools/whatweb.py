"""WhatWeb — technology fingerprinting (server, CMS, JS frameworks, versions)."""
import json

from app.recon.base import FindingDraft, ToolRunner


class WhatWebRunner(ToolRunner):
    name = "WhatWeb"
    binary = "whatweb"

    def build_command(self, target: str) -> list[str]:
        base = target if target.startswith("http") else f"https://{target}"
        return [self.binary, "--log-json=-", base]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for line in stdout.splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            for plugin, detail in row.get("plugins", {}).items():
                version = (detail.get("version") or [""])[0] if isinstance(detail, dict) else ""
                out.append(FindingDraft(
                    title=f"Technology identified: {plugin}" + (f" {version}" if version else ""),
                    description=f"WhatWeb identified {plugin}{' version ' + version if version else ''} on {target}.",
                ))
        return out
