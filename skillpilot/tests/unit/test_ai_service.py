"""Tests for AI Service"""

import pytest

from skillpilot.core.services.ai_service import ai_service


class TestAIService:
    """Test AI service functionality"""

    @pytest.mark.asyncio
    async def test_rule_based_analysis(self):
        """Test rule-based task analysis"""
        task = "Scrape data from website and analyze it"
        
        analysis = ai_service._rule_based_analysis(task)
        
        assert "web_scraping" in analysis["required_capabilities"]
        assert "content_analysis" in analysis["required_capabilities"]
        assert analysis["complexity"] in ["simple", "medium", "complex"]
        assert "output_format" in analysis

    @pytest.mark.asyncio
    async def test_rule_based_analysis_report(self):
        """Test rule-based analysis for report generation"""
        task = "Generate a PDF report from the data"
        
        analysis = ai_service._rule_based_analysis(task)
        
        assert "document_generation" in analysis["required_capabilities"]
        assert analysis["output_format"] == "PDF"

    @pytest.mark.asyncio
    async def test_rule_based_chain_generation(self):
        """Test rule-based skill chain generation"""
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
        
        chain = ai_service._rule_based_chain_generation(task, available_skills)
        
        assert len(chain) > 0
        assert all(step.step > 0 for step in chain)
        assert all(step.skill_id for step in chain)

    @pytest.mark.asyncio
    async def test_rule_based_chain_empty_skills(self):
        """Test chain generation with no available skills"""
        task = "Do something"
        
        chain = ai_service._rule_based_chain_generation(task, [])
        
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
        simple_task = "Summarize text"
        complex_task = "Generate image and create PDF report"
        
        simple_analysis = ai_service._rule_based_analysis(simple_task)
        complex_analysis = ai_service._rule_based_analysis(complex_task)
        
        # Complex task should have higher or equal complexity
        complexity_order = {"simple": 1, "medium": 2, "complex": 3}
        assert complexity_order[complex_analysis["complexity"]] >= complexity_order[
            simple_analysis["complexity"]
        ]
