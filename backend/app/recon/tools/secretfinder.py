"""SecretFinder — looks for API keys, tokens and other secret-shaped strings
inside JavaScript source."""
from app.recon.base import FindingDraft, ToolRunner


class SecretFinderRunner(ToolRunner):
    name = "SecretFinder"
    binary = "secretfinder"

    def build_command(self, target: str) -> list[str]:
        base = target if target.startswith("http") else f"https://{target}"
        return [self.binary, "-i", base, "-o", "cli"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for line in stdout.splitlines():
            if "=>" in line and line.strip():
                out.append(FindingDraft(
                    title="Possible secret in JavaScript",
                    description=f"SecretFinder flagged a string that looks like a secret on {target}: {line.strip()[:200]}.",
                    severity="high",
                    recommendation="Rotate the exposed credential immediately and remove it from client-side code.",
                ))
        return out
