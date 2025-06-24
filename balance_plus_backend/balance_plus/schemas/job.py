# TODO: Pydantic схема Job 
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

from ..models.calculation_job import JobStatus
from .user import UserRead

class JobBase(BaseModel):
    status: JobStatus
    git_commit_sha: str
    metadata: Optional[Dict[str, Any]] = None

class JobCreate(BaseModel):
    celery_task_id: UUID
    git_commit_sha: str

class JobRead(JobBase):
    id: UUID
    celery_task_id: Optional[UUID]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    triggered_by: UserRead
    model_config = ConfigDict(from_attributes=True)

class JobUpdate(BaseModel):
    status: JobStatus
    metadata: Optional[Dict[str, Any]] = None 