"""TruffleHog — scans a repository's full commit history (not just the
working tree) for high-confidence secrets, verifying many of them live
against the issuing service."""
import json

from app.recon.base import FindingDraft, ToolRunner


class TruffleHogRunner(ToolRunner):
    name = "TruffleHog"
    binary = "trufflehog"

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def build_command(self, target: str) -> list[str]:
        return [self.binary, "git", f"file://{self.repo_path}", "--json", "--only-verified"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for line in stdout.splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            out.append(FindingDraft(
                title=f"Verified secret: {row.get('DetectorName', 'unknown detector')}",
                description=f"TruffleHog found and verified a live secret ({row.get('DetectorName')}) in "
                             f"{row.get('SourceMetadata', {}).get('Data', {}).get('Git', {}).get('file', 'the repository')}.",
                severity="high",
                recommendation="Revoke and rotate this credential immediately; it was confirmed to still work.",
            ))
        return out
