# TODO: DAL для расчетных заданий 

from typing import Optional, Sequence, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from .. import models

async def create_calculation_job(db: AsyncSession, task_id: UUID, celery_task_id: UUID, git_commit_sha: str, triggered_by_user_id: UUID) -> models.CalculationJob:
    """Создает запись о новом расчетном задании."""
    ...

async def update_job_status(db: AsyncSession, celery_task_id: UUID, status: str, metadata: Optional[dict[str, Any]] = None) -> Optional[models.CalculationJob]:
    """Обновляет статус расчетного задания (вызывается из Celery worker)."""
    ...

async def get_job_by_celery_id(db: AsyncSession, celery_task_id: UUID) -> Optional[models.CalculationJob]:
    """Находит расчетное задание по его ID в Celery."""
    ...

async def list_jobs_for_task(db: AsyncSession, task_id: UUID, limit: int = 10) -> Sequence[models.CalculationJob]:
    """Возвращает историю запусков расчетов для конкретной задачи."""
    ... 