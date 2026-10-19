import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    scan_run_id: uuid.UUID
    format: Literal["markdown", "json"]
    content: str
    generated_at: datetime
