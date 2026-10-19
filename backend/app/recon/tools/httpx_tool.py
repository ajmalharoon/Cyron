"""ProjectDiscovery httpx — HTTP/HTTPS probing: status, title, tech, TLS."""
from app.recon.base import FindingDraft, ToolRunner, json_lines


class HttpxRunner(ToolRunner):
    name = "httpx"
    binary = "httpx"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, "-u", target, "-json", "-silent", "-title", "-status-code", "-tech-detect"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        for row in json_lines(stdout):
            url = row.get("url", target)
            code = row.get("status_code")
            title = row.get("title", "")
            out.append(FindingDraft(
                title=f"{url} responded with status {code}",
                description=f"{url} answered with HTTP status {code}" + (f' and page title "{title}".' if title else "."),
            ))
            for tech in row.get("tech", []) or []:
                out.append(FindingDraft(
                    title=f"Technology detected: {tech}",
                    description=f"httpx identified {tech} on {url}.",
                ))
        return out
