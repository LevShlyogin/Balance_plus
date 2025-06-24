# TODO: SQLAlchemy модель Project 
import uuid
from typing import Optional, List
from datetime import datetime

from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    gitlab_project_id: Mapped[int] = mapped_column(unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    gitlab_repo_path: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]]
    
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # --- Отношения ---
    # Связь "один ко многим" с создателем (пользователем)
    created_by: Mapped["User"] = relationship(back_populates="projects")
    # Связь "один ко многим" с задачами
    tasks: Mapped[List["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan") 