"""Recommendation Routes for AI-powered skill matching"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from skillpilot.api.routes.auth import get_current_user
from skillpilot.core.models.common import ListResponse
from skillpilot.core.models.orchestration import OrchestrationCreate, SkillChainStep
from skillpilot.core.models.user import User
from skillpilot.core.services.orchestration import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/analyze")
async def analyze_task(
    task_description: str = Query(..., description="Task description to analyze"),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze a task description to identify required capabilities.

    Returns analysis results including required capabilities and complexity.
    """
    analysis = await recommendation_service.analyze_task(task_description)
    return analysis


@router.post("/skills")
async def recommend_skills(
    task_description: str = Query(..., description="Task description"),
    limit: int = Query(10, ge=1, le=50, description="Max skills to recommend"),
    current_user: User = Depends(get_current_user),
):
    """
    Recommend skills for a given task using semantic matching.

    Returns ranked list of skill recommendations.
    """
    skills = await recommendation_service.recommend_skills(
        task_description=task_description,
        limit=limit,
    )
    return {"skills": skills, "count": len(skills)}


@router.post("/chain", response_model=list[SkillChainStep], status_code=status.HTTP_201_CREATED)
async def generate_skill_chain(
    request_data: OrchestrationCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a recommended skill chain for completing a task.

    Returns an ordered list of skill steps to accomplish the task.
    """
    skill_chain = await recommendation_service.generate_skill_chain(
        task_description=request_data.task_description
    )
    return skill_chain


@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_recommendation(
    request_data: OrchestrationCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Generate and save a skill chain recommendation.

    Returns the saved plan ID.
    """
    skill_chain = await recommendation_service.generate_skill_chain(
        task_description=request_data.task_description
    )
    plan_id = await recommendation_service.save_recommendation(
        user_id=current_user.user_id,
        task_description=request_data.task_description,
        skill_chain=skill_chain,
    )
    return {"plan_id": plan_id, "steps": len(skill_chain)}


@router.get("/plans", response_model=ListResponse)
async def list_plans(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
):
    """List saved recommendation plans for the current user"""
    plans, pagination = await recommendation_service.list_plans(
        user_id=current_user.user_id, page=page, limit=limit
    )
    return ListResponse(data=plans, pagination=pagination)


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str, current_user: User = Depends(get_current_user)):
    """Get a saved recommendation plan by ID"""
    plan = await recommendation_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan
