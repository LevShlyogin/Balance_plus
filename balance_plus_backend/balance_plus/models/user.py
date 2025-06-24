# TODO: SQLAlchemy модель User 
import uuid
from typing import Optional, List
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import func, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class UserRole(PyEnum):
    manager = "manager"
    engineer = "engineer"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    gitlab_user_id: Mapped[int] = mapped_column(unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)

    # Важно: эти поля должны быть зашифрованы в реальном приложении
    access_token: Mapped[Optional[str]]
    refresh_token: Mapped[Optional[str]]
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # --- Отношения ---
    # Связь с проектами, которые создал пользователь
    projects: Mapped[List["Project"]] = relationship(back_populates="created_by")
    # Связь с задачами, которые назначены пользователю
    assigned_tasks: Mapped[List["Task"]] = relationship(back_populates="assignee")
    # Связь с расчетами, которые запустил пользователь
    triggered_jobs: Mapped[List["CalculationJob"]] = relationship(back_populates="triggered_by") 