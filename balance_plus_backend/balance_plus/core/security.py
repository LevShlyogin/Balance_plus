from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from balance_plus.db.session import get_db
from balance_plus.models.user import User
from balance_plus.services.gitlab_service import GitLabService
from balance_plus.core.config import settings
from balance_plus.db.dal import users_dal

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    Простая зависимость для получения текущего пользователя.
    Ожидает заголовок 'Authorization: Bearer <gitlab_access_token>'.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    
    gitlab_service = GitLabService(settings.GITLAB_URL, token)
    try:
        gitlab_user = gitlab_service.get_current_user()
        user = await users_dal.get_user_by_gitlab_id(db, gitlab_user.id)
        if not user:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found in our DB")
        return user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") 