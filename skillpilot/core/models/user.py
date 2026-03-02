"""User Models"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from .common import UserRole


class UserBase(BaseModel):
    """User base model"""

    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None


class UserCreate(UserBase):
    """User create request"""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update request"""

    name: str | None = None
    avatar_url: str | None = None


class User(UserBase):
    """User response model"""

    user_id: str = Field(default_factory=lambda: f"usr_{__import__('uuid').uuid4().hex[:12]}")
    role: UserRole = UserRole.FREE
    email_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}
