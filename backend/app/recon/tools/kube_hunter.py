"""kube-hunter — probes a Kubernetes cluster's exposed surface (API server,
kubelet, dashboard) for exploitable misconfiguration."""
import json

from app.recon.base import FindingDraft, ToolRunner


class KubeHunterRunner(ToolRunner):
    name = "kube-hunter"
    binary = "kube-hunter"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, "--remote", target, "--report", "json"]

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            data = json.loads(stdout or "{}")
        except json.JSONDecodeError:
            return out
        for v in data.get("vulnerabilities", []):
            sev = "high" if v.get("severity") == "high" else "medium" if v.get("severity") == "medium" else "low"
            out.append(FindingDraft(
                title=v.get("vulnerability", "Kubernetes exposure"),
                description=v.get("description", "")[:300] or f"kube-hunter flagged an issue on {target}.",
                severity=sev,
                recommendation=v.get("avd_reference"),
            ))
        return out
