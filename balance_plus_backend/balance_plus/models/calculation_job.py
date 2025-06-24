# TODO: SQLAlchemy модель CalculationJob 

import uuid
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import func, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class JobStatus(PyEnum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"

class CalculationJob(Base):
    __tablename__ = "calculation_jobs"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    celery_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(unique=True, index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), nullable=False, default=JobStatus.pending)
    git_commit_sha: Mapped[str] = mapped_column(nullable=False)
    
    triggered_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    started_at: Mapped[Optional[datetime]]
    completed_at: Mapped[Optional[datetime]]
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # --- Отношения ---
    task: Mapped["Task"] = relationship(back_populates="calculation_jobs")
    triggered_by: Mapped["User"] = relationship(back_populates="triggered_jobs") 