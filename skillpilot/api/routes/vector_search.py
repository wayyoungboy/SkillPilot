"""Vector Search API Routes"""

from fastapi import APIRouter, HTTPException, Query

from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.skill import SkillSearchResult
from skillpilot.core.services.vector_search import vector_search_service

router = APIRouter(prefix="/vector", tags=["Vector Search"])


@router.post("/search", response_model=list[SkillSearchResult])
async def search_skills_semantic(
    query: str = Query(..., description="Search query text"),
    platforms: list[PlatformType] | None = Query(None, description="Filter by platforms"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Similarity threshold"),
):
    """
    Search skills using semantic similarity.
    
    Uses vector embeddings to find skills semantically similar to the query,
    not just keyword matches.
    """
    try:
        results = await vector_search_service.search_skills_semantic(
            query=query,
            platforms=platforms,
            top_k=top_k,
            threshold=threshold,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/similar/{skill_id}", response_model=list[SkillSearchResult])
async def find_similar_skills(
    skill_id: str,
    top_k: int = Query(5, ge=1, le=50, description="Number of similar skills"),
):
    """
    Find skills similar to a given skill.
    
    Useful for skill recommendations and discovery.
    """
    try:
        results = await vector_search_service.find_similar_skills(skill_id, top_k=top_k)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar skills: {str(e)}")


@router.post("/skills/{skill_id}/index")
async def index_skill_for_search(skill_id: str):
    """
    Index or re-index a skill for vector search.
    
    Useful when a skill is updated or if the vector index needs rebuilding.
    """
    from skillpilot.core.services.skill import skill_service
    
    skill = await skill_service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    try:
        success = await vector_search_service.index_skill(skill)
        if success:
            return {"status": "success", "message": "Skill indexed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to index skill")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/skills/reindex-all")
async def reindex_all_skills():
    """
    Re-index all skills for vector search.
    
    This is a heavy operation and should be used sparingly.
    """
    from skillpilot.core.services.skill import skill_service
    
    try:
        count = await skill_service.reindex_all_skills()
        return {
            "status": "success",
            "message": f"Successfully indexed {count} skills",
            "indexed_count": count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")
