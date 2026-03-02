"""Skill Models"""

from datetime import datetime

from pydantic import BaseModel, Field

from .common import PlatformType, Pricing


class SkillBase(BaseModel):
    """Skill base model"""

    skill_name: str
    description: str | None = None
    platform: PlatformType
    developer: str | None = None
    capabilities: list[str] = []
    tags: list[str] = []
    pricing: Pricing = Pricing()


class SkillCreate(SkillBase):
    """Skill create request"""

    pass


class SkillUpdate(BaseModel):
    """Skill update request"""

    skill_name: str | None = None
    description: str | None = None
    capabilities: list[str] | None = None
    tags: list[str] | None = None
    pricing: Pricing | None = None


class Skill(SkillBase):
    """Skill response model"""

    skill_id: str = Field(default_factory=lambda: f"sk_{__import__('uuid').uuid4().hex[:12]}")
    rating: float = 0.0
    usage_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class SkillSearchResult(Skill):
    """Skill search result"""

    similarity: float | None = None
