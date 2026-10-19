"""LinkFinder — extracts endpoint paths and URLs from JavaScript source."""
import re

from app.recon.base import FindingDraft, ToolRunner


class LinkFinderRunner(ToolRunner):
    name = "LinkFinder"
    binary = "linkfinder"

    def build_command(self, target: str) -> list[str]:
        base = target if target.startswith("http") else f"https://{target}"
        return [self.binary, "-i", base, "-o", "cli"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for line in stdout.splitlines():
            line = line.strip()
            if re.match(r"^[\"']?/[\w\-./?=&%]+", line):
                out.append(FindingDraft(
                    title=f"Endpoint found in JavaScript: {line}",
                    description=f"LinkFinder extracted the path {line} from a JavaScript file on {target}.",
                ))
        return out
