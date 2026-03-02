"""Authentication Models"""

from pydantic import BaseModel, EmailStr, Field

from .common import UserRole


class Token(BaseModel):
    """Token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """Token payload"""

    sub: str  # user_id
    email: str
    role: UserRole
    permissions: list[str] = []


class LoginRequest(BaseModel):
    """Login request"""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Register request"""

    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = None
