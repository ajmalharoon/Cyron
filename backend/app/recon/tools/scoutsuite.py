"""ScoutSuite — multi-cloud security auditor (AWS, Azure, GCP). Reused for
both the AWS-specific phase and the multi-cloud phase, selected by `provider`."""
import json

from app.recon.base import FindingDraft, ToolRunner

LEVEL_MAP = {"danger": "high", "warning": "medium", "good": "info"}


class ScoutSuiteRunner(ToolRunner):
    name = "ScoutSuite"
    binary = "scout"

    def __init__(self, provider: str = "aws"):
        self.provider = provider
        self.name = f"ScoutSuite ({provider})"

    def build_command(self, target: str) -> list[str]:
        # `target` here is a profile/subscription/project id, not a hostname.
        return [self.binary, self.provider, "--profile" if self.provider == "aws" else "--project-id", target,
                "--report-dir", "-", "--no-browser"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            data = json.loads(stdout or "{}")
        except json.JSONDecodeError:
            return out
        for finding_id, finding in data.get("findings", {}).items():
            level = finding.get("level", "good")
            if level == "good":
                continue
            out.append(FindingDraft(
                title=finding.get("description", finding_id),
                description=f"ScoutSuite ({self.provider}) flagged {finding.get('description', finding_id)} "
                             f"affecting {len(finding.get('items', []))} resource(s).",
                severity=LEVEL_MAP.get(level, "info"),
            ))
        return out
