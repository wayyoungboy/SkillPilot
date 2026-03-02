"""Common Models and Enums"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class UserRole(StrEnum):
    """User roles"""

    FREE = "free"
    PERSONAL = "personal"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class PlatformType(StrEnum):
    """Platform types"""

    COZE = "coze"
    DIFY = "dify"
    LANGCHAIN = "langchain"
    CURSOR = "cursor"
    GITHUB = "github"
    CUSTOM = "custom"


class SubscriptionStatus(StrEnum):
    """Subscription status"""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


class ExecutionStatus(StrEnum):
    """Execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Pricing(BaseModel):
    """Pricing model"""

    type: str = "free"  # free, subscription, per_use
    price: float | None = None
    currency: str = "USD"


class Pagination(BaseModel):
    """Pagination info"""

    page: int = 1
    limit: int = 20
    total: int = 0
    total_pages: int = 0


class ErrorDetail(BaseModel):
    """Error detail"""

    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Error response"""

    error: ErrorDetail


class ListResponse(BaseModel):
    """List response"""

    data: list[Any]
    pagination: Pagination
