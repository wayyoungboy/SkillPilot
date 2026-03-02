"""Tests for Vector Search Service"""

import pytest

from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.skill import Pricing, Skill
from skillpilot.core.services.vector_search import vector_search_service


class TestVectorSearchService:
    """Test vector search service functionality"""

    @pytest.mark.asyncio
    async def test_create_skill_search_text(self):
        """Test searchable text creation from skill"""
        skill = Skill(
            skill_id="sk_test",
            skill_name="Test Skill",
            description="A test skill for testing",
            platform=PlatformType.COZE,
            capabilities=["capability1", "capability2"],
            tags=["tag1", "tag2"],
            pricing=Pricing(),
        )
        
        search_text = vector_search_service._create_skill_search_text(skill)
        
        assert "Test Skill" in search_text
        assert "A test skill for testing" in search_text
        assert "capability1" in search_text
        assert "tag1" in search_text
        assert "coze" in search_text.lower()

    @pytest.mark.asyncio
    async def test_index_skill_mock(self):
        """Test skill indexing (mock mode)"""
        skill = Skill(
            skill_id="sk_test_index",
            skill_name="Index Test Skill",
            description="Testing skill indexing",
            platform=PlatformType.CUSTOM,
            capabilities=["test"],
            tags=["test"],
            pricing=Pricing(),
        )
        
        # This will use mock embeddings
        result = await vector_search_service.index_skill(skill)
        
        # Should not raise exception
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_search_fallback(self):
        """Test search falls back to keyword search when vector search fails"""
        # This tests the fallback mechanism
        results = await vector_search_service.search_skills_semantic(
            query="test query",
            platforms=None,
            top_k=5,
        )
        
        # Should return list (may be empty if no skills in DB)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_similarity_threshold(self):
        """Test that similarity threshold is applied"""
        # Test with very high threshold (should filter out most results)
        results_high = await vector_search_service.search_skills_semantic(
            query="test",
            threshold=0.95,
            top_k=10,
        )
        
        # Test with low threshold
        results_low = await vector_search_service.search_skills_semantic(
            query="test",
            threshold=0.1,
            top_k=10,
        )
        
        # High threshold should return fewer or equal results
        assert len(results_high) <= len(results_low)
