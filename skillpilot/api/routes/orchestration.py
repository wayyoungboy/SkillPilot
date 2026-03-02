"""Orchestration Routes"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from skillpilot.api.routes.auth import get_current_user
from skillpilot.core.models.common import ListResponse
from skillpilot.core.models.orchestration import Orchestration, OrchestrationCreate
from skillpilot.core.models.user import User
from skillpilot.core.services.orchestration import orchestration_service

router = APIRouter(prefix="/orchestrations", tags=["Orchestration"])


@router.post("", response_model=Orchestration, status_code=status.HTTP_201_CREATED)
async def create_orchestration(
    orchestration_data: OrchestrationCreate, current_user: User = Depends(get_current_user)
):
    """Create orchestration plan"""
    orchestration = await orchestration_service.create_plan(
        user_id=current_user.user_id, task_data=orchestration_data
    )
    return orchestration


@router.get("", response_model=ListResponse)
async def list_orchestrations(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
):
    """List orchestration plans"""
    plans, _ = await orchestration_service.list_plans(
        user_id=current_user.user_id, page=page, limit=limit
    )

    return ListResponse(
        data=[p.model_dump() for p in plans],
        pagination={
            "page": page,
            "limit": limit,
            "total": len(plans),
            "total_pages": (len(plans) + limit - 1) // limit if limit > 0 else 0,
        },
    )


@router.get("/{plan_id}", response_model=Orchestration)
async def get_orchestration(plan_id: str, current_user: User = Depends(get_current_user)):
    """Get orchestration plan details"""
    orchestration = await orchestration_service.get_plan(plan_id)
    if not orchestration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    return orchestration


@router.post("/{plan_id}/execute", response_model=Orchestration)
async def execute_orchestration(plan_id: str, current_user: User = Depends(get_current_user)):
    """Execute orchestration plan"""
    try:
        orchestration = await orchestration_service.execute_plan(plan_id)
        return orchestration
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{plan_id}")
async def cancel_orchestration(plan_id: str, current_user: User = Depends(get_current_user)):
    """Cancel orchestration plan"""
    success = await orchestration_service.cancel_plan(plan_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to cancel plan")

    return {"message": "Plan cancelled"}
