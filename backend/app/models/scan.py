import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, Enum, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

SCAN_STATUS = Enum("pending", "running", "completed", "failed", "cancelled", name="scan_status")
SCAN_MODE = Enum("active", "passive", name="scan_mode")


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("targets.id", ondelete="CASCADE"))
    modes: Mapped[list[str]] = mapped_column(ARRAY(SCAN_MODE), nullable=False)
    status: Mapped[str] = mapped_column(SCAN_STATUS, default="pending")
    authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    requested_by: Mapped[str | None] = mapped_column(String, nullable=True)
    exposure_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    target = relationship("Target", back_populates="scan_runs")
    phase_results = relationship("PhaseResult", back_populates="scan_run", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="scan_run", cascade="all, delete-orphan")


class PhaseResult(Base):
    __tablename__ = "phase_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scan_runs.id", ondelete="CASCADE"))
    phase_id: Mapped[str] = mapped_column(String, nullable=False)
    phase_name: Mapped[str] = mapped_column(String, nullable=False)
    mode: Mapped[str] = mapped_column(SCAN_MODE, nullable=False)
    tools_used: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    status: Mapped[str] = mapped_column(SCAN_STATUS, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scan_run = relationship("ScanRun", back_populates="phase_results")
    findings = relationship("Finding", back_populates="phase_result", cascade="all, delete-orphan")
