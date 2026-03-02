"""Skill Routes"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from skillpilot.api.routes.auth import get_current_user
from skillpilot.core.models.common import ListResponse, PlatformType
from skillpilot.core.models.skill import (
    Skill,
    SkillCreate,
    SkillSearchResult,
    SkillUpdate,
)
from skillpilot.core.models.user import User
from skillpilot.core.services.skill import skill_service

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("", response_model=ListResponse)
async def list_skills(
    platform: PlatformType | None = Query(None, description="Filter by platform"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
):
    """List skills"""
    skills, pagination = await skill_service.list_skills(platform=platform, page=page, limit=limit)

    return ListResponse(data=[s.model_dump() for s in skills], pagination=pagination)


@router.get("/search", response_model=list[SkillSearchResult])
async def search_skills(
    q: str = Query(..., description="Search query"),
    platforms: list[PlatformType] | None = Query(None, description="Filter by platforms"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
):
    """Search skills"""
    results = await skill_service.search_skills(
        query=q, platforms=platforms, page=page, limit=limit
    )

    return results


@router.get("/{skill_id}", response_model=Skill)
async def get_skill(skill_id: str, current_user: User = Depends(get_current_user)):
    """Get skill details"""
    skill = await skill_service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    return skill


@router.post("", response_model=Skill, status_code=status.HTTP_201_CREATED)
async def create_skill(skill_data: SkillCreate, current_user: User = Depends(get_current_user)):
    """Create skill"""
    skill = await skill_service.create_skill(skill_data, current_user.user_id)
    return skill


@router.put("/{skill_id}", response_model=Skill)
async def update_skill(
    skill_id: str, skill_data: SkillUpdate, current_user: User = Depends(get_current_user)
):
    """Update skill"""
    skill = await skill_service.update_skill(skill_id, skill_data)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(skill_id: str, current_user: User = Depends(get_current_user)):
    """Delete skill"""
    success = await skill_service.delete_skill(skill_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
