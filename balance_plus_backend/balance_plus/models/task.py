# TODO: SQLAlchemy модель Task 
import uuid
from typing import Optional, List
from datetime import datetime

from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class Task(Base):
    __tablename__ = "tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)
    gitlab_issue_iid: Mapped[int] = mapped_column(nullable=False, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    branch_name: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default='open')
    
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # --- Отношения ---
    project: Mapped["Project"] = relationship(back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship(back_populates="assigned_tasks")
    calculation_jobs: Mapped[List["CalculationJob"]] = relationship(back_populates="task", cascade="all, delete-orphan") 