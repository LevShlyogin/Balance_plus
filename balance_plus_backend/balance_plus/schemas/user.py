# TODO: Pydantic схема User 
from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID
from typing import Optional

from ..models.user import UserRole

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    gitlab_user_id: int
    access_token: str
    refresh_token: str

class UserUpdateTokens(BaseModel):
    access_token: str
    refresh_token: str

class UserRead(UserBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True) 