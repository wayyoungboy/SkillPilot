"""SkillPilot Configuration Module"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # SeekDB (Single storage - Vector DB + Relational storage)
    seekdb_url: str = Field(default="seekdb://localhost:6432", description="SeekDB connection URL")
    seekdb_vector_dimension: int = Field(default=1536, description="Vector dimension")
    seekdb_index_type: str = Field(default="hnsw", description="Vector index type")
    seekdb_hnsw_m: int = Field(default=16, description="HNSW M parameter")
    seekdb_hnsw_ef_construction: int = Field(default=200, description="HNSW ef_construction")

    # JWT
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production", description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=15, description="Access token expiry (minutes)"
    )
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiry (days)")

    # API
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    project_name: str = Field(default="SkillPilot", description="Project name")
    debug: bool = Field(default=False, description="Debug mode")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, description="Requests per minute limit")

    # AI Providers
    openai_api_key: str | None = Field(default=None, description="OpenAI API Key")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API Key")
    embedding_provider: str = Field(default="mock", description="Embedding provider (openai, local, mock)")
    llm_provider: str = Field(default="mock", description="LLM provider (openai, anthropic, mock)")

    # Platform APIs
    coze_api_base: str = Field(default="https://api.coze.com", description="Coze API Base URL")
    dify_api_key: str | None = Field(default=None, description="Dify API Key")
    dify_api_base: str = Field(default="https://api.dify.ai/v1", description="Dify API Base URL")
    langchain_endpoint_url: str | None = Field(default=None, description="LangChain/LangServe Endpoint")


@lru_cache
def get_settings() -> Settings:
    """Get settings singleton"""
    return Settings()


settings = get_settings()
