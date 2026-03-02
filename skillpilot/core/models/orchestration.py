"""Orchestration Models"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import PlatformType


class SkillChainStep(BaseModel):
    """Skill chain step"""

    step: int
    skill_id: str
    skill_name: str
    platform: PlatformType
    input: dict[str, Any] = {}
    output_format: str = "JSON"
    depends_on: list[int] = []


class OrchestrationCreate(BaseModel):
    """Orchestration create request"""

    task_description: str
    options: dict[str, Any] = Field(default_factory=dict)


class Orchestration(BaseModel):
    """Orchestration response model"""

    plan_id: str = Field(default_factory=lambda: f"op_{__import__('uuid').uuid4().hex[:12]}")
    task_description: str
    skill_chain: list[SkillChainStep] = []
    status: str = (
        "pending_confirmation"  # pending_confirmation, pending, running, completed, failed
    )
    estimated_duration: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: datetime | None = None

    model_config = {"from_attributes": True}
