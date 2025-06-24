# TODO: Pydantic схема Project 
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

from .user import UserRead

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    gitlab_project_id: int
    gitlab_repo_path: str

class ProjectRead(ProjectBase):
    id: UUID
    gitlab_project_id: int
    gitlab_repo_path: str
    created_at: datetime
    created_by: UserRead
    model_config = ConfigDict(from_attributes=True) 