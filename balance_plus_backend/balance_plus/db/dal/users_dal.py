# TODO: DAL для пользователей 

from typing import Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from .. import models

async def get_user_by_gitlab_id(db: AsyncSession, gitlab_user_id: int) -> Optional[models.User]:
    """Находит пользователя в БД по его ID в GitLab."""
    ...

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[models.User]:
    """Находит пользователя в БД по его внутреннему UUID."""
    ...

async def create_user(db: AsyncSession, user_data: dict[str, Any]) -> models.User:
    """Создает нового пользователя после первой аутентификации через GitLab."""
    ...

async def update_user_tokens(db: AsyncSession, user_id: UUID, access_token: str, refresh_token: str) -> models.User:
    """Обновляет OAuth2 токены пользователя."""
    ... 