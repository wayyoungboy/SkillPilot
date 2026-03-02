"""Vector Search Service for semantic skill matching"""

from datetime import UTC, datetime
from uuid import uuid4

from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.skill import Skill, SkillSearchResult
from skillpilot.core.services.embedding import embedding_service
from skillpilot.core.utils.logger import get_logger
from skillpilot.db.seekdb import seekdb_client

logger = get_logger(__name__)


class VectorSearchService:
    """
    Vector search service for semantic similarity search.
    
    Provides:
    - Semantic skill search using vector embeddings
    - Skill-to-skill similarity recommendations
    - Task-to-skill matching for orchestration
    """

    def __init__(self):
        self.top_k_default = 10
        self.similarity_threshold = 0.5

    async def index_skill(self, skill: Skill) -> bool:
        """
        Index a skill for vector search.
        
        Args:
            skill: Skill object to index
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create searchable text from skill
            searchable_text = self._create_skill_search_text(skill)
            
            # Generate embedding
            embedding = await embedding_service.generate_embedding(searchable_text)
            
            # Store skill vector
            vector_data = {
                "skill_id": skill.skill_id,
                "skill_vector": embedding,
                "capability_vectors": {},  # Can store per-capability vectors
            }
            
            await seekdb_client.insert("skill_vectors", vector_data)
            logger.info("Skill indexed for vector search", skill_id=skill.skill_id)
            return True
            
        except Exception as e:
            logger.error("Failed to index skill", skill_id=skill.skill_id, error=str(e))
            return False

    async def index_skills_batch(self, skills: list[Skill]) -> int:
        """
        Index multiple skills in batch.
        
        Args:
            skills: List of skills to index
            
        Returns:
            Number of successfully indexed skills
        """
        success_count = 0
        for skill in skills:
            if await self.index_skill(skill):
                success_count += 1
        
        logger.info("Batch skill indexing completed", indexed=success_count, total=len(skills))
        return success_count

    async def search_skills_semantic(
        self,
        query: str,
        platforms: list[PlatformType] | None = None,
        top_k: int | None = None,
        threshold: float | None = None,
    ) -> list[SkillSearchResult]:
        """
        Search skills using semantic similarity.
        
        Args:
            query: Search query text
            platforms: Optional platform filters
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of skill search results with similarity scores
        """
        top_k = top_k or self.top_k_default
        threshold = threshold or self.similarity_threshold
        
        try:
            # Generate query embedding
            query_embedding = await embedding_service.generate_embedding(query)
            
            # Build filter conditions
            filter_conditions = None
            if platforms:
                platform_values = [p.value for p in platforms]
                filter_conditions = {"platform": platform_values}
            
            # Perform vector search
            results = await seekdb_client.vector_search(
                table="skill_vectors",
                vector_column="skill_vector",
                query_vector=query_embedding,
                top_k=top_k * 2,  # Get more results to filter by threshold
                filter_conditions=filter_conditions,
            )
            
            # Parse results and apply threshold
            skill_results = []
            for result in results:
                similarity = result.get("similarity", 0.0)
                if similarity >= threshold:
                    skill_id = result.get("skill_id")
                    if skill_id:
                        skill = await self._get_skill_by_id(skill_id)
                        if skill:
                            skill_results.append(
                                SkillSearchResult(**skill.model_dump(), similarity=similarity)
                            )
            
            # Sort by similarity and limit
            skill_results.sort(key=lambda x: x.similarity, reverse=True)
            skill_results = skill_results[:top_k]
            
            logger.info(
                "Semantic skill search completed",
                query=query[:50],
                results_count=len(skill_results),
            )
            return skill_results
            
        except Exception as e:
            logger.error("Semantic search failed", query=query[:50], error=str(e))
            # Fallback to keyword search
            return await self._fallback_keyword_search(query, platforms, top_k)

    async def find_similar_skills(
        self, skill_id: str, top_k: int = 5
    ) -> list[SkillSearchResult]:
        """
        Find skills similar to a given skill.
        
        Args:
            skill_id: Source skill ID
            top_k: Number of similar skills to find
            
        Returns:
            List of similar skills
        """
        try:
            # Get the source skill's vector
            vector_data = await seekdb_client.get("skill_vectors", skill_id)
            if not vector_data or "skill_vector" not in vector_data:
                logger.warning("Skill vector not found", skill_id=skill_id)
                return []
            
            query_vector = vector_data["skill_vector"]
            
            # Search for similar skills
            results = await seekdb_client.vector_search(
                table="skill_vectors",
                vector_column="skill_vector",
                query_vector=query_vector,
                top_k=top_k + 1,  # +1 to exclude the source skill
            )
            
            # Parse results, excluding the source skill
            skill_results = []
            for result in results:
                result_skill_id = result.get("skill_id")
                if result_skill_id and result_skill_id != skill_id:
                    similarity = result.get("similarity", 0.0)
                    skill = await self._get_skill_by_id(result_skill_id)
                    if skill:
                        skill_results.append(
                            SkillSearchResult(**skill.model_dump(), similarity=similarity)
                        )
            
            logger.info("Similar skills found", skill_id=skill_id, count=len(skill_results))
            return skill_results[:top_k]
            
        except Exception as e:
            logger.error("Find similar skills failed", skill_id=skill_id, error=str(e))
            return []

    async def match_skills_to_task(
        self, task_description: str, top_k: int = 10
    ) -> list[SkillSearchResult]:
        """
        Match skills to a task description for orchestration.
        
        Args:
            task_description: Task description text
            top_k: Number of skills to match
            
        Returns:
            List of matched skills ranked by relevance
        """
        # This is essentially a semantic search with task-specific optimization
        return await self.search_skills_semantic(task_description, top_k=top_k)

    async def update_skill_embedding(self, skill: Skill) -> bool:
        """
        Update a skill's embedding when it changes.
        
        Args:
            skill: Updated skill object
            
        Returns:
            True if successful
        """
        # Delete old vector
        try:
            await seekdb_client.delete("skill_vectors", skill.skill_id)
        except Exception:
            pass  # Ignore if doesn't exist
        
        # Index new vector
        return await self.index_skill(skill)

    def _create_skill_search_text(self, skill: Skill) -> str:
        """
        Create searchable text from skill for embedding.
        
        Combines skill name, description, capabilities, and tags.
        """
        parts = [
            skill.skill_name,
            skill.description or "",
            " ".join(skill.capabilities),
            " ".join(skill.tags),
            skill.platform.value,
        ]
        return " ".join(filter(None, parts))

    async def _get_skill_by_id(self, skill_id: str) -> Skill | None:
        """Get skill by ID from database"""
        skill_data = await seekdb_client.get("skills", skill_id)
        if not skill_data:
            return None
        
        from skillpilot.core.services.skill import skill_service
        return skill_service._parse_skill(skill_data)

    async def _fallback_keyword_search(
        self, query: str, platforms: list[PlatformType] | None, top_k: int
    ) -> list[SkillSearchResult]:
        """Fallback to keyword search if vector search fails"""
        logger.warning("Using fallback keyword search", query=query[:50])
        
        from skillpilot.core.services.skill import skill_service
        
        results = await skill_service.search_skills(query, platforms, limit=top_k)
        # Set mock similarity for fallback results
        for result in results:
            result.similarity = 0.5  # Default similarity for keyword matches
        
        return results


vector_search_service = VectorSearchService()
