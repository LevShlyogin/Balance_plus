# TODO: DAL для задач 
from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from .. import models

async def create_task(db: AsyncSession, project_id: UUID, gitlab_issue_iid: int, title: str, branch_name: str, assignee_id: Optional[UUID]) -> models.Task:
    """Сохраняет метаданные новой задачи в БД."""
    ...

async def get_task_by_gitlab_iid(db: AsyncSession, project_id: UUID, gitlab_issue_iid: int) -> Optional[models.Task]:
    """Находит задачу по ее IID в рамках проекта."""
    ...

async def list_tasks_for_assignee(db: AsyncSession, assignee_id: UUID, status: Optional[str] = 'open') -> Sequence[models.Task]:
    """Возвращает список задач, назначенных конкретному инженеру."""
    ...

async def update_task_status(db: AsyncSession, task_id: UUID, new_status: str) -> models.Task:
    """Обновляет статус задачи (например, после webhook'а из GitLab)."""
    ... 