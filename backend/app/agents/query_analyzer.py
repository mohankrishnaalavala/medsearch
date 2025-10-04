"""Query analysis agent for intent detection and entity extraction."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.agents.state import QueryAnalysisInput, QueryAnalysisOutput
from app.services.vertex_ai_service import get_vertex_ai_service

logger = logging.getLogger(__name__)


# Medical entity patterns
DISEASE_PATTERNS = [
    r"\b(diabetes|cancer|hypertension|alzheimer|parkinson|covid|asthma|copd)\b",
    r"\b(heart disease|stroke|arthritis|depression|anxiety)\b",
]

DRUG_PATTERNS = [
    r"\b(metformin|insulin|aspirin|statin|warfarin|lisinopril)\b",
    r"\b(treatment|medication|drug|therapy|prescription)\b",
]

CLINICAL_TRIAL_PATTERNS = [
    r"\b(clinical trial[s]?|trial[s]?|phase \d)\b",
    r"\b(randomized|placebo|controlled|double-blind)\b",
]


def extract_entities_regex(query: str) -> Dict[str, List[str]]:
    """Extract entities using regex patterns."""
    entities: Dict[str, List[str]] = {
        "diseases": [],
        "drugs": [],
        "procedures": [],
        "symptoms": [],
    }

    query_lower = query.lower()

    # Extract diseases
    for pattern in DISEASE_PATTERNS:
        matches = re.findall(pattern, query_lower, re.IGNORECASE)
        entities["diseases"].extend(matches)

    # Extract drugs
    for pattern in DRUG_PATTERNS:
        matches = re.findall(pattern, query_lower, re.IGNORECASE)
        entities["drugs"].extend(matches)

    # Remove duplicates
    for key in entities:
        entities[key] = list(set(entities[key]))

    return entities


def detect_intent_heuristic(query: str) -> str:
    """Detect query intent using heuristics."""
    query_lower = query.lower()

    # Check for clinical trial keywords (highest priority)
    for pattern in CLINICAL_TRIAL_PATTERNS:
        if re.search(pattern, query_lower):
            return "clinical_trial"

    # Check for research keywords (before drug keywords to avoid false positives)
    if any(
        keyword in query_lower
        for keyword in ["research", "study", "evidence", "literature", "pubmed", "latest research"]
    ):
        return "research"

    # Check for drug information keywords
    if any(
        keyword in query_lower
        for keyword in ["drug", "medication", "prescription", "side effect"]
    ):
        return "drug_info"

    # Default to general
    return "general"


async def analyze_query_with_ai(
    query: str, conversation_context: Optional[Dict[str, Any]] = None
) -> QueryAnalysisOutput:
    """Analyze query using Vertex AI for intent and entity extraction."""
    vertex_ai = get_vertex_ai_service()

    # Build prompt for query analysis
    prompt = f"""Analyze the following medical query and extract:
1. Intent: Classify as one of [research, clinical_trial, drug_info, general]
2. Entities: Extract diseases, drugs, procedures, and symptoms
3. Suggested agents: Which agents should be used [research_agent, clinical_agent, drug_agent]

Query: "{query}"

Respond in JSON format:
{{
    "intent": "research|clinical_trial|drug_info|general",
    "entities": {{
        "diseases": ["disease1", "disease2"],
        "drugs": ["drug1"],
        "procedures": ["procedure1"],
        "symptoms": ["symptom1"]
    }},
    "suggested_agents": ["research_agent", "clinical_agent", "drug_agent"],
    "confidence": 0.95
}}
"""

    try:
        response = await vertex_ai.generate_chat_response(
            prompt=prompt,
            temperature=0.1,  # Low temperature for consistent analysis
            max_output_tokens=500,
        )

        # Parse JSON response
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in response")

        analysis_data = json.loads(json_str)

        return QueryAnalysisOutput(
            intent=analysis_data.get("intent", "general"),
            entities=analysis_data.get("entities", {}),
            confidence=analysis_data.get("confidence", 0.8),
            suggested_agents=analysis_data.get("suggested_agents", ["research_agent"]),
        )

    except Exception as e:
        logger.error(f"Error in AI query analysis: {e}")
        # Fallback to heuristic analysis
        return QueryAnalysisOutput(
            intent=detect_intent_heuristic(query),
            entities=extract_entities_regex(query),
            confidence=0.6,
            suggested_agents=["research_agent"],
        )


def analyze_query(
    query: str, conversation_context: Optional[Dict[str, Any]] = None
) -> QueryAnalysisOutput:
    """
    Analyze query to determine intent and extract entities.

    Args:
        query: User query to analyze
        conversation_context: Optional conversation context

    Returns:
        Query analysis with intent, entities, and suggested agents
    """
    logger.info(f"Analyzing query: {query[:100]}...")

    # Use heuristic analysis for now (fast and reliable)
    # TODO: Enable AI analysis for better accuracy
    intent = detect_intent_heuristic(query)
    entities = extract_entities_regex(query)

    # Determine suggested agents based on intent
    suggested_agents = []
    if intent == "research" or intent == "general":
        suggested_agents.append("research_agent")
    if intent == "clinical_trial" or intent == "general":
        suggested_agents.append("clinical_agent")
    if intent == "drug_info" or intent == "general":
        suggested_agents.append("drug_agent")

    # If no specific intent, use all agents
    if not suggested_agents:
        suggested_agents = ["research_agent", "clinical_agent", "drug_agent"]

    return QueryAnalysisOutput(
        intent=intent,
        entities=entities,
        confidence=0.8,
        suggested_agents=suggested_agents,
    )

