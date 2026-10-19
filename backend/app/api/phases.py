from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.recon.registry import PHASES

router = APIRouter(prefix="/api/phases", tags=["phases"], dependencies=[Depends(require_api_key)])


@router.get("")
async def list_phases():
    return [
        {
            "id": p.id,
            "name": p.name,
            "mode": p.mode,
            "description": p.description,
            "recommendation": p.recommendation,
            "tools": [label for label, _ in p.tools],
        }
        for p in PHASES
    ]
