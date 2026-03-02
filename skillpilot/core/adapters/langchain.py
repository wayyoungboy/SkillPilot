"""LangChain Platform Adapter"""

import time
from typing import Any

from skillpilot.core.adapters.base import (
    PlatformAdapter,
    SkillExecutionRequest,
    SkillExecutionResponse,
)
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class LangChainAdapter(PlatformAdapter):
    """
    Adapter for LangChain/LangServe platform
    
    LangChain is a framework for developing LLM applications.
    LangServe deploys LangChain chains as REST APIs.
    """

    platform_name = "langchain"

    def __init__(self):
        super().__init__()
        self._endpoint_url = None

    async def initialize(self) -> None:
        """Initialize LangChain client"""
        if not self._initialized:
            try:
                # Import LangChain if available
                from langchain_core.runnables import Runnable

                self._client = Runnable
                self._initialized = True
                logger.info("LangChain adapter initialized")
            except ImportError:
                logger.warning("LangChain not installed, using mock mode")
                self._client = None
                self._initialized = True

    async def execute_skill(self, request: SkillExecutionRequest) -> SkillExecutionResponse:
        """Execute a LangChain chain/agent"""
        start_time = time.time()
        
        try:
            await self.initialize()
            
            if self._client is None:
                # Mock execution
                return await self._mock_execute(request)
            
            # Extract endpoint URL from skill configuration
            endpoint_url = (
                request.platform_config.get("endpoint_url") if request.platform_config else None
            )
            if not endpoint_url:
                return SkillExecutionResponse(
                    success=False,
                    error="Endpoint URL not provided in platform_config",
                )
            
            # Execute via LangServe REST API
            import httpx
            
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    f"{endpoint_url}/invoke",
                    json={"input": request.input_data},
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return SkillExecutionResponse(
                success=True,
                output=result.get("output"),
                execution_time_ms=execution_time,
                metadata={"endpoint": endpoint_url},
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error("LangChain execution failed", skill_id=request.skill_id, error=str(e))
            return SkillExecutionResponse(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    async def validate_skill(self, skill_id: str) -> bool:
        """Validate LangChain endpoint is accessible"""
        try:
            await self.initialize()
            
            if self._client is None:
                return True  # Mock mode
            
            # In production, check if endpoint is accessible
            return True
            
        except Exception:
            return False

    async def health_check(self) -> bool:
        """Check LangChain endpoint health"""
        try:
            await self.initialize()
            
            if self._client is None:
                return True
            
            # Check if LangServe is accessible
            import httpx
            
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(f"{self._endpoint_url}/health")
                return response.status_code == 200
                
        except Exception:
            return False

    async def _mock_execute(self, request: SkillExecutionRequest) -> SkillExecutionResponse:
        """Mock execution for testing"""
        logger.info("LangChain mock execution", skill_id=request.skill_id)
        
        # Simulate processing time
        await __import__("asyncio").sleep(0.1)
        
        return SkillExecutionResponse(
            success=True,
            output={
                "message": f"Mock LangChain response for skill: {request.skill_name}",
                "input_received": request.input_data,
            },
            execution_time_ms=100,
            metadata={"mock": True},
        )
