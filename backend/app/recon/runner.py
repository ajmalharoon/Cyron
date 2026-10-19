"""The scan orchestrator. Given a ScanRun that's already been inserted
(status="pending"), runs every enabled phase in registry order, persists a
PhaseResult and its Findings as each phase completes, and publishes progress
over the WebSocket event bus so the frontend's run log updates live."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import bus
from app.models.finding import Finding
from app.models.scan import PhaseResult, ScanRun
from app.recon.registry import PHASES
from app.utils.logger import get_logger

log = get_logger(__name__)

SEVERITY_WEIGHT = {"high": 14, "medium": 6, "low": 2, "info": 0}


async def run_scan(
    session: AsyncSession,
    scan_id: uuid.UUID,
    target_value: str,
    phase_ids: list[str] | None = None,
    tool_selection: dict[str, list[str]] | None = None,
) -> None:
    """`phase_ids`, if given, restricts the run to that subset of phases (on
    top of the scan's modes). `tool_selection` maps phase_id -> the tool
    labels to run within that phase; a phase absent from the mapping (or
    `tool_selection=None`) runs every tool it has — this keeps the API
    backward compatible with a scan that doesn't pick individual tools."""
    scan = await session.get(ScanRun, scan_id)
    if scan is None:
        log.error("runner.missing_scan", extra={"scan_id": str(scan_id)})
        return

    scan.status = "running"
    scan.started_at = datetime.now(timezone.utc)
    await session.commit()
    await bus.publish(str(scan_id), {"event": "scan.started", "target": target_value})

    phases = [p for p in PHASES if p.mode in scan.modes]
    if phase_ids:
        allowed = set(phase_ids)
        phases = [p for p in phases if p.id in allowed]
    finding_counter = 0
    score = 0

    for phase in phases:
        phase_result = PhaseResult(
            scan_run_id=scan.id,
            phase_id=phase.id,
            phase_name=phase.name,
            mode=phase.mode,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(phase_result)
        await session.commit()
        await bus.publish(str(scan_id), {"event": "phase.started", "phase_id": phase.id, "phase_name": phase.name})

        selected_labels = tool_selection.get(phase.id) if tool_selection else None
        tools_to_run = phase.tools if selected_labels is None else [
            (label, factory) for label, factory in phase.tools if label in selected_labels
        ]
        if selected_labels is not None:
            skipped = {label for label, _ in phase.tools} - set(selected_labels)
            for label in skipped:
                await bus.publish(str(scan_id), {
                    "event": "tool.skipped", "phase_id": phase.id, "tool": label, "reason": "deselected",
                })

        tools_used = []
        for label, factory in tools_to_run:
            runner = factory()
            result = await runner.run(target_value)
            if not result.ran:
                await bus.publish(str(scan_id), {
                    "event": "tool.skipped", "phase_id": phase.id, "tool": label, "reason": result.error,
                })
                continue
            tools_used.append(label)
            for draft in result.findings:
                finding_counter += 1
                score += SEVERITY_WEIGHT.get(draft.severity, 0)
                session.add(Finding(
                    phase_result_id=phase_result.id,
                    ref=f"CYR-{finding_counter:03d}",
                    tool=label,
                    title=draft.title,
                    description=draft.description,
                    severity=draft.severity,
                    recommendation=draft.recommendation or phase.recommendation,
                    raw_output=draft.raw,
                ))
            await bus.publish(str(scan_id), {
                "event": "tool.finished", "phase_id": phase.id, "tool": label, "findings": len(result.findings),
            })

        phase_result.tools_used = tools_used
        phase_result.status = "completed"
        phase_result.finished_at = datetime.now(timezone.utc)
        await session.commit()
        await bus.publish(str(scan_id), {"event": "phase.finished", "phase_id": phase.id, "tools_used": tools_used})

    scan.status = "completed"
    scan.finished_at = datetime.now(timezone.utc)
    scan.exposure_score = min(100, score)
    await session.commit()
    await bus.publish(str(scan_id), {"event": "scan.completed", "exposure_score": scan.exposure_score})
