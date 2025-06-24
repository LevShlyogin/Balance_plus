# TODO: DAL для пользователей 

from typing import Optional, Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models

async def get_user_by_gitlab_id(db: AsyncSession, gitlab_user_id: int) -> Optional[models.User]:
    """
    Находит пользователя в БД по его ID в GitLab.
    Использует индекс по gitlab_user_id для быстрого поиска.
    """
    query = select(models.User).where(models.User.gitlab_user_id == gitlab_user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[models.User]:
    """
    Находит пользователя в БД по его внутреннему UUID.
    Использует db.get для максимальной производительности при поиске по первичному ключу.
    """
    return await db.get(models.User, user_id)

async def create_user(db: AsyncSession, user_data: dict[str, Any]) -> models.User:
    """
    Создает нового пользователя после первой аутентификации через GitLab.
    Не делает commit, только flush, чтобы получить ID из БД.
    """
    new_user = models.User(**user_data)
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)  # Обновляем объект данными из БД (например, default значения)
    return new_user

async def update_user_tokens(db: AsyncSession, user_id: UUID, access_token: str, refresh_token: str) -> Optional[models.User]:
    """
    Обновляет OAuth2 токены пользователя.
    Использует 'UPDATE ... RETURNING' для эффективности, чтобы обновить и вернуть данные за один запрос.
    """
    stmt = (
        update(models.User)
        .where(models.User.id == user_id)
        .values(access_token=access_token, refresh_token=refresh_token)
        .returning(models.User)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()