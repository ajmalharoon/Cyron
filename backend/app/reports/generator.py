"""Builds the Markdown reconnaissance report for a completed scan. Follows
the information-gathering stages of PTES, the planning/discovery guidance in
NIST SP 800-115, and the information-gathering section of the OWASP Web
Security Testing Guide. Severity and the exposure score are Cyron's
automated judgement, not CVSS — the report says so in its own limitations
section."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finding import Finding
from app.models.scan import PhaseResult, ScanRun
from app.models.target import Target

SEVERITY_LABEL = {"high": "High", "medium": "Medium", "low": "Low", "info": "Informational"}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}
SLA = {"high": "within 7 days", "medium": "within 30 days", "low": "within 90 days"}
IMPACT = {
    "high": "An attacker could exploit this issue directly and gain access to sensitive data or systems.",
    "medium": "This issue weakens the security posture and could help an attacker chain further attacks.",
    "low": "This issue has limited direct impact, but it widens the attack surface or departs from good practice.",
    "info": "This observation is recorded for completeness and does not indicate a weakness on its own.",
}


async def generate_report(session: AsyncSession, scan_id) -> str:
    scan: ScanRun = await session.get(ScanRun, scan_id)
    target: Target = await session.get(Target, scan.target_id)

    phase_rows = (await session.execute(
        select(PhaseResult).where(PhaseResult.scan_run_id == scan.id)
    )).scalars().all()

    findings: list[tuple[PhaseResult, Finding]] = []
    for pr in phase_rows:
        rows = (await session.execute(
            select(Finding).where(Finding.phase_result_id == pr.id)
        )).scalars().all()
        findings.extend((pr, f) for f in rows)
    findings.sort(key=lambda pf: SEVERITY_ORDER.get(pf[1].severity, 3))

    def count(sev: str) -> int:
        return sum(1 for _, f in findings if f.severity == sev)

    high, med, low, info = count("high"), count("medium"), count("low"), count("info")
    score = min(100, high * 14 + med * 6 + low * 2)
    level = "high" if score >= 60 else "moderate" if score >= 30 else "low"
    modes = " and ".join(m.capitalize() for m in scan.modes)
    tools_used = sorted({pr.phase_id and t for pr in phase_rows for t in pr.tools_used})
    top_phases = sorted({pr.phase_name for pr, f in findings if f.severity == "high"})
    report_id = f"CYR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(scan.id)[:8]}"

    lines: list[str] = []
    w = lines.append

    w(f"# Reconnaissance Assessment Report\n")
    w("| Document control | |")
    w("|---|---|")
    w(f"| Target | {target.value} |")
    w(f"| Report ID | {report_id} |")
    w(f"| Date | {datetime.now(timezone.utc).strftime('%Y-%m-%d')} |")
    w("| Version | 1.0 |")
    w("| Classification | Confidential |")
    w(f"| Assessment type | {modes} reconnaissance |")
    w("| Prepared by | Cyron reconnaissance platform |\n")

    w("## 1. Executive summary\n")
    w(f"This report presents the results of a {modes.lower()} reconnaissance assessment of {target.value}. "
      f"The assessment was run with the Cyron platform and covered {len(phase_rows)} reconnaissance phases "
      f"using {len(tools_used)} tools. Its purpose is to describe what an outsider could learn about the "
      f"target and to point out weaknesses that deserve attention.\n")
    w(f"The assessment recorded {len(findings)} observations: {high} high, {med} medium, {low} low and "
      f"{info} informational. The overall exposure is rated {level}, with a score of {score} out of 100." +
      (f" The most serious issues relate to {', '.join(top_phases)}." if top_phases else " No high-severity issues were found.") + "\n")
    w(f"The organization should fix the high-severity findings first and then work through the medium and "
      f"low findings using the remediation roadmap in section 7. Each finding states what was observed, why "
      f"it matters and how to fix it.\n")

    w("## 2. Scope and rules of engagement\n")
    w(f"The target of this assessment is {target.value}. The operator confirmed before the run that testing "
      f"of this target is authorized. Active modules send traffic to the target and its infrastructure. "
      f"Passive modules read only public sources, archives and the operator's own cloud accounts and "
      f"repositories, and send nothing to the target. No exploitation, credential guessing or "
      f"denial-of-service testing was performed, and no finding was validated by hand.\n")

    w("## 3. Methodology\n")
    w("The assessment follows the information-gathering and vulnerability-analysis stages of the "
      "Penetration Testing Execution Standard (PTES), the planning and discovery guidance of NIST SP "
      "800-115, and the information-gathering section of the OWASP Web Security Testing Guide. Each phase "
      "below was run with the tools listed, and the results were normalized into one set of findings.\n")
    w("| Phase | Mode | Tools | Observations |")
    w("|---|---|---|---|")
    for pr in phase_rows:
        n = sum(1 for p, _ in findings if p.id == pr.id)
        w(f"| {pr.phase_name} | {pr.mode.capitalize()} | {', '.join(pr.tools_used) or '—'} | {n} |")
    w("")

    w("## 4. Risk rating method\n")
    w("Each finding is rated by its likelihood of exploitation and its potential impact. The ratings are "
      "Cyron's automated judgement, not CVSS scores, and an analyst should confirm them before action is "
      "taken.\n")
    w("| Rating | Meaning | Target remediation |")
    w("|---|---|---|")
    w("| High | Exploitation is likely and could lead to serious compromise. | Within 7 days |")
    w("| Medium | The issue weakens security and could be combined with other issues. | Within 30 days |")
    w("| Low | The issue has limited impact but widens the attack surface. | Within 90 days |")
    w("| Informational | The observation is recorded for completeness. | No fix required |\n")

    w("## 5. Summary of findings\n")
    w("| ID | Rating | Observation | Phase |")
    w("|---|---|---|---|")
    for pr, f in findings:
        w(f"| {f.ref} | {SEVERITY_LABEL[f.severity]} | {f.title} | {pr.phase_name} |")
    w("")

    w("## 6. Detailed findings\n")
    actionable = [(pr, f) for pr, f in findings if f.severity != "info"]
    if not actionable:
        w("No findings rated low or above were recorded.\n")
    for pr, f in actionable:
        w(f"### {f.ref}: {pr.phase_name}\n")
        w(f"**Rating:** {SEVERITY_LABEL[f.severity]}  ")
        w(f"**Affected asset:** {target.value}  ")
        w(f"**Detected by:** {f.tool}  ")
        w(f"**Description:** {f.description}  ")
        w(f"**Impact:** {IMPACT[f.severity]}  ")
        w(f"**Recommendation:** {f.recommendation or 'Review this finding and remediate as appropriate.'}\n")

    w("## 7. Remediation roadmap\n")
    roadmap_any = False
    for sev in ("high", "medium", "low"):
        group = [f for _, f in findings if f.severity == sev]
        if not group:
            continue
        roadmap_any = True
        recs = sorted({f.recommendation for f in group if f.recommendation})
        w(f"1. **{SEVERITY_LABEL[sev]} priority:** Fix {', '.join(f.ref for f in group)} {SLA[sev]}. " +
          " ".join(recs))
    if not roadmap_any:
        w("No remediation is required for this run.\n")
    w("")

    w("## 8. Conclusion\n")
    w(f"Cyron recorded {len(findings)} observations about {target.value}, of which {high + med} need "
      f"prompt attention. A qualified analyst should validate these results before remediation begins, and "
      f"the target should be retested afterwards to confirm that each fix works.\n")

    w("## Appendix A. Tools used\n")
    w(f"The following tools produced the results in this report: {', '.join(tools_used) or 'none ran'}.\n")

    w("## Appendix B. Limitations\n")
    w("This report reflects the state of the target at the time of the run. Passive sources show only what "
      "is public at that moment, and active results depend on the tools selected and on how the target "
      "responds. Findings that are not listed were not necessarily absent.\n")

    return "\n".join(lines)
