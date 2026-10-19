"""Nmap — port scan and, with NSE scripts enabled, protocol/service detail.
One class serves both the "IP and network reconnaissance" phase (plain scan)
and the "Protocol and service enumeration" phase (NSE scripts), selected by
the `nse` flag the registry passes in."""
import xml.etree.ElementTree as ET

from app.recon.base import FindingDraft, ToolRunner

RISKY_METHODS_PORTS = {23, 21, 3389}


class NmapRunner(ToolRunner):
    name = "Nmap"
    binary = "nmap"

    def __init__(self, nse: bool = False):
        self.nse = nse
        self.name = "Nmap NSE" if nse else "Nmap"

    def build_command(self, target: str) -> list[str]:
        cmd = [self.binary, "-sV", "-oX", "-", target]
        if self.nse:
            cmd[1:1] = ["-sC"]
        return cmd

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            root = ET.fromstring(stdout)
        except ET.ParseError:
            return out
        for port in root.iter("port"):
            state = port.find("state")
            if state is None or state.get("state") != "open":
                continue
            portid = int(port.get("portid", 0))
            svc = port.find("service")
            svc_name = svc.get("name", "unknown") if svc is not None else "unknown"
            product = (svc.get("product", "") if svc is not None else "") or ""
            sev = "medium" if portid in RISKY_METHODS_PORTS else "info"
            out.append(FindingDraft(
                title=f"Port {portid}/tcp open ({svc_name})",
                description=f"Port {portid} is open on {target} and is running {svc_name} {product}".strip() + ".",
                severity=sev,
                recommendation="Close or firewall this port if it has no current owner." if sev != "info" else None,
            ))
            if self.nse:
                for script in port.iter("script"):
                    out.append(FindingDraft(
                        title=f"NSE {script.get('id')} on port {portid}",
                        description=(script.get("output") or "").strip()[:300] or f"{script.get('id')} ran on port {portid}.",
                    ))
        return out
