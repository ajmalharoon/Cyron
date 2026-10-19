import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TargetCreate(BaseModel):
    value: str
    type: Literal["domain", "ip", "cidr"]


class TargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    value: str
    type: str
    created_at: datetime
