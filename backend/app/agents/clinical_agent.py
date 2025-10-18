"""Clinical trials agent for ClinicalTrials.gov search."""

import logging
from typing import Any, Dict, List, Optional

from app.services.elasticsearch_service import get_elasticsearch_service
from app.services.redis_service import get_redis_service
from app.services.vertex_ai_service import get_vertex_ai_service
from app.core.config import settings

logger = logging.getLogger(__name__)


async def execute_clinical_agent(
    query: str,
    query_embedding: Optional[List[float]] = None,
    filters: Optional[Dict[str, Any]] = None,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Execute clinical trials agent to search ClinicalTrials.gov.

    Args:
        query: Search query
        query_embedding: Pre-computed query embedding (optional)
        filters: Search filters
        max_results: Maximum number of results to return

    Returns:
        List of clinical trial results
    """
    logger.info(f"Clinical trials agent searching for: {query[:50]}...")

    try:
        # Get services
        es_service = await get_elasticsearch_service()
        redis_service = await get_redis_service()
        vertex_ai_service = get_vertex_ai_service()

        # Generate query embedding if not provided
        if query_embedding is None:
            # Check cache first
            cached_embedding = await redis_service.get_embedding(query)
            if cached_embedding:
                query_embedding = cached_embedding
            else:
                # Generate new embedding
                query_embedding = await vertex_ai_service.generate_embedding(
                    query, task_type="RETRIEVAL_QUERY"
                )
                # Cache it
                await redis_service.set_embedding(query, query_embedding)

        # Perform hybrid search on clinical trials index
        results = await es_service.hybrid_search(
            index_name=es_service.indices["trials"],
            query_text=query,
            query_embedding=query_embedding,
            filters=filters,
            size=max_results,
            keyword_weight=0.4,  # Higher keyword weight for clinical trials
            semantic_weight=0.6,
        )

        # Convert to SearchResult format
        search_results = []
        for result in results:
            search_result = {
                "id": result.get("_id", result.get("nct_id", "")),
                "source_type": "clinical_trial",
                "title": result.get("title", ""),
                "abstract": result.get("brief_summary", ""),
                "description": result.get("detailed_description", ""),
                "nct_id": result.get("nct_id", ""),
                "phase": result.get("phase", ""),
                "status": result.get("status", ""),
                "conditions": result.get("conditions", []),
                "interventions": result.get("interventions", []),
                "locations": result.get("locations", []),
                "start_date": result.get("start_date", ""),
                "completion_date": result.get("completion_date", ""),
                "sponsors": result.get("sponsors", []),
                "relevance_score": min(result.get("_score", 0) / 10.0, 1.0),
                "metadata": {
                    "phase": result.get("phase", ""),
                    "status": result.get("status", ""),
                },
            }
            search_results.append(search_result)

        # Optional Gemini-based reranking (single per-call)
        if settings.VERTEX_AI_RERANK_ENABLED:
            try:
                search_results = await vertex_ai_service.rerank_results(
                    query=query,
                    results=search_results,
                    text_fields=["abstract", "description", "brief_summary", "detailed_description"],
                    top_k=settings.VERTEX_AI_RERANK_TOP_K,
                )
            except Exception as e:
                logger.warning(f"Rerank skipped due to error: {e}")

        logger.info(f"Clinical trials agent found {len(search_results)} results")
        return search_results

    except Exception as e:
        logger.error(f"Error in clinical trials agent: {e}")
        return []


def filter_clinical_trials(
    results: List[Dict[str, Any]], filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Apply additional filters to clinical trial results.

    Args:
        results: Clinical trial results
        filters: Additional filters to apply

    Returns:
        Filtered results
    """
    if not filters:
        return results

    filtered_results = results.copy()

    # Filter by status
    if "status" in filters:
        allowed_statuses = filters["status"]
        if isinstance(allowed_statuses, str):
            allowed_statuses = [allowed_statuses]
        filtered_results = [
            r for r in filtered_results if r.get("status") in allowed_statuses
        ]

    # Filter by phase
    if "phase" in filters:
        allowed_phases = filters["phase"]
        if isinstance(allowed_phases, str):
            allowed_phases = [allowed_phases]
        filtered_results = [
            r for r in filtered_results if r.get("phase") in allowed_phases
        ]

    # Filter by location
    if "locations" in filters:
        target_locations = filters["locations"]
        if isinstance(target_locations, str):
            target_locations = [target_locations]

        filtered_results = [
            r
            for r in filtered_results
            if any(
                loc in r.get("locations", [])
                for loc in target_locations
            )
        ]

    return filtered_results


def rank_clinical_trials(
    results: List[Dict[str, Any]], query: str
) -> List[Dict[str, Any]]:
    """
    Re-rank clinical trial results based on multiple factors.

    Args:
        results: Clinical trial results to rank
        query: Original query

    Returns:
        Re-ranked results
    """
    query_lower = query.lower()

    for result in results:
        score = result.get("relevance_score", 0.5)

        # Boost active/recruiting trials
        status = result.get("status", "").lower()
        if "recruiting" in status or "active" in status:
            score *= 1.3
        elif "completed" in status:
            score *= 1.1

        # Boost later phase trials
        phase = result.get("phase", "").lower()
        if "phase 3" in phase or "phase iii" in phase:
            score *= 1.2
        elif "phase 2" in phase or "phase ii" in phase:
            score *= 1.1

        # Boost if query terms in title
        title_lower = result.get("title", "").lower()
        query_terms = query_lower.split()
        title_matches = sum(1 for term in query_terms if term in title_lower)
        if title_matches > 0:
            score *= (1 + 0.1 * title_matches)

        # Boost if has recent start date
        start_date = result.get("start_date", "")
        if start_date:
            try:
                year = int(start_date[:4])
                if year >= 2020:
                    score *= 1.2
                elif year >= 2015:
                    score *= 1.1
            except (ValueError, IndexError):
                pass

        result["final_score"] = min(score, 1.0)

    # Sort by final score
    results.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    return results


async def summarize_clinical_trial(trial: Dict[str, Any]) -> str:
    """
    Generate a summary of a clinical trial.

    Args:
        trial: Clinical trial data

    Returns:
        Summary text
    """
    vertex_ai_service = get_vertex_ai_service()

    prompt = f"""Summarize this clinical trial in 2-3 sentences:

Title: {trial.get('title', '')}
Phase: {trial.get('phase', 'Unknown')}
Status: {trial.get('status', 'Unknown')}
Conditions: {', '.join(trial.get('conditions', []))}
Interventions: {', '.join(trial.get('interventions', []))}
Brief Summary: {trial.get('abstract', '')[:500]}

Provide a concise summary focusing on the key aspects and findings.
"""

    try:
        summary = await vertex_ai_service.generate_chat_response(
            prompt=prompt,
            temperature=0.3,
            max_output_tokens=200,
        )
        return summary.strip()
    except Exception as e:
        logger.error(f"Error generating trial summary: {e}")
        return trial.get("abstract", "")[:200]

