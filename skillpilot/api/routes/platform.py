"""Platform Adapter API Routes"""

from fastapi import APIRouter, HTTPException

from skillpilot.core.adapters.base import SkillExecutionRequest, SkillExecutionResponse
from skillpilot.core.services.skill import skill_service

router = APIRouter(prefix="/platforms", tags=["Platform Adapters"])


@router.get("", summary="List available platforms")
async def list_platforms():
    """List all available platform adapters"""
    platforms = [
        {
            "name": "coze",
            "display_name": "Coze",
            "description": "ByteDance's low-code AI bot development platform",
            "status": "available",
        },
        {
            "name": "dify",
            "display_name": "Dify",
            "description": "Open-source LLM app development platform",
            "status": "available",
        },
        {
            "name": "langchain",
            "display_name": "LangChain/LangServe",
            "description": "Framework for developing LLM applications",
            "status": "available",
        },
        {
            "name": "custom",
            "display_name": "Custom",
            "description": "Custom platform adapter",
            "status": "available",
        },
    ]
    return {"platforms": platforms}


@router.get("/{platform_name}/health", summary="Check platform health")
async def check_platform_health(platform_name: str):
    """Check if a platform adapter is healthy and accessible"""
    from skillpilot.core.adapters import get_adapter
    
    adapter = get_adapter(platform_name)
    
    try:
        is_healthy = await adapter.health_check()
        return {
            "platform": platform_name,
            "healthy": is_healthy,
            "status": "healthy" if is_healthy else "unhealthy",
        }
    except Exception as e:
        return {
            "platform": platform_name,
            "healthy": False,
            "status": "error",
            "error": str(e),
        }


@router.post("/{platform_name}/execute", response_model=SkillExecutionResponse)
async def execute_skill_on_platform(
    platform_name: str,
    request: SkillExecutionRequest,
):
    """
    Execute a skill on a specific platform.
    
    This is a low-level endpoint for direct skill execution.
    For orchestrated execution, use the orchestration endpoints.
    """
    from skillpilot.core.adapters import get_adapter
    
    # Verify skill exists
    skill = await skill_service.get_skill(request.skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Get adapter and execute
    adapter = get_adapter(platform_name)
    
    try:
        response = await adapter.execute_skill(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.get("/{platform_name}/skill/{skill_id}/validate")
async def validate_skill_on_platform(platform_name: str, skill_id: str):
    """
    Validate that a skill exists and is executable on a platform.
    """
    from skillpilot.core.adapters import get_adapter
    
    adapter = get_adapter(platform_name)
    
    try:
        is_valid = await adapter.validate_skill(skill_id)
        return {
            "platform": platform_name,
            "skill_id": skill_id,
            "valid": is_valid,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
