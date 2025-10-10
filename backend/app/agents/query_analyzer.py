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
    r"\b(kidney disease|renal disease|chronic kidney disease|ckd|end-stage renal disease|esrd)\b",
    r"\b(resistant hypertension|high blood pressure|cardiovascular disease)\b",
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

    # Build context section if conversation history exists
    context_section = ""
    if conversation_context and conversation_context.get("messages"):
        messages = conversation_context.get("messages", [])
        if len(messages) >= 2:
            # Get last user query and assistant response
            last_user_msg = None
            last_assistant_msg = None
            for msg in reversed(messages):
                if msg.get("role") == "user" and not last_user_msg:
                    last_user_msg = msg.get("content", "")
                elif msg.get("role") == "assistant" and not last_assistant_msg:
                    last_assistant_msg = msg.get("content", "")
                if last_user_msg and last_assistant_msg:
                    break

            if last_user_msg:
                context_section = f"""
CONVERSATION CONTEXT:
Previous Question: "{last_user_msg}"
Previous Answer Summary: "{last_assistant_msg[:300] if last_assistant_msg else 'N/A'}..."

IMPORTANT: The current query may be a follow-up question. If it references "patients", "about", "what about", or uses pronouns without clear antecedents, interpret it in the context of the previous conversation.
"""

    # Build prompt for query analysis
    prompt = f"""{context_section}

Analyze the following medical query and extract:
1. Intent: Classify as one of [research, clinical_trial, drug_info, general]
2. Entities: Extract diseases, drugs, procedures, and symptoms
3. Suggested agents: Which agents should be used [research_agent, clinical_agent, drug_agent]
4. Expanded Query: If this is a follow-up question, expand it to be standalone using context

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
    "expanded_query": "Full standalone version of the query if it's a follow-up, otherwise same as original",
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

        # Get expanded query if available
        expanded_query = analysis_data.get("expanded_query", query)

        return QueryAnalysisOutput(
            intent=analysis_data.get("intent", "general"),
            entities=analysis_data.get("entities", {}),
            confidence=analysis_data.get("confidence", 0.8),
            suggested_agents=analysis_data.get("suggested_agents", ["research_agent"]),
            expanded_query=expanded_query,
        )

    except Exception as e:
        logger.error(f"Error in AI query analysis: {e}")
        # Fallback to heuristic analysis
        return QueryAnalysisOutput(
            intent=detect_intent_heuristic(query),
            entities=extract_entities_regex(query),
            confidence=0.6,
            suggested_agents=["research_agent"],
            expanded_query=query,
        )


async def analyze_query_async(
    query: str, conversation_context: Optional[Dict[str, Any]] = None
) -> QueryAnalysisOutput:
    """
    Analyze query asynchronously using AI with conversation context.

    Args:
        query: User query to analyze
        conversation_context: Optional conversation context with messages

    Returns:
        Query analysis with intent, entities, and suggested agents
    """
    logger.info(f"Analyzing query: {query[:100]}...")

    # Use AI analysis for better context understanding
    try:
        return await analyze_query_with_ai(query, conversation_context)
    except Exception as e:
        logger.error(f"AI analysis failed, falling back to heuristic: {e}")
        # Fallback to heuristic
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
            confidence=0.6,
            suggested_agents=suggested_agents,
            expanded_query=query,
        )


def analyze_query(
    query: str, conversation_context: Optional[Dict[str, Any]] = None
) -> QueryAnalysisOutput:
    """
    Synchronous wrapper for analyze_query (for backward compatibility).

    Args:
        query: User query to analyze
        conversation_context: Optional conversation context

    Returns:
        Query analysis with intent, entities, and suggested agents
    """
    logger.info(f"Analyzing query: {query[:100]}...")

    # Use heuristic analysis for synchronous calls
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
        expanded_query=query,
    )

