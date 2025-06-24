from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from balance_plus.core.config import settings
from balance_plus.db.session import get_db
from balance_plus.services import auth_service
from balance_plus.services.gitlab_service import GitLabService

router = APIRouter()

@router.get("/login")
def login():
    """Перенаправляет пользователя на страницу аутентификации GitLab."""
    auth_url = (
        f"{settings.GITLAB_URL}/oauth/authorize?"
        f"client_id={settings.GITLAB_APP_ID}&"
        f"redirect_uri={settings.GITLAB_REDIRECT_URI}&"
        "response_type=code&scope=api"
    )
    return Response(status_code=302, headers={'Location': auth_url})

@router.get("/callback")
async def auth_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Обрабатывает callback от GitLab, получает токен и создает пользователя."""
    tokens = await auth_service.get_gitlab_tokens(code)
    gitlab_service = GitLabService(settings.GITLAB_URL, private_token=tokens["access_token"])
    gitlab_user_info = gitlab_service.get_current_user()

    user = await auth_service.get_or_create_user(db, gitlab_user_info, tokens)
    
    return {"message": "Authentication successful", "access_token": user.access_token} 