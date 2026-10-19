import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Mode = Literal["active", "passive"]
Status = Literal["pending", "running", "completed", "failed", "cancelled"]


class ScanCreate(BaseModel):
    target: str
    target_type: Literal["domain", "ip", "cidr"] = "domain"
    modes: list[Mode] = Field(min_length=1)
    authorized: bool
    phase_ids: list[str] | None = None  # omit to run every phase for the chosen modes
    tools: dict[str, list[str]] | None = None  # phase_id -> selected tool labels; omit a phase to run all its tools
    requested_by: str | None = None


class PhaseResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    phase_id: str
    phase_name: str
    mode: Mode
    tools_used: list[str]
    status: Status
    started_at: datetime | None
    finished_at: datetime | None


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    target_id: uuid.UUID
    modes: list[Mode]
    status: Status
    exposure_score: int | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    phase_results: list[PhaseResultOut] = []
