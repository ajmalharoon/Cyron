"""Gitleaks — scans a git repository (or working tree) for committed
secrets. Reused by both the JavaScript-reconnaissance phase (scanning
downloaded JS as a plain directory) and the source-code/repository phase
(scanning a cloned repo), selected by the `repo_path` argument."""
import json

from app.recon.base import FindingDraft, ToolRunner


class GitleaksRunner(ToolRunner):
    name = "Gitleaks"
    binary = "gitleaks"

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def build_command(self, target: str) -> list[str]:
        return [self.binary, "detect", "--source", self.repo_path, "--report-format", "json", "--report-path", "-", "--exit-code", "0"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            rows = json.loads(stdout or "[]")
        except json.JSONDecodeError:
            return out
        for row in rows:
            out.append(FindingDraft(
                title=f"Secret pattern found: {row.get('RuleID', 'unknown rule')}",
                description=f"Gitleaks matched the rule {row.get('RuleID')} in {row.get('File')} "
                             f"at commit {row.get('Commit', 'n/a')[:8]}.",
                severity="high",
                recommendation="Rotate the exposed credential and remove it from the repository's history.",
            ))
        return out
