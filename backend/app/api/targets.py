import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import require_api_key
from app.models.target import Target
from app.schemas.target import TargetCreate, TargetOut

router = APIRouter(prefix="/api/targets", tags=["targets"], dependencies=[Depends(require_api_key)])


@router.post("", response_model=TargetOut)
async def create_or_get_target(payload: TargetCreate, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(Target).where(Target.value == payload.value))).scalar_one_or_none()
    if existing:
        return existing
    target = Target(id=uuid.uuid4(), value=payload.value, type=payload.type)
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


@router.get("", response_model=list[TargetOut])
async def list_targets(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Target).order_by(Target.created_at.desc()))).scalars().all()
