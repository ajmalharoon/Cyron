import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import require_api_key
from app.models.report import Report
from app.models.scan import ScanRun
from app.reports.generator import generate_report
from app.schemas.report import ReportOut

router = APIRouter(prefix="/api/scans", tags=["reports"], dependencies=[Depends(require_api_key)])


@router.get("/{scan_id}/report", response_model=ReportOut)
async def get_report(scan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    scan = await db.get(ScanRun, scan_id)
    if scan is None:
        raise HTTPException(404, "Scan not found.")
    if scan.status != "completed":
        raise HTTPException(409, "The scan has not finished yet.")

    content = await generate_report(db, scan_id)
    report = Report(scan_run_id=scan_id, format="markdown", content=content)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report
