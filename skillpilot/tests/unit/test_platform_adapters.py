"""Tests for Platform Adapters"""

import pytest

from skillpilot.core.adapters import get_adapter
from skillpilot.core.adapters.base import SkillExecutionRequest
from skillpilot.core.models.common import PlatformType


class TestPlatformAdapters:
    """Test platform adapter functionality"""

    @pytest.mark.asyncio
    async def test_get_coze_adapter(self):
        """Test getting Coze adapter"""
        adapter = get_adapter("coze")
        assert adapter is not None
        assert adapter.platform_name == "coze"

    @pytest.mark.asyncio
    async def test_get_dify_adapter(self):
        """Test getting Dify adapter"""
        adapter = get_adapter("dify")
        assert adapter is not None
        assert adapter.platform_name == "dify"

    @pytest.mark.asyncio
    async def test_get_langchain_adapter(self):
        """Test getting LangChain adapter"""
        adapter = get_adapter("langchain")
        assert adapter is not None
        assert adapter.platform_name == "langchain"

    @pytest.mark.asyncio
    async def test_get_custom_adapter(self):
        """Test getting custom/base adapter"""
        adapter = get_adapter("custom")
        assert adapter is not None
        assert adapter.platform_name == "base"

    @pytest.mark.asyncio
    async def test_get_unknown_adapter(self):
        """Test that unknown adapter returns base adapter"""
        adapter = get_adapter("unknown_platform")
        assert adapter is not None
        assert adapter.platform_name == "base"

    @pytest.mark.asyncio
    async def test_coze_mock_execution(self):
        """Test Coze adapter mock execution"""
        adapter = get_adapter("coze")
        
        request = SkillExecutionRequest(
            skill_id="sk_test",
            skill_name="Test Skill",
            input_data={"test": "input"},
        )
        
        response = await adapter.execute_skill(request)
        
        assert response.success is True
        assert response.output is not None
        assert response.execution_time_ms is not None

    @pytest.mark.asyncio
    async def test_dify_mock_execution(self):
        """Test Dify adapter mock execution"""
        adapter = get_adapter("dify")
        
        request = SkillExecutionRequest(
            skill_id="sk_test",
            skill_name="Test Skill",
            input_data={"test": "input"},
        )
        
        response = await adapter.execute_skill(request)
        
        assert response.success is True
        assert response.output is not None

    @pytest.mark.asyncio
    async def test_langchain_mock_execution(self):
        """Test LangChain adapter mock execution"""
        adapter = get_adapter("langchain")
        
        request = SkillExecutionRequest(
            skill_id="sk_test",
            skill_name="Test Skill",
            input_data={"test": "input"},
        )
        
        response = await adapter.execute_skill(request)
        
        assert response.success is True
        assert response.output is not None

    @pytest.mark.asyncio
    async def test_adapter_health_check(self):
        """Test adapter health check"""
        adapter = get_adapter("coze")
        
        # Should not raise exception
        health = await adapter.health_check()
        assert isinstance(health, bool)

    @pytest.mark.asyncio
    async def test_adapter_validate_skill(self):
        """Test adapter skill validation"""
        adapter = get_adapter("dify")
        
        # Should not raise exception
        is_valid = await adapter.validate_skill("sk_test")
        assert isinstance(is_valid, bool)
