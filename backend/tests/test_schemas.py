"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    Citation,
    ConversationCreate,
    SearchFilters,
    SearchRequest,
    SearchResponse,
)


def test_citation_model() -> None:
    """Test Citation model validation."""
    citation = Citation(
        id="pmid_12345",
        source_type="pubmed",
        title="Test Article",
        relevance_score=0.95,
        confidence_score=0.89,
    )

    assert citation.id == "pmid_12345"
    assert citation.source_type == "pubmed"
    assert citation.relevance_score == 0.95


def test_citation_invalid_score() -> None:
    """Test Citation with invalid score."""
    with pytest.raises(ValidationError):
        Citation(
            id="test",
            source_type="pubmed",
            title="Test",
            relevance_score=1.5,  # Invalid: > 1
            confidence_score=0.5,
        )


def test_search_request_valid() -> None:
    """Test valid SearchRequest."""
    request = SearchRequest(
        query="What are the latest treatments for diabetes?",
        filters=SearchFilters(
            date_range={"start": "2020-01-01", "end": "2024-12-31"}
        ),
    )

    assert request.query == "What are the latest treatments for diabetes?"
    assert request.filters is not None
    assert request.filters.date_range is not None


def test_search_request_empty_query() -> None:
    """Test SearchRequest with empty query."""
    with pytest.raises(ValidationError):
        SearchRequest(query="   ")  # Empty after strip


def test_search_request_too_long() -> None:
    """Test SearchRequest with query too long."""
    with pytest.raises(ValidationError):
        SearchRequest(query="a" * 501)  # Max is 500


def test_search_response() -> None:
    """Test SearchResponse model."""
    response = SearchResponse(
        search_id="test-123",
        status="processing",
        estimated_time=5,
        message="Search initiated",
    )

    assert response.search_id == "test-123"
    assert response.status == "processing"
    assert response.estimated_time == 5


def test_conversation_create() -> None:
    """Test ConversationCreate model."""
    request = ConversationCreate(
        user_id="user123",
        title="My Conversation",
    )

    assert request.user_id == "user123"
    assert request.title == "My Conversation"


def test_search_filters() -> None:
    """Test SearchFilters model."""
    filters = SearchFilters(
        date_range={"start": "2020-01-01", "end": "2024-12-31"},
        study_types=["randomized_controlled_trial"],
        languages=["en"],
    )

    assert filters.date_range is not None
    assert len(filters.study_types) == 1
    assert filters.languages == ["en"]

