"""SkillPilot - API Module"""

from fastapi import APIRouter

from .routes import auth, orchestration, skill, vector_search

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(skill.router, prefix="/skills", tags=["Skills"])
api_router.include_router(orchestration.router, prefix="/orchestrations", tags=["Orchestrations"])
api_router.include_router(vector_search.router, prefix="/vector-search", tags=["Vector Search"])

__all__ = ["api_router"]
