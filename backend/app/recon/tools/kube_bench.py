"""kube-bench — checks a Kubernetes cluster against the CIS Kubernetes
Benchmark and reports which controls pass or fail."""
import json

from app.recon.base import FindingDraft, ToolRunner


class KubeBenchRunner(ToolRunner):
    name = "kube-bench"
    binary = "kube-bench"

    def build_command(self, target: str) -> list[str]:
        return [self.binary, "--json"]  # runs against the cluster the host is part of

    def parse(self, stdout, stderr, returncode, target) -> list[FindingDraft]:
        out = []
        try:
            data = json.loads(stdout or "{}")
        except json.JSONDecodeError:
            return out
        for section in data.get("Controls", []):
            for test in section.get("tests", []):
                for result in test.get("results", []):
                    if result.get("status") == "FAIL":
                        out.append(FindingDraft(
                            title=f"CIS {result.get('test_number')}: {result.get('test_desc', '')[:80]}",
                            description=f"kube-bench reports a failed check: {result.get('test_desc', '')}.",
                            severity="medium",
                            recommendation=result.get("remediation"),
                        ))
        return out
