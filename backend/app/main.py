from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import phases, reports, scans, targets, ws
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Cyron",
    description="One API for active and passive reconnaissance, run against authorized targets only.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(targets.router)
app.include_router(phases.router)
app.include_router(scans.router)
app.include_router(reports.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
