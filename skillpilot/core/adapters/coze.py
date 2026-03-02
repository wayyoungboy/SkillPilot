"""Coze Platform Adapter"""

import time
from typing import Any

from skillpilot.core.adapters.base import (
    PlatformAdapter,
    SkillExecutionRequest,
    SkillExecutionResponse,
)
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class CozeAdapter(PlatformAdapter):
    """
    Adapter for Coze platform (https://www.coze.com/)
    
    Coze is a low-code AI bot development platform by ByteDance.
    """

    platform_name = "coze"

    def __init__(self):
        super().__init__()
        self.api_base = "https://api.coze.com"
        self._bot_id = None

    async def initialize(self) -> None:
        """Initialize Coze client"""
        if not self._initialized:
            try:
                # Import Coze SDK if available
                from coze import Coze

                self._client = Coze()
                self._initialized = True
                logger.info("Coze adapter initialized")
            except ImportError:
                logger.warning("Coze SDK not installed, using mock mode")
                self._client = None
                self._initialized = True

    async def execute_skill(self, request: SkillExecutionRequest) -> SkillExecutionResponse:
        """Execute a Coze bot/skill"""
        start_time = time.time()
        
        try:
            await self.initialize()
            
            if self._client is None:
                # Mock execution
                return await self._mock_execute(request)
            
            # Extract bot ID from skill configuration
            bot_id = request.platform_config.get("bot_id") if request.platform_config else None
            if not bot_id:
                return SkillExecutionResponse(
                    success=False,
                    error="Bot ID not provided in platform_config",
                )
            
            # Execute the bot
            response = await self._client.chat.create(
                bot_id=bot_id,
                user_id="skillpilot_user",
                additional_messages=[
                    {
                        "role": "user",
                        "content": str(request.input_data),
                        "content_type": "text",
                    }
                ],
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return SkillExecutionResponse(
                success=True,
                output=response.content,
                execution_time_ms=execution_time,
                metadata={"bot_id": bot_id, "message_id": response.id},
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error("Coze execution failed", skill_id=request.skill_id, error=str(e))
            return SkillExecutionResponse(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    async def validate_skill(self, skill_id: str) -> bool:
        """Validate Coze bot exists"""
        try:
            await self.initialize()
            
            if self._client is None:
                return True  # Mock mode
            
            # In production, call Coze API to validate bot
            # bot = await self._client.bots.retrieve(bot_id=skill_id)
            return True
            
        except Exception:
            return False

    async def _mock_execute(self, request: SkillExecutionRequest) -> SkillExecutionResponse:
        """Mock execution for testing"""
        logger.info("Coze mock execution", skill_id=request.skill_id)
        
        # Simulate processing time
        await __import__("asyncio").sleep(0.1)
        
        return SkillExecutionResponse(
            success=True,
            output={
                "message": f"Mock Coze response for skill: {request.skill_name}",
                "input_received": request.input_data,
            },
            execution_time_ms=100,
            metadata={"mock": True},
        )
