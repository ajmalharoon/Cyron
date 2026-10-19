"""Prowler — AWS security-best-practice auditor. Run against whatever AWS
credentials/profile the backend container has (never a secret Cyron stores
itself)."""
import json

from app.recon.base import FindingDraft, ToolRunner

SEV_MAP = {"CRITICAL": "high", "HIGH": "high", "MEDIUM": "medium", "LOW": "low", "INFORMATIONAL": "info"}


class ProwlerRunner(ToolRunner):
    name = "Prowler"
    binary = "prowler"

    def build_command(self, target: str) -> list[str]:
        # `target` here is an AWS profile name, not a hostname.
        return [self.binary, "aws", "--profile", target, "-M", "json"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            rows = json.loads(stdout or "[]")
        except json.JSONDecodeError:
            return out
        for row in rows:
            if row.get("Status") != "PASS":
                out.append(FindingDraft(
                    title=row.get("CheckTitle", "Prowler check failed"),
                    description=row.get("StatusExtended", "")[:300] or "A Prowler AWS check did not pass.",
                    severity=SEV_MAP.get(str(row.get("Severity", "")).upper(), "info"),
                    recommendation=row.get("Remediation", {}).get("Recommendation", {}).get("Text"),
                ))
        return out
