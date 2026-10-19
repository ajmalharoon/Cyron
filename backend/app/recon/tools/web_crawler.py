"""Lightweight same-origin web crawler — not a single named tool. Follows
links a short distance from the target's homepage to build a page inventory
for the HTTP/HTTPS reconnaissance phase."""
from urllib.parse import urljoin, urlparse

import httpx

from app.recon.base import FindingDraft, ToolResult, ToolRunner


class WebCrawlerRunner(ToolRunner):
    name = "Web crawler"
    binary = "python3"
    max_pages = 20

    def is_available(self) -> bool:
        return True

    def build_command(self, target: str) -> list[str]:
        return []

    async def run(self, target: str) -> ToolResult:
        start = target if target.startswith("http") else f"https://{target}"
        origin = urlparse(start).netloc
        seen, queue, pages = set(), [start], []
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                while queue and len(pages) < self.max_pages:
                    url = queue.pop(0)
                    if url in seen:
                        continue
                    seen.add(url)
                    try:
                        resp = await client.get(url)
                    except httpx.HTTPError:
                        continue
                    pages.append((url, resp.status_code))
                    if "text/html" not in resp.headers.get("content-type", ""):
                        continue
                    for part in resp.text.split('href="')[1:]:
                        link = part.split('"')[0]
                        full = urljoin(url, link)
                        if urlparse(full).netloc == origin and full not in seen:
                            queue.append(full)
        except Exception as exc:
            return ToolResult(tool=self.name, ran=False, error=str(exc))

        findings = [
            FindingDraft(
                title=f"Page discovered: {url}",
                description=f"The crawler found {url}, which answered with status {code}.",
            )
            for url, code in pages
        ]
        return ToolResult(tool=self.name, ran=True, findings=findings)
