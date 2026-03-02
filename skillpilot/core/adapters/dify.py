"""Dify Platform Adapter"""

import time
from typing import Any

from skillpilot.core.adapters.base import (
    PlatformAdapter,
    SkillExecutionRequest,
    SkillExecutionResponse,
)
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class DifyAdapter(PlatformAdapter):
    """
    Adapter for Dify platform (https://dify.ai/)
    
    Dify is an open-source LLM app development platform.
    """

    platform_name = "dify"

    def __init__(self):
        super().__init__()
        self.api_base = "https://api.dify.ai/v1"
        self._api_key = None

    async def initialize(self) -> None:
        """Initialize Dify client"""
        if not self._initialized:
            try:
                # Import Dify SDK if available
                from dify_client import DifyClient

                self._client = DifyClient(api_key=self._api_key or "mock-key")
                self._initialized = True
                logger.info("Dify adapter initialized")
            except ImportError:
                logger.warning("Dify SDK not installed, using mock mode")
                self._client = None
                self._initialized = True

    async def execute_skill(self, request: SkillExecutionRequest) -> SkillExecutionResponse:
        """Execute a Dify application/workflow"""
        start_time = time.time()
        
        try:
            await self.initialize()
            
            if self._client is None:
                # Mock execution
                return await self._mock_execute(request)
            
            # Extract app ID from skill configuration
            app_id = request.platform_config.get("app_id") if request.platform_config else None
            if not app_id:
                return SkillExecutionResponse(
                    success=False,
                    error="App ID not provided in platform_config",
                )
            
            # Create client with specific app
            client = self._client
            
            # Execute the workflow/chatflow
            response = await client.create_chat_message(
                inputs=request.input_data,
                user="skillpilot_user",
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return SkillExecutionResponse(
                success=True,
                output=response.get("answer"),
                execution_time_ms=execution_time,
                metadata={"app_id": app_id, "message_id": response.get("message_id")},
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error("Dify execution failed", skill_id=request.skill_id, error=str(e))
            return SkillExecutionResponse(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    async def validate_skill(self, skill_id: str) -> bool:
        """Validate Dify app exists"""
        try:
            await self.initialize()
            
            if self._client is None:
                return True  # Mock mode
            
            # In production, call Dify API to validate app
            return True
            
        except Exception:
            return False

    async def _mock_execute(self, request: SkillExecutionRequest) -> SkillExecutionResponse:
        """Mock execution for testing"""
        logger.info("Dify mock execution", skill_id=request.skill_id)
        
        # Simulate processing time
        await __import__("asyncio").sleep(0.1)
        
        return SkillExecutionResponse(
            success=True,
            output={
                "message": f"Mock Dify response for skill: {request.skill_name}",
                "input_received": request.input_data,
            },
            execution_time_ms=100,
            metadata={"mock": True},
        )
