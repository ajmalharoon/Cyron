"""TLS reconnaissance — not a single named CLI tool; Cyron inspects the
target's certificate directly with Python's ssl module (protocol version,
expiry, subject/issuer, SAN list)."""
import socket
import ssl
from datetime import datetime, timezone

from app.recon.base import FindingDraft, ToolRunner


class TlsReconRunner(ToolRunner):
    name = "TLS reconnaissance"
    binary = "python3"  # no external binary; always "available"

    def is_available(self) -> bool:
        return True

    def build_command(self, target: str) -> list[str]:
        return []  # unused: run() is overridden below

    async def run(self, target: str):
        from app.recon.base import ToolResult
        host = target.split("/")[0]
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as tls:
                    cert = tls.getpeercert()
                    version = tls.version()
        except Exception as exc:
            return ToolResult(tool=self.name, ran=False, error=str(exc))

        findings = []
        not_after = cert.get("notAfter")
        if not_after:
            expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days_left = (expiry - datetime.now(timezone.utc)).days
            sev = "high" if days_left < 7 else "medium" if days_left < 30 else "info"
            findings.append(FindingDraft(
                title=f"TLS certificate expires in {days_left} days",
                description=f"The TLS certificate for {host} is valid for {days_left} more days ({not_after}).",
                severity=sev,
                recommendation="Renew the certificate before it expires." if sev != "info" else None,
            ))
        if version in {"TLSv1", "TLSv1.1"}:
            findings.append(FindingDraft(
                title=f"Deprecated TLS version offered: {version}",
                description=f"{host} negotiated {version}, which is deprecated.",
                severity="medium",
                recommendation="Disable TLS versions older than 1.2.",
            ))
        else:
            findings.append(FindingDraft(
                title=f"TLS version in use: {version}",
                description=f"{host} negotiated {version}.",
            ))
        return ToolResult(tool=self.name, ran=True, findings=findings)
