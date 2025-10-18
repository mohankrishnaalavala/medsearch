"""Tests for Pillar 3: Synthesis quality and safety."""

import pytest

from app.agents.synthesis_agent import (
    calculate_confidence_score,
    calculate_recency_score,
    detect_conflicts,
    get_confidence_band,
)
from app.core.safety import (
    check_unsafe_content,
    get_crisis_resources,
    hash_user_id,
    redact_pii,
    sanitize_response,
    validate_filters,
)


# ============================================================================
# T3.1: Grounded synthesis with inline citations
# ============================================================================


def test_citation_extraction():
    """Test that citations are properly extracted from results."""
    from app.agents.synthesis_agent import extract_citations
    
    research_results = [
        {
            "id": "pmid123",
            "title": "Test Study",
            "authors": ["Smith J", "Doe A"],
            "journal": "Test Journal",
            "publication_date": "2023-01-01",
            "doi": "10.1234/test",
            "pmid": "123",
            "relevance_score": 0.9,
        }
    ]
    
    citations = extract_citations(research_results, [], [])
    
    assert len(citations) == 1
    assert citations[0]["source_type"] == "pubmed"
    assert citations[0]["title"] == "Test Study"
    assert citations[0]["pmid"] == "123"


# ============================================================================
# T3.2: Conflict/consensus detection
# ============================================================================


@pytest.mark.asyncio
async def test_conflict_detection():
    """Test conflict detection in contradictory results."""
    # This is a unit test - actual conflict detection requires Vertex AI
    # We test the function signature and error handling
    
    research_results = [
        {"title": "Study A", "abstract": "Treatment X is effective"},
        {"title": "Study B", "abstract": "Treatment X shows no benefit"},
    ]
    
    # Should not crash even if Vertex AI is unavailable
    conflicts, summary = await detect_conflicts(research_results, [], [], "test query")
    
    # In test environment without Vertex AI, should return False
    assert isinstance(conflicts, bool)
    assert isinstance(summary, str)


# ============================================================================
# T3.3: Confidence band
# ============================================================================


def test_confidence_score_calculation():
    """Test confidence score calculation."""
    research_results = [
        {"relevance_score": 0.9},
        {"relevance_score": 0.8},
        {"relevance_score": 0.7},
    ]
    
    score = calculate_confidence_score(research_results, [], [])
    
    assert 0.0 <= score <= 1.0
    assert score > 0.0  # Should have some confidence with results


def test_confidence_band_high():
    """Test high confidence band."""
    band = get_confidence_band(confidence_score=0.9, result_count=10, recency_score=0.9)
    assert band == "High"


def test_confidence_band_medium():
    """Test medium confidence band."""
    band = get_confidence_band(confidence_score=0.6, result_count=5, recency_score=0.5)
    assert band == "Medium"


def test_confidence_band_low():
    """Test low confidence band."""
    band = get_confidence_band(confidence_score=0.3, result_count=2, recency_score=0.2)
    assert band == "Low"


def test_recency_score():
    """Test recency score calculation."""
    from datetime import datetime
    
    current_year = datetime.now().year
    
    results = [
        {"publication_date": f"{current_year}-01-01"},  # Current year
        {"publication_date": f"{current_year-1}-01-01"},  # Last year
        {"publication_date": f"{current_year-5}-01-01"},  # 5 years ago
    ]
    
    score = calculate_recency_score(results)
    
    assert 0.0 <= score <= 1.0
    assert score > 0.5  # Should be relatively recent


# ============================================================================
# T3.4: Filters propagate to synthesis
# ============================================================================


def test_filter_validation_valid():
    """Test valid filter validation."""
    filters = {
        "year_range": {"start": 2020, "end": 2024},
        "study_types": ["RCT", "Meta-Analysis"],
    }
    
    is_valid, error = validate_filters(filters)
    
    assert is_valid is True
    assert error is None


def test_filter_validation_invalid_year_range():
    """Test invalid year range validation."""
    filters = {
        "year_range": {"start": 2024, "end": 2020},  # Start after end
    }
    
    is_valid, error = validate_filters(filters)
    
    assert is_valid is False
    assert "Invalid year range" in error


def test_filter_validation_future_year():
    """Test future year validation."""
    filters = {
        "year_range": {"start": 2030, "end": 2035},  # Future years
    }
    
    is_valid, error = validate_filters(filters)
    
    assert is_valid is False
    assert "future" in error.lower()


def test_filter_validation_invalid_study_type():
    """Test invalid study type validation."""
    filters = {
        "study_types": ["InvalidType"],
    }
    
    is_valid, error = validate_filters(filters)
    
    assert is_valid is False
    assert "Invalid study type" in error


# ============================================================================
# T3.5: Safety guardrails
# ============================================================================


def test_unsafe_content_detection_self_harm():
    """Test detection of self-harm content."""
    query = "how to kill myself"
    
    is_unsafe, reason = check_unsafe_content(query)
    
    assert is_unsafe is True
    assert reason is not None


def test_unsafe_content_detection_drug_manufacturing():
    """Test detection of illegal drug manufacturing."""
    query = "how to make meth"
    
    is_unsafe, reason = check_unsafe_content(query)
    
    assert is_unsafe is True
    assert reason is not None


def test_safe_content():
    """Test that safe content passes."""
    query = "what are the treatments for diabetes"
    
    is_unsafe, reason = check_unsafe_content(query)
    
    assert is_unsafe is False
    assert reason is None


def test_pii_redaction_email():
    """Test PII redaction for email addresses."""
    text = "Contact me at john.doe@example.com for more info"
    
    redacted = redact_pii(text)
    
    assert "[EMAIL]" in redacted
    assert "john.doe@example.com" not in redacted


def test_pii_redaction_phone():
    """Test PII redaction for phone numbers."""
    text = "Call me at 555-123-4567"
    
    redacted = redact_pii(text)
    
    assert "[PHONE]" in redacted
    assert "555-123-4567" not in redacted


def test_user_id_hashing():
    """Test user ID hashing for privacy."""
    user_id = "user123"
    
    hashed = hash_user_id(user_id)
    
    assert hashed != user_id
    assert len(hashed) == 16  # SHA256 truncated to 16 chars


def test_crisis_resources():
    """Test crisis resources message."""
    resources = get_crisis_resources()
    
    assert "988" in resources  # Suicide prevention lifeline
    assert "741741" in resources  # Crisis text line


def test_sanitize_response_with_disclaimer():
    """Test response sanitization adds disclaimer."""
    response = "Treatment X is effective for condition Y."
    query = "what is the treatment for Y"
    
    sanitized = sanitize_response(response, query)
    
    assert "Medical Disclaimer" in sanitized
    assert "not medical advice" in sanitized.lower()
    assert response in sanitized


def test_sanitize_response_sensitive_query():
    """Test response sanitization for sensitive queries."""
    response = "Here is some information."
    query = "I want to kill myself"
    
    sanitized = sanitize_response(response, query)
    
    assert "988" in sanitized  # Crisis resources
    assert "Medical Disclaimer" in sanitized

