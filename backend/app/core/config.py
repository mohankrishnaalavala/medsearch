"""Application configuration using Pydantic settings.

Adds optional Google Secret Manager loading (per-call) and reranker toggles.
"""

import os
import json
import logging
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

    # Optional reranker toggles (uses chat model per call; no deployments)
    VERTEX_AI_RERANK_ENABLED: bool = Field(default=False)
    VERTEX_AI_RERANK_TOP_K: int = Field(default=10)

    # Elasticsearch Configuration
    ELASTICSEARCH_URL: str = Field(default="http://localhost:9200")
    ELASTICSEARCH_USERNAME: str = Field(default="elastic")
    ELASTICSEARCH_PASSWORD: str = Field(default="changeme")
    ELASTICSEARCH_INDEX_PUBMED: str = Field(default="medsearch-pubmed")
    ELASTICSEARCH_INDEX_TRIALS: str = Field(default="medsearch-trials")
    ELASTICSEARCH_INDEX_DRUGS: str = Field(default="medsearch-drugs")

    # Search Fusion & Query Options
    HYBRID_FUSION_STRATEGY: str = Field(default="weighted")  # options: 'weighted' | 'rrf'
    RRF_K: int = Field(default=60)
    QUERY_SYNONYMS_ENABLED: bool = Field(default=True)
    LOG_SEARCH_METRICS: bool = Field(default=True)

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

    # Elastic APM (optional)
    APM_ENABLED: bool = Field(default=False)
    APM_SERVER_URL: str = Field(default="")
    APM_SECRET_TOKEN: str = Field(default="")
    APM_SERVICE_NAME: str = Field(default="medsearch-api")
    APM_ENVIRONMENT: str = Field(default="development")
    APM_TRANSACTION_SAMPLE_RATE: float = Field(default=0.1)
    APM_CAPTURE_BODY: str = Field(default="off")  # 'off'|'errors'|'transactions'|'all'

    # Performance
    SEARCH_TIMEOUT_SECONDS: int = Field(default=30)
    AGENT_TIMEOUT_SECONDS: int = Field(default=60)
    MAX_SEARCH_RESULTS: int = Field(default=20)

    # Secret Manager integration (optional)
    SECRET_MANAGER_SECRET_NAME: str = Field(default="")
    SECRET_MANAGER_SECRET_VERSION: str = Field(default="latest")


def _load_secrets_from_secret_manager_if_configured() -> None:
    """Load environment variables from Google Secret Manager if configured.

    The secret can be either a JSON object of key-value pairs or dotenv-formatted text.
    This is a no-op if SECRET_MANAGER_SECRET_NAME is empty. Import is lazy to avoid
    requiring the dependency when not used.
    """
    secret_name = (
        os.getenv("SECRET_MANAGER_SECRET_NAME")
        or os.getenv("GOOGLE_SECRET_MANAGER_NAME")
        or ""
    )
    if not secret_name:
        return

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "medsearch-ai")
    version = os.getenv("SECRET_MANAGER_SECRET_VERSION", "latest")

    logger = logging.getLogger(__name__)
    try:
        # Lazy import to avoid hard dependency
        from google.cloud import secretmanager  # type: ignore
    except Exception as e:  # pragma: no cover - env-specific
        logger.warning("Secret Manager client not available; skipping: %s", e)
        return

    try:
        client = secretmanager.SecretManagerServiceClient()
        resource = f"projects/{project}/secrets/{secret_name}/versions/{version}"
        response = client.access_secret_version(name=resource)
        payload = response.payload.data.decode("utf-8")

        # Try JSON payload first
        try:
            data = json.loads(payload)
            if isinstance(data, dict):
                # If this looks like a service account key, write to a temp file and point GOOGLE_APPLICATION_CREDENTIALS
                if data.get("type") == "service_account" and "private_key" in data:
                    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or ""
                    if not creds_path:
                        tmp_dir = os.getenv("MEDSEARCH_RUNTIME_DIR", "/tmp")
                        os.makedirs(tmp_dir, exist_ok=True)
                        file_path = os.path.join(tmp_dir, "medsearch-sa.json")
                        with open(file_path, "w") as f:
                            f.write(payload)
                        try:
                            os.chmod(file_path, 0o600)
                        except Exception:
                            pass
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = file_path
                        if data.get("project_id"):
                            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", str(data["project_id"]))
                        logger.info("Loaded service account key from Secret Manager into GOOGLE_APPLICATION_CREDENTIALS")
                    else:
                        logger.info("GOOGLE_APPLICATION_CREDENTIALS already set; not overriding with Secret Manager key")
                    return
                # Otherwise treat as key-value map of env vars
                for k, v in data.items():
                    os.environ.setdefault(str(k), "" if v is None else str(v))
                logger.info("Loaded %d keys from Secret Manager '%s' (JSON)", len(data), secret_name)
                return
        except json.JSONDecodeError:
            pass

        # Fallback to dotenv-style lines
        loaded = 0
        for line in payload.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            loaded += 1
        logger.info("Loaded %d keys from Secret Manager '%s' (dotenv)", loaded, secret_name)
    except Exception as e:  # pragma: no cover - env-specific
        logger.warning("Unable to load secrets from Secret Manager: %s", e)


# Load secrets early (no-op if not configured)
_load_secrets_from_secret_manager_if_configured()

# Create global settings instance
settings = Settings()

