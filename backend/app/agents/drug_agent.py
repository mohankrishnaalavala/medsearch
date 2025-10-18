"""Drug information agent for FDA database search."""

import logging
from typing import Any, Dict, List, Optional

from app.services.elasticsearch_service import get_elasticsearch_service
from app.services.redis_service import get_redis_service
from app.services.vertex_ai_service import get_vertex_ai_service
from app.core.config import settings

logger = logging.getLogger(__name__)


async def execute_drug_agent(
    query: str,
    query_embedding: Optional[List[float]] = None,
    filters: Optional[Dict[str, Any]] = None,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Execute drug information agent to search FDA database.

    Args:
        query: Search query
        query_embedding: Pre-computed query embedding (optional)
        filters: Search filters
        max_results: Maximum number of results to return

    Returns:
        List of drug information results
    """
    logger.info(f"Drug information agent searching for: {query[:50]}...")

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

        # Perform hybrid search on drugs index
        results = await es_service.hybrid_search(
            index_name=es_service.indices["drugs"],
            query_text=query,
            query_embedding=query_embedding,
            filters=filters,
            size=max_results,
            keyword_weight=0.5,  # Equal weight for drug searches
            semantic_weight=0.5,
        )

        # Convert to SearchResult format
        search_results = []
        for result in results:
            search_result = {
                "id": result.get("_id", result.get("application_number", "")),
                "source_type": "fda_drug",
                "title": result.get("drug_name", ""),
                "generic_name": result.get("generic_name", ""),
                "brand_names": result.get("brand_names", []),
                "manufacturer": result.get("manufacturer", ""),
                "approval_date": result.get("approval_date", ""),
                "indications": result.get("indications", ""),
                "warnings": result.get("warnings", ""),
                "adverse_reactions": result.get("adverse_reactions", ""),
                "drug_class": result.get("drug_class", ""),
                "route": result.get("route", ""),
                "application_number": result.get("application_number", ""),
                "relevance_score": min(result.get("_score", 0) / 10.0, 1.0),
                "metadata": {
                    "drug_class": result.get("drug_class", ""),
                    "route": result.get("route", ""),
                },
            }
            search_results.append(search_result)

        # Optional Gemini-based reranking (single per-call)
        if settings.VERTEX_AI_RERANK_ENABLED:
            try:
                search_results = await vertex_ai_service.rerank_results(
                    query=query,
                    results=search_results,
                    text_fields=["indications", "warnings", "adverse_reactions"],
                    top_k=settings.VERTEX_AI_RERANK_TOP_K,
                )
            except Exception as e:
                logger.warning(f"Rerank skipped due to error: {e}")

        logger.info(f"Drug information agent found {len(search_results)} results")
        return search_results

    except Exception as e:
        logger.error(f"Error in drug information agent: {e}")
        return []


def rank_drug_results(
    results: List[Dict[str, Any]], query: str
) -> List[Dict[str, Any]]:
    """
    Re-rank drug results based on multiple factors.

    Args:
        results: Drug results to rank
        query: Original query

    Returns:
        Re-ranked results
    """
    query_lower = query.lower()

    for result in results:
        score = result.get("relevance_score", 0.5)

        # Boost if query terms in drug name
        drug_name_lower = result.get("title", "").lower()
        generic_name_lower = result.get("generic_name", "").lower()

        if query_lower in drug_name_lower or query_lower in generic_name_lower:
            score *= 1.5

        # Boost recent approvals
        approval_date = result.get("approval_date", "")
        if approval_date:
            try:
                year = int(approval_date[:4])
                if year >= 2020:
                    score *= 1.2
                elif year >= 2015:
                    score *= 1.1
            except (ValueError, IndexError):
                pass

        # Boost if has brand names (more established)
        if result.get("brand_names"):
            score *= 1.1

        result["final_score"] = min(score, 1.0)

    # Sort by final score
    results.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    return results


async def extract_drug_safety_info(drug: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and summarize drug safety information.

    Args:
        drug: Drug information

    Returns:
        Safety information summary
    """
    vertex_ai_service = get_vertex_ai_service()

    warnings = drug.get("warnings", "")
    adverse_reactions = drug.get("adverse_reactions", "")

    if not warnings and not adverse_reactions:
        return {
            "has_safety_info": False,
            "summary": "No safety information available.",
        }

    prompt = f"""Summarize the key safety information for this drug:

Drug: {drug.get('title', '')}
Warnings: {warnings[:500]}
Adverse Reactions: {adverse_reactions[:500]}

Provide a concise summary of:
1. Main warnings (2-3 key points)
2. Common adverse reactions (top 3-5)
3. Any contraindications

Keep it brief and focused on the most important safety information.
"""

    try:
        summary = await vertex_ai_service.generate_chat_response(
            prompt=prompt,
            temperature=0.2,
            max_output_tokens=300,
        )

        return {
            "has_safety_info": True,
            "summary": summary.strip(),
            "warnings": warnings[:200],
            "adverse_reactions": adverse_reactions[:200],
        }

    except Exception as e:
        logger.error(f"Error extracting safety info: {e}")
        return {
            "has_safety_info": True,
            "summary": f"{warnings[:100]}... {adverse_reactions[:100]}...",
        }


async def compare_drugs(drugs: List[Dict[str, Any]]) -> str:
    """
    Compare multiple drugs and highlight differences.

    Args:
        drugs: List of drug information

    Returns:
        Comparison summary
    """
    if len(drugs) < 2:
        return "Not enough drugs to compare."

    vertex_ai_service = get_vertex_ai_service()

    # Build comparison prompt
    drug_info = []
    for i, drug in enumerate(drugs[:3], 1):  # Compare up to 3 drugs
        drug_info.append(f"""
Drug {i}: {drug.get('title', '')} ({drug.get('generic_name', '')})
- Class: {drug.get('drug_class', 'Unknown')}
- Indications: {drug.get('indications', '')[:200]}
- Route: {drug.get('route', 'Unknown')}
""")

    prompt = f"""Compare these drugs and highlight key differences:

{chr(10).join(drug_info)}

Provide a brief comparison focusing on:
1. Different indications or uses
2. Different drug classes or mechanisms
3. Key distinguishing features

Keep it concise (3-4 sentences).
"""

    try:
        comparison = await vertex_ai_service.generate_chat_response(
            prompt=prompt,
            temperature=0.3,
            max_output_tokens=250,
        )
        return comparison.strip()

    except Exception as e:
        logger.error(f"Error comparing drugs: {e}")
        return "Unable to generate comparison."

