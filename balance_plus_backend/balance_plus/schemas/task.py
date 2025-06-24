# TODO: Pydantic схема Task 
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

from .user import UserRead
from .project import ProjectRead

class TaskBase(BaseModel):
    title: str
    status: str

class TaskCreate(TaskBase):
    gitlab_issue_iid: int
    branch_name: str
    assignee_id: Optional[UUID] = None

class TaskRead(TaskBase):
    id: UUID
    gitlab_issue_iid: int
    branch_name: str
    created_at: datetime
    project: ProjectRead
    assignee: Optional[UserRead] = None
    model_config = ConfigDict(from_attributes=True) 