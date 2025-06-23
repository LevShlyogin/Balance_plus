# TODO: DAL для проектов 

from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from .. import models

async def create_project(db: AsyncSession, name: str, gitlab_project_id: int, gitlab_repo_path: str, created_by_user_id: UUID) -> models.Project:
    """Сохраняет метаданные нового проекта в БД."""
    ...

async def get_project_by_id(db: AsyncSession, project_id: UUID) -> Optional[models.Project]:
    """Находит проект по его внутреннему UUID."""
    ...

async def get_project_by_gitlab_id(db: AsyncSession, gitlab_project_id: int) -> Optional[models.Project]:
    """Находит проект по его ID в GitLab."""
    ...

async def list_all_projects(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[models.Project]:
    """Возвращает список всех проектов с пагинацией."""
    ... 