"""Configuration Module Unit Tests"""

from unittest.mock import patch

from skillpilot.core.config import Settings


class TestSettings:
    """Settings tests"""

    def test_default_settings(self):
        """Test default configuration"""
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()

            assert settings.project_name == "PowerSkills"
            assert settings.api_v1_prefix == "/api/v1"
            assert settings.debug is False

    def test_jwt_settings(self):
        """Test JWT configuration"""
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()

            assert settings.jwt_algorithm == "HS256"
            assert settings.access_token_expire_minutes == 15
            assert settings.refresh_token_expire_days == 7

    def test_seekdb_settings(self):
        """Test SeekDB configuration"""
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()

            assert settings.seekdb_url == "seekdb://localhost:6432"
            assert settings.seekdb_vector_dimension == 1536
            assert settings.seekdb_index_type == "hnsw"
            assert settings.seekdb_hnsw_m == 16

    def test_rate_limit_settings(self):
        """Test rate limit configuration"""
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()

            assert settings.rate_limit_per_minute == 100

    def test_settings_from_env(self):
        """Test loading configuration from environment variables"""
        with patch.dict(
            "os.environ",
            {"PROJECT_NAME": "TestApp", "DEBUG": "true", "RATE_LIMIT_PER_MINUTE": "200"},
            clear=True,
        ):
            settings = Settings()

            assert settings.project_name == "TestApp"
            assert settings.debug is True
            assert settings.rate_limit_per_minute == 200


class TestGetSettings:
    """Settings singleton tests"""

    def test_get_settings_returns_same_instance(self):
        """Test get_settings returns same instance"""
        from skillpilot.core.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2
