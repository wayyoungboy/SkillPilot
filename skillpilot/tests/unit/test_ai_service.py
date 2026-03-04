"""Tests for AI Service"""

import pytest

from skillpilot.core.services.ai_service import ai_service


class TestAIService:
    """Test AI service functionality"""

    @pytest.mark.asyncio
    async def test_mock_analysis(self):
        """Test mock mode task analysis"""
        ai_service.set_provider("mock")
        task = "Scrape data from website and analyze it"

        analysis = await ai_service.analyze_task(task)

        assert "required_capabilities" in analysis
        assert "complexity" in analysis
        assert analysis["complexity"] in ["simple", "medium", "complex"]
        assert "output_format" in analysis

    @pytest.mark.asyncio
    async def test_mock_analysis_report(self):
        """Test mock mode analysis for report generation"""
        ai_service.set_provider("mock")
        task = "Generate a PDF report from the data"

        analysis = await ai_service.analyze_task(task)

        assert "required_capabilities" in analysis
        assert "output_format" in analysis

    @pytest.mark.asyncio
    async def test_mock_chain_generation(self):
        """Test mock mode skill chain generation"""
        ai_service.set_provider("mock")
        task = "Analyze website content"
        available_skills = [
            {
                "skill_id": "sk_1",
                "skill_name": "Web Scraper",
                "platform": "coze",
                "capabilities": ["web_scraping"],
            },
            {
                "skill_id": "sk_2",
                "skill_name": "Analyzer",
                "platform": "dify",
                "capabilities": ["content_analysis"],
            },
        ]

        chain = await ai_service.generate_skill_chain(task, available_skills)

        assert len(chain) > 0
        assert all(step.step > 0 for step in chain)
        assert all(step.skill_id for step in chain)

    @pytest.mark.asyncio
    async def test_mock_chain_empty_skills(self):
        """Test chain generation with no available skills"""
        ai_service.set_provider("mock")
        task = "Do something"

        chain = await ai_service.generate_skill_chain(task, [])

        # Should return empty chain
        assert len(chain) == 0

    @pytest.mark.asyncio
    async def test_provider_switching(self):
        """Test switching AI providers"""
        ai_service.set_provider("mock")
        assert ai_service.provider == "mock"

        ai_service.set_provider("openai")
        assert ai_service.provider == "openai"

        # Reset to mock
        ai_service.set_provider("mock")

    @pytest.mark.asyncio
    async def test_invalid_provider(self):
        """Test that invalid provider raises error"""
        with pytest.raises(ValueError, match="Unknown provider"):
            ai_service.set_provider("invalid_provider")

    @pytest.mark.asyncio
    async def test_complexity_detection(self):
        """Test complexity level detection"""
        ai_service.set_provider("mock")
        simple_task = "Summarize text"
        complex_task = "Generate image and create PDF report"

        simple_analysis = await ai_service.analyze_task(simple_task)
        complex_analysis = await ai_service.analyze_task(complex_task)

        # Mock returns same complexity for both
        assert simple_analysis["complexity"] in ["simple", "medium", "complex"]
        assert complex_analysis["complexity"] in ["simple", "medium", "complex"]
