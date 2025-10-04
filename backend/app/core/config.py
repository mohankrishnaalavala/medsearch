"""Application configuration using Pydantic settings."""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: str = Field(default="medsearch-ai")
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(default="./medsearch-key.json")

    # Vertex AI Models
    VERTEX_AI_CHAT_MODEL: str = Field(default="gemini-2.5-flash")
    VERTEX_AI_CHAT_ESCALATION_MODEL: str = Field(default="gemini-2.5-pro")
    VERTEX_AI_EMBEDDING_MODEL: str = Field(default="gemini-embedding-001")
    VERTEX_AI_LOCATION: str = Field(default="us-central1")

    # Elasticsearch Configuration
    ELASTICSEARCH_URL: str = Field(default="http://localhost:9200")
    ELASTICSEARCH_USERNAME: str = Field(default="elastic")
    ELASTICSEARCH_PASSWORD: str = Field(default="changeme")
    ELASTICSEARCH_INDEX_PUBMED: str = Field(default="medsearch-pubmed")
    ELASTICSEARCH_INDEX_TRIALS: str = Field(default="medsearch-trials")
    ELASTICSEARCH_INDEX_DRUGS: str = Field(default="medsearch-drugs")

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379")
    REDIS_DB: int = Field(default=0)
    REDIS_MAX_CONNECTIONS: int = Field(default=20)

    # SQLite Configuration
    SQLITE_PATH: str = Field(default="./data/medsearch.db")
    SQLITE_CHECKPOINT_PATH: str = Field(default="./data/agent_checkpoints.db")

    # API Keys for Data Sources
    PUBMED_API_KEY: str = Field(default="")
    FDA_API_KEY: str = Field(default="")

    # Application Configuration
    APP_ENV: str = Field(default="development")
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)
    APP_DEBUG: bool = Field(default=True)
    APP_RELOAD: bool = Field(default=True)

    # CORS Configuration
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:80")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=10)
    RATE_LIMIT_PER_HOUR: int = Field(default=100)

    # Memory Management
    MAX_MEMORY_PERCENT: float = Field(default=85.0)
    MAX_CONCURRENT_REQUESTS: int = Field(default=3)

    # Logging
    LOG_LEVEL: str = Field(default="DEBUG")
    LOG_FILE: str = Field(default="./logs/medsearch.log")
    LOG_ROTATION_DAYS: int = Field(default=7)

    # Performance
    SEARCH_TIMEOUT_SECONDS: int = Field(default=30)
    AGENT_TIMEOUT_SECONDS: int = Field(default=60)
    MAX_SEARCH_RESULTS: int = Field(default=20)


# Create global settings instance
settings = Settings()

