import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import require_api_key
from app.database import SessionLocal
from app.models.finding import Finding
from app.models.scan import PhaseResult, ScanRun
from app.models.target import Target
from app.recon.registry import PHASES
from app.recon.runner import run_scan
from app.schemas.finding import FindingOut
from app.schemas.scan import ScanCreate, ScanOut

router = APIRouter(prefix="/api/scans", tags=["scans"], dependencies=[Depends(require_api_key)])


async def _background_run(
    scan_id: uuid.UUID,
    target_value: str,
    phase_ids: list[str] | None,
    tool_selection: dict[str, list[str]] | None,
) -> None:
    # Own session: the request's session is closed by the time this runs.
    async with SessionLocal() as session:
        await run_scan(session, scan_id, target_value, phase_ids=phase_ids, tool_selection=tool_selection)


@router.post("", response_model=ScanOut)
async def create_scan(payload: ScanCreate, background: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    if not payload.authorized:
        raise HTTPException(422, "A scan cannot be created without confirming authorization for the target.")

    valid_ids = {p.id for p in PHASES}
    if payload.phase_ids and not set(payload.phase_ids) <= valid_ids:
        raise HTTPException(422, "phase_ids contains an unknown phase id.")
    if payload.tools:
        if not set(payload.tools.keys()) <= valid_ids:
            raise HTTPException(422, "tools contains an unknown phase id.")
        valid_tools_by_phase = {p.id: {label for label, _ in p.tools} for p in PHASES}
        for phase_id, labels in payload.tools.items():
            if not set(labels) <= valid_tools_by_phase[phase_id]:
                raise HTTPException(422, f"tools['{phase_id}'] contains a tool that isn't part of that phase.")

    target = (await db.execute(select(Target).where(Target.value == payload.target))).scalar_one_or_none()
    if target is None:
        target = Target(id=uuid.uuid4(), value=payload.target, type=payload.target_type)
        db.add(target)
        await db.flush()

    scan = ScanRun(
        id=uuid.uuid4(),
        target_id=target.id,
        modes=payload.modes,
        authorized=True,
        requested_by=payload.requested_by,
        status="pending",
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    background.add_task(_background_run, scan.id, target.value, payload.phase_ids, payload.tools)
    return ScanOut.model_validate(scan, from_attributes=True)


@router.get("/{scan_id}", response_model=ScanOut)
async def get_scan(scan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    scan = await db.get(ScanRun, scan_id)
    if scan is None:
        raise HTTPException(404, "Scan not found.")
    phase_results = (await db.execute(
        select(PhaseResult).where(PhaseResult.scan_run_id == scan_id)
    )).scalars().all()
    out = ScanOut.model_validate(scan, from_attributes=True)
    out.phase_results = phase_results
    return out


@router.get("", response_model=list[ScanOut])
async def list_scans(db: AsyncSession = Depends(get_db)):
    scans = (await db.execute(select(ScanRun).order_by(ScanRun.created_at.desc()))).scalars().all()
    return [ScanOut.model_validate(s, from_attributes=True) for s in scans]


@router.get("/{scan_id}/findings", response_model=list[FindingOut])
async def get_findings(scan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    phase_ids = (await db.execute(
        select(PhaseResult.id).where(PhaseResult.scan_run_id == scan_id)
    )).scalars().all()
    if not phase_ids:
        return []
    findings = (await db.execute(
        select(Finding).where(Finding.phase_result_id.in_(phase_ids)).order_by(Finding.created_at)
    )).scalars().all()
    return findings
