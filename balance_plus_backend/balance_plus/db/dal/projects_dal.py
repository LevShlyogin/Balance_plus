# TODO: DAL для проектов 

from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .. import models

async def create_project(db: AsyncSession, name: str, gitlab_project_id: int, gitlab_repo_path: str, created_by_user_id: UUID) -> models.Project:
    """Сохраняет метаданные нового проекта в БД."""
    new_project = models.Project(
        name=name,
        gitlab_project_id=gitlab_project_id,
        gitlab_repo_path=gitlab_repo_path,
        created_by_user_id=created_by_user_id,
    )
    db.add(new_project)
    await db.flush()
    await db.refresh(new_project)
    return new_project

async def get_project_by_id(db: AsyncSession, project_id: UUID) -> Optional[models.Project]:
    """Находит проект по его внутреннему UUID."""
    return await db.get(models.Project, project_id)

async def get_project_by_gitlab_id(db: AsyncSession, gitlab_project_id: int) -> Optional[models.Project]:
    """Находит проект по его ID в GitLab, используя индекс."""
    query = select(models.Project).where(models.Project.gitlab_project_id == gitlab_project_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def list_all_projects(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[models.Project]:
    """Возвращает список всех проектов с пагинацией.
    Сортировка по дате создания, чтобы новые были вверху."""
    query = (
        select(models.Project)
        .order_by(models.Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all() 