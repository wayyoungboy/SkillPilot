"""Base Platform Adapter"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class SkillExecutionRequest(BaseModel):
    """Request model for skill execution"""

    skill_id: str
    skill_name: str
    input_data: dict[str, Any]
    platform_config: dict[str, Any] | None = None


class SkillExecutionResponse(BaseModel):
    """Response model for skill execution"""

    success: bool
    output: Any | None = None
    error: str | None = None
    execution_time_ms: int | None = None
    metadata: dict[str, Any] = {}


class PlatformAdapter(ABC):
    """
    Abstract base class for platform adapters.
    
    Platform adapters handle the execution of skills on specific platforms
    like Coze, Dify, LangChain, etc.
    """

    platform_name: str = "base"

    def __init__(self):
        self._client = None
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the platform client"""
        pass

    @abstractmethod
    async def execute_skill(self, request: SkillExecutionRequest) -> SkillExecutionResponse:
        """
        Execute a skill on the platform.
        
        Args:
            request: Execution request with skill details and input
            
        Returns:
            Execution response with output or error
        """
        pass

    @abstractmethod
    async def validate_skill(self, skill_id: str) -> bool:
        """
        Validate that a skill exists and is executable on the platform.
        
        Args:
            skill_id: Skill identifier
            
        Returns:
            True if skill is valid
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the platform connection is healthy.
        
        Returns:
            True if platform is accessible
        """
        try:
            await self.initialize()
            return self._client is not None
        except Exception:
            return False

    async def get_skill_status(self, skill_id: str) -> dict[str, Any]:
        """
        Get the status of a skill execution.
        
        Args:
            skill_id: Skill identifier
            
        Returns:
            Status information
        """
        return {"status": "unknown", "platform": self.platform_name}

    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running skill execution.
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            True if cancellation successful
        """
        logger.warning("Cancel not implemented", platform=self.platform_name, execution_id=execution_id)
        return False

    def _parse_config(self, config: dict[str, Any] | None) -> dict[str, Any]:
        """Parse and validate platform configuration"""
        return config or {}
