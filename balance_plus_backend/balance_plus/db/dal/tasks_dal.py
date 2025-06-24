# TODO: DAL для задач 
from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from .. import models

async def create_task(db: AsyncSession, project_id: UUID, gitlab_issue_iid: int, title: str, branch_name: str, assignee_id: Optional[UUID]) -> models.Task:
    """Сохраняет метаданные новой задачи в БД."""
    new_task = models.Task(
        project_id=project_id,
        gitlab_issue_iid=gitlab_issue_iid,
        title=title,
        branch_name=branch_name,
        assignee_id=assignee_id,
    )
    db.add(new_task)
    await db.flush()
    await db.refresh(new_task)
    return new_task

async def get_task_by_gitlab_iid(db: AsyncSession, project_id: UUID, gitlab_issue_iid: int) -> Optional[models.Task]:
    """Находит задачу по ее IID в рамках проекта, используя композитный индекс."""
    query = select(models.Task).where(
        and_(
            models.Task.project_id == project_id,
            models.Task.gitlab_issue_iid == gitlab_issue_iid
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def list_tasks_for_assignee(db: AsyncSession, assignee_id: UUID, status: Optional[str] = 'open') -> Sequence[models.Task]:
    """Возвращает список задач, назначенных конкретному инженеру. Оптимизировано с помощью 'selectinload' для предзагрузки данных о проекте, чтобы избежать N+1 запросов."""
    query = (
        select(models.Task)
        .where(models.Task.assignee_id == assignee_id)
        .options(selectinload(models.Task.project))
        .order_by(models.Task.created_at.desc())
    )
    if status:
        query = query.where(models.Task.status == status)

    result = await db.execute(query)
    return result.scalars().all()

async def update_task_status(db: AsyncSession, task_id: UUID, new_status: str) -> Optional[models.Task]:
    """Обновляет статус задачи (например, после webhook'а из GitLab)."""
    stmt = (
        update(models.Task)
        .where(models.Task.id == task_id)
        .values(status=new_status)
        .returning(models.Task)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() 