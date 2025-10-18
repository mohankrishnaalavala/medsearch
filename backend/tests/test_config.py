"""Tests for configuration."""

from app.core.config import settings


def test_settings_loaded() -> None:
    """Test that settings are loaded correctly."""
    assert settings.GOOGLE_CLOUD_PROJECT is not None
    assert settings.VERTEX_AI_CHAT_MODEL == "gemini-2.5-flash"
    assert settings.VERTEX_AI_CHAT_ESCALATION_MODEL == "gemini-2.5-pro"
    assert settings.VERTEX_AI_EMBEDDING_MODEL == "text-embedding-004"


def test_elasticsearch_config() -> None:
    """Test Elasticsearch configuration."""
    assert settings.ELASTICSEARCH_URL is not None
    assert settings.ELASTICSEARCH_INDEX_PUBMED == "medsearch-pubmed"
    assert settings.ELASTICSEARCH_INDEX_TRIALS == "medsearch-trials"
    assert settings.ELASTICSEARCH_INDEX_DRUGS == "medsearch-drugs"


def test_redis_config() -> None:
    """Test Redis configuration."""
    assert settings.REDIS_URL is not None
    assert settings.REDIS_DB == 0


def test_rate_limiting_config() -> None:
    """Test rate limiting configuration."""
    assert settings.RATE_LIMIT_PER_MINUTE > 0
    assert settings.RATE_LIMIT_PER_HOUR > 0

