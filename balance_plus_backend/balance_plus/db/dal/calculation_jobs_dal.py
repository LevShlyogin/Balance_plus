# TODO: DAL для расчетных заданий 

from typing import Optional, Sequence, Any
from uuid import UUID
import datetime

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .. import models


async def create_calculation_job(db: AsyncSession, task_id: UUID, celery_task_id: UUID, git_commit_sha: str, triggered_by_user_id: UUID) -> models.CalculationJob:
    """
    Создает запись о новом расчетном задании.
    """
    new_job = models.CalculationJob(
        task_id=task_id,
        celery_task_id=celery_task_id,
        git_commit_sha=git_commit_sha,
        triggered_by_user_id=triggered_by_user_id,
        status='pending'
    )
    db.add(new_job)
    await db.flush()
    await db.refresh(new_job)
    return new_job


async def update_job_status(db: AsyncSession, celery_task_id: UUID, status: str, metadata: Optional[dict[str, Any]] = None) -> Optional[models.CalculationJob]:
    """
    Обновляет статус расчетного задания (вызывается из Celery worker).
    Автоматически проставляет время начала и завершения.
    """
    values_to_update = {"status": status}
    
    if status == 'running':
        values_to_update['started_at'] = datetime.datetime.now(datetime.timezone.utc)
    elif status in ['success', 'failed']:
        values_to_update['completed_at'] = datetime.datetime.now(datetime.timezone.utc)

    if metadata is not None:
        values_to_update['metadata'] = metadata
        
    stmt = (
        update(models.CalculationJob)
        .where(models.CalculationJob.celery_task_id == celery_task_id)
        .values(**values_to_update)
        .returning(models.CalculationJob)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_job_by_celery_id(db: AsyncSession, celery_task_id: UUID) -> Optional[models.CalculationJob]:
    """
    Находит расчетное задание по его ID в Celery.
    """
    query = select(models.CalculationJob).where(models.CalculationJob.celery_task_id == celery_task_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_jobs_for_task(db: AsyncSession, task_id: UUID, limit: int = 10) -> Sequence[models.CalculationJob]:
    """
    Возвращает историю запусков расчетов для конкретной задачи.
    Показывает самые свежие запуски первыми.
    """
    query = (
        select(models.CalculationJob)
        .where(models.CalculationJob.task_id == task_id)
        .order_by(models.CalculationJob.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all() 