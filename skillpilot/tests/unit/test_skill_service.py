"""Skill Service Unit Tests"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skillpilot.core.models import PlatformType, Pricing, SkillCreate
from skillpilot.core.services.skill import SkillService


class TestSkillService:
    """Skill service tests"""

    @pytest.mark.asyncio
    async def test_create_skill(self):
        """Test skill creation"""
        service = SkillService()

        skill_data = SkillCreate(
            skill_name="Test Skill",
            platform=PlatformType.COZE,
            description="A test skill",
            capabilities=["coding", "testing"],
            tags=["test", "demo"],
            pricing=Pricing(type="free"),
        )

        with patch.object(service, "_parse_skill") as mock_parse:
            mock_parse.return_value = MagicMock(
                skill_id="sk_test123",
                skill_name="Test Skill",
                platform=PlatformType.COZE,
            )

            with patch("skillpilot.core.services.skill.seekdb_client") as mock_db:
                mock_db.insert = AsyncMock()

                skill = await service.create_skill(skill_data, "usr_test")

                assert skill is not None
                mock_db.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_skill(self):
        """Test getting skill details"""
        service = SkillService()

        mock_skill_data = {
            "skill_id": "sk_test123",
            "skill_name": "Test Skill",
            "platform": "coze",
            "description": "A test skill",
            "capabilities": ["coding"],
            "tags": ["test"],
            "pricing": {"type": "free"},
            "rating": 4.5,
            "usage_count": 100,
        }

        with patch("skillpilot.core.services.skill.seekdb_client") as mock_db:
            mock_db.get = AsyncMock(return_value=mock_skill_data)

            skill = await service.get_skill("sk_test123")

            assert skill is not None
            assert skill.skill_id == "sk_test123"
            mock_db.get.assert_called_once_with("skills", "sk_test123")

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self):
        """Test getting non-existent skill"""
        service = SkillService()

        with patch("skillpilot.core.services.skill.seekdb_client") as mock_db:
            mock_db.get = AsyncMock(return_value=None)

            skill = await service.get_skill("sk_nonexistent")

            assert skill is None

    @pytest.mark.asyncio
    async def test_delete_skill(self):
        """Test deleting skill"""
        service = SkillService()

        with patch("skillpilot.core.services.skill.seekdb_client") as mock_db:
            mock_db.get = AsyncMock(return_value={"skill_id": "sk_test123"})
            mock_db.delete = AsyncMock()

            result = await service.delete_skill("sk_test123")

            assert result is True
            # Should delete from both skills and skill_vectors tables
            assert mock_db.delete.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_skill_not_found(self):
        """Test deleting non-existent skill"""
        service = SkillService()

        with patch("skillpilot.core.services.skill.seekdb_client") as mock_db:
            mock_db.get = AsyncMock(return_value=None)

            result = await service.delete_skill("sk_nonexistent")

            assert result is False

    @pytest.mark.asyncio
    async def test_list_skills(self):
        """Test listing skills"""
        service = SkillService()

        mock_skills = [
            {
                "skill_id": "sk_1",
                "skill_name": "Skill 1",
                "platform": "coze",
                "description": "Desc 1",
                "capabilities": [],
                "tags": [],
                "pricing": {"type": "free"},
            },
            {
                "skill_id": "sk_2",
                "skill_name": "Skill 2",
                "platform": "dify",
                "description": "Desc 2",
                "capabilities": [],
                "tags": [],
                "pricing": {"type": "free"},
            },
        ]

        with patch("skillpilot.core.services.skill.seekdb_client") as mock_db:
            mock_db.query = AsyncMock(return_value=mock_skills)

            skills, pagination = await service.list_skills(page=1, limit=20)

            assert len(skills) == 2
            assert pagination.page == 1
            assert pagination.limit == 20

    @pytest.mark.asyncio
    async def test_search_skills(self):
        """Test searching skills"""
        service = SkillService()

        mock_skill_data = {
            "skill_id": "sk_1",
            "skill_name": "Code Review Pro",
            "platform": "coze",
            "description": "A skill for code review",
            "capabilities": ["review"],
            "tags": ["code"],
            "pricing": {"type": "free"},
        }

        # Mock vector_search_service to return results
        with patch("skillpilot.core.services.skill.vector_search_service") as mock_vector:
            from skillpilot.core.models.skill import SkillSearchResult
            from skillpilot.core.models.common import PlatformType
            from datetime import UTC, datetime

            mock_result = SkillSearchResult(
                skill_id="sk_1",
                skill_name="Code Review Pro",
                platform=PlatformType.COZE,
                description="A skill for code review",
                capabilities=["review"],
                tags=["code"],
                pricing={"type": "free"},
                rating=0.0,
                usage_count=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                similarity=0.8,
            )
            mock_vector.search_skills_semantic = AsyncMock(return_value=[mock_result])

            results = await service.search_skills(query="code", page=1, limit=10)

            assert len(results) >= 1
            assert results[0].skill_name == "Code Review Pro"

    @pytest.mark.asyncio
    async def test_increment_usage(self):
        """Test incrementing skill usage count"""
        service = SkillService()

        mock_skill = {"skill_id": "sk_test", "usage_count": 10}

        with patch("skillpilot.core.services.skill.seekdb_client") as mock_db:
            mock_db.get = AsyncMock(return_value=mock_skill)
            mock_db.update = AsyncMock()

            await service.increment_usage("sk_test")

            mock_db.update.assert_called_once_with("skills", "sk_test", {"usage_count": 11})
