from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from balance_plus.core.config import settings
from balance_plus.db.dal import users_dal
from balance_plus.models.user import User

async def get_gitlab_tokens(code: str) -> dict:
    """Обменивает авторизационный код на access_token."""
    token_url = f"{settings.GITLAB_URL}/oauth/token"
    data = {
        "client_id": settings.GITLAB_APP_ID,
        "client_secret": settings.GITLAB_APP_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GITLAB_REDIRECT_URI,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        response.raise_for_status()
        return response.json()

async def get_or_create_user(db: AsyncSession, gitlab_user_info, tokens: dict) -> User:
    """Находит пользователя в БД или создает нового."""
    user = await users_dal.get_user_by_gitlab_id(db, gitlab_user_id=gitlab_user_info.id)
    
    user_data = {
        "gitlab_user_id": gitlab_user_info.id,
        "username": gitlab_user_info.username,
        "email": gitlab_user_info.email,
        "role": "engineer",
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }

    if user:
        await users_dal.update_user_tokens(db, user.id, user_data["access_token"], user_data["refresh_token"])
        await db.commit()
        await db.refresh(user)
    else:
        user = await users_dal.create_user(db, user_data)
        await db.commit()

    return user 