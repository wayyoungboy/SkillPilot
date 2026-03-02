"""Skill Service"""

from datetime import UTC, datetime
from uuid import uuid4

from skillpilot.core.models.common import Pagination, PlatformType
from skillpilot.core.models.skill import (
    Skill,
    SkillCreate,
    SkillSearchResult,
    SkillUpdate,
)
from skillpilot.core.services.vector_search import vector_search_service
from skillpilot.core.utils.logger import get_logger
from skillpilot.db.seekdb import seekdb_client

logger = get_logger(__name__)


class SkillService:
    """Skill service for managing AI skills"""

    async def create_skill(self, skill_data: SkillCreate, developer_id: str) -> Skill:
        """Create a new skill"""
        skill_id = f"sk_{uuid4().hex[:12]}"
        now = datetime.now(UTC)

        skill_dict = {
            "skill_id": skill_id,
            "skill_name": skill_data.skill_name,
            "platform": skill_data.platform.value,
            "developer": developer_id,
            "description": skill_data.description,
            "capabilities": skill_data.capabilities,
            "tags": skill_data.tags,
            "pricing": skill_data.pricing.model_dump(),
            "rating": 0.0,
            "usage_count": 0,
            "created_at": now,
            "updated_at": now,
        }

        await seekdb_client.insert("skills", skill_dict)
        logger.info("Skill created", skill_id=skill_id, developer=developer_id)

        # Create skill model
        skill = Skill(
            skill_id=skill_id,
            skill_name=skill_data.skill_name,
            platform=skill_data.platform,
            developer=developer_id,
            description=skill_data.description,
            capabilities=skill_data.capabilities,
            tags=skill_data.tags,
            pricing=skill_data.pricing,
            created_at=now,
            updated_at=now,
        )

        # Index skill for vector search (async, non-blocking)
        try:
            await vector_search_service.index_skill(skill)
        except Exception as e:
            logger.warning("Failed to index skill for vector search", skill_id=skill_id, error=str(e))

        return skill

    async def get_skill(self, skill_id: str) -> Skill | None:
        """Get skill details by ID"""
        skill_data = await seekdb_client.get("skills", skill_id)
        if not skill_data:
            logger.debug("Skill not found", skill_id=skill_id)
            return None

        return self._parse_skill(skill_data)

    async def update_skill(self, skill_id: str, skill_data: SkillUpdate) -> Skill | None:
        """Update an existing skill"""
        existing = await seekdb_client.get("skills", skill_id)
        if not existing:
            logger.debug("Skill not found for update", skill_id=skill_id)
            return None

        update_dict = skill_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now(UTC)

        if "platform" in update_dict and update_dict["platform"]:
            update_dict["platform"] = update_dict["platform"].value
        if "pricing" in update_dict and update_dict["pricing"]:
            update_dict["pricing"] = update_dict["pricing"].model_dump()

        await seekdb_client.update("skills", skill_id, update_dict)
        logger.info("Skill updated", skill_id=skill_id)

        # Get updated skill
        updated_skill = await self.get_skill(skill_id)
        
        # Re-index skill for vector search if content changed
        if updated_skill and (
            skill_data.skill_name
            or skill_data.description
            or skill_data.capabilities
            or skill_data.tags
        ):
            try:
                await vector_search_service.update_skill_embedding(updated_skill)
            except Exception as e:
                logger.warning("Failed to update skill vector", skill_id=skill_id, error=str(e))

        return updated_skill

    async def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill"""
        existing = await seekdb_client.get("skills", skill_id)
        if not existing:
            logger.debug("Skill not found for deletion", skill_id=skill_id)
            return False

        await seekdb_client.delete("skills", skill_id)
        
        # Also delete skill vector
        try:
            await seekdb_client.delete("skill_vectors", skill_id)
        except Exception:
            pass  # Ignore if vector doesn't exist
        
        logger.info("Skill deleted", skill_id=skill_id)
        return True

    async def list_skills(
        self, platform: PlatformType | None = None, page: int = 1, limit: int = 20
    ) -> tuple[list[Skill], Pagination]:
        """List skills with pagination"""
        filters = {}
        if platform:
            filters["platform"] = platform.value

        offset = (page - 1) * limit
        skills_data = await seekdb_client.query(
            "skills", filters=filters, limit=limit, offset=offset
        )

        # Get total count
        all_skills = await seekdb_client.query("skills", filters=filters, limit=10000)
        total = len(all_skills)

        skills = [self._parse_skill(s) for s in skills_data]
        logger.debug("Listed skills", count=len(skills), total=total, page=page)

        pagination = Pagination(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit if limit > 0 else 0,
        )

        return skills, pagination

    async def search_skills(
        self,
        query: str,
        platforms: list[PlatformType] | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> list[SkillSearchResult]:
        """
        Search skills using semantic vector search.
        
        Falls back to keyword matching if vector search is unavailable.
        """
        # Use vector search service for semantic search
        results = await vector_search_service.search_skills_semantic(
            query=query,
            platforms=platforms,
            top_k=limit,
        )
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_results = results[start_idx:end_idx]
        
        logger.info(
            "Skills searched",
            query=query[:50],
            total_results=len(results),
            returned=len(paginated_results),
        )
        
        return paginated_results

    async def get_similar_skills(self, skill_id: str, limit: int = 5) -> list[SkillSearchResult]:
        """
        Get skills similar to a given skill.
        
        Args:
            skill_id: Source skill ID
            limit: Number of similar skills to return
            
        Returns:
            List of similar skills
        """
        return await vector_search_service.find_similar_skills(skill_id, top_k=limit)

    async def increment_usage(self, skill_id: str) -> None:
        """Increment skill usage count"""
        skill_data = await seekdb_client.get("skills", skill_id)
        if skill_data:
            new_count = skill_data.get("usage_count", 0) + 1
            await seekdb_client.update("skills", skill_id, {"usage_count": new_count})

    async def reindex_all_skills(self) -> int:
        """
        Reindex all skills for vector search.
        
        Useful for migrating existing skills or rebuilding indexes.
        
        Returns:
            Number of successfully indexed skills
        """
        all_skills_data = await seekdb_client.query("skills", filters={}, limit=10000)
        
        success_count = 0
        for skill_data in all_skills_data:
            skill = self._parse_skill(skill_data)
            if await vector_search_service.index_skill(skill):
                success_count += 1
        
        logger.info("All skills reindexed", total=len(all_skills_data), success=success_count)
        return success_count

    def _parse_skill(self, data: dict) -> Skill:
        """Parse skill data from database format to model"""
        return Skill(
            skill_id=data["skill_id"],
            skill_name=data["skill_name"],
            platform=PlatformType(data.get("platform", "custom")),
            developer=data.get("developer"),
            description=data.get("description"),
            capabilities=data.get("capabilities", []),
            tags=data.get("tags", []),
            pricing=data.get("pricing", {}),
            rating=data.get("rating", 0.0),
            usage_count=data.get("usage_count", 0),
            created_at=data.get("created_at", datetime.now(UTC)),
            updated_at=data.get("updated_at", datetime.now(UTC)),
        )


skill_service = SkillService()
