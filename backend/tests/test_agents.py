"""Tests for LangGraph agents."""

import pytest

from app.agents.query_analyzer import analyze_query, detect_intent_heuristic, extract_entities_regex
from app.agents.synthesis_agent import calculate_confidence_score, extract_citations


def test_detect_intent_research() -> None:
    """Test intent detection for research queries."""
    query = "What is the latest research on diabetes treatment?"
    intent = detect_intent_heuristic(query)
    assert intent == "research"


def test_detect_intent_clinical_trial() -> None:
    """Test intent detection for clinical trial queries."""
    query = "Are there any clinical trials for Alzheimer's disease?"
    intent = detect_intent_heuristic(query)
    assert intent == "clinical_trial"


def test_detect_intent_drug() -> None:
    """Test intent detection for drug queries."""
    query = "What are the side effects of metformin?"
    intent = detect_intent_heuristic(query)
    assert intent == "drug_info"


def test_detect_intent_general() -> None:
    """Test intent detection for general queries."""
    query = "Tell me about heart disease"
    intent = detect_intent_heuristic(query)
    assert intent == "general"


def test_extract_entities_diseases() -> None:
    """Test entity extraction for diseases."""
    query = "What are treatments for diabetes and hypertension?"
    entities = extract_entities_regex(query)

    assert "diseases" in entities
    assert "diabetes" in entities["diseases"]
    assert "hypertension" in entities["diseases"]


def test_extract_entities_drugs() -> None:
    """Test entity extraction for drugs."""
    query = "Is metformin effective for diabetes treatment?"
    entities = extract_entities_regex(query)

    assert "drugs" in entities
    assert any("metformin" in drug or "treatment" in drug for drug in entities["drugs"])


def test_analyze_query() -> None:
    """Test complete query analysis."""
    query = "What are the latest clinical trials for diabetes treatment?"
    analysis = analyze_query(query)

    assert analysis.intent in ["research", "clinical_trial", "drug_info", "general"]
    assert isinstance(analysis.entities, dict)
    assert isinstance(analysis.suggested_agents, list)
    assert len(analysis.suggested_agents) > 0
    assert 0 <= analysis.confidence <= 1


def test_calculate_confidence_score_no_results() -> None:
    """Test confidence score with no results."""
    score = calculate_confidence_score([], [], [])
    assert score == 0.0


def test_calculate_confidence_score_with_results() -> None:
    """Test confidence score with results."""
    research_results = [
        {"relevance_score": 0.9},
        {"relevance_score": 0.8},
    ]
    clinical_results = [
        {"relevance_score": 0.7},
    ]
    drug_results = []

    score = calculate_confidence_score(research_results, clinical_results, drug_results)
    assert 0 < score <= 1.0


def test_extract_citations() -> None:
    """Test citation extraction."""
    research_results = [
        {
            "id": "pmid_123",
            "title": "Test Article",
            "authors": ["Smith J"],
            "journal": "Test Journal",
            "publication_date": "2024-01-01",
            "doi": "10.1234/test",
            "pmid": "123",
            "relevance_score": 0.9,
        }
    ]
    clinical_results = [
        {
            "id": "nct_456",
            "title": "Test Trial",
            "nct_id": "NCT456",
            "phase": "Phase 3",
            "status": "Recruiting",
            "relevance_score": 0.8,
        }
    ]
    drug_results = [
        {
            "id": "drug_789",
            "title": "Test Drug",
            "generic_name": "testdrug",
            "manufacturer": "Test Pharma",
            "approval_date": "2023-01-01",
            "relevance_score": 0.7,
        }
    ]

    citations = extract_citations(research_results, clinical_results, drug_results)

    assert len(citations) == 3
    assert citations[0]["source_type"] == "pubmed"
    assert citations[1]["source_type"] == "clinical_trial"
    assert citations[2]["source_type"] == "fda_drug"


def test_extract_citations_limits() -> None:
    """Test that citation extraction respects limits."""
    # Create 10 research results
    research_results = [
        {
            "id": f"pmid_{i}",
            "title": f"Article {i}",
            "relevance_score": 0.9,
        }
        for i in range(10)
    ]

    citations = extract_citations(research_results, [], [])

    # Should only extract top 5
    assert len(citations) <= 5


def test_query_analysis_suggested_agents() -> None:
    """Test that query analysis suggests appropriate agents."""
    # Research query
    research_query = "What is the latest research on cancer treatment?"
    analysis = analyze_query(research_query)
    assert "research_agent" in analysis.suggested_agents

    # Clinical trial query
    clinical_query = "Are there clinical trials for COVID-19?"
    analysis = analyze_query(clinical_query)
    assert "clinical_agent" in analysis.suggested_agents

    # Drug query
    drug_query = "What are the side effects of aspirin?"
    analysis = analyze_query(drug_query)
    assert "drug_agent" in analysis.suggested_agents

    # General query should suggest all agents
    general_query = "Tell me about diabetes"
    analysis = analyze_query(general_query)
    assert len(analysis.suggested_agents) >= 1

