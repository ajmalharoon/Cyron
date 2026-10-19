import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Severity = Literal["info", "low", "medium", "high"]


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    ref: str
    tool: str
    title: str
    description: str
    severity: Severity
    recommendation: str | None
    created_at: datetime
