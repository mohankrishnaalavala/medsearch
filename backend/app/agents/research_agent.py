"""Research agent for PubMed search."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.agents.state import SearchResult
from app.services.elasticsearch_service import get_elasticsearch_service
from app.services.redis_service import get_redis_service
from app.services.vertex_ai_service import get_vertex_ai_service

logger = logging.getLogger(__name__)


async def execute_research_agent(
    query: str,
    query_embedding: Optional[List[float]] = None,
    filters: Optional[Dict[str, Any]] = None,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Execute research agent to search PubMed articles.

    Args:
        query: Search query
        query_embedding: Pre-computed query embedding (optional)
        filters: Search filters
        max_results: Maximum number of results to return

    Returns:
        List of search results from PubMed
    """
    logger.info(f"Research agent searching for: {query[:50]}...")

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
                logger.debug("Using cached query embedding")
            else:
                # Generate new embedding
                query_embedding = await vertex_ai_service.generate_embedding(
                    query, task_type="RETRIEVAL_QUERY"
                )
                # Cache it
                await redis_service.set_embedding(query, query_embedding)
                logger.debug("Generated and cached query embedding")

        # Perform hybrid search on PubMed index
        results = await es_service.hybrid_search(
            index_name=es_service.indices["pubmed"],
            query_text=query,
            query_embedding=query_embedding,
            filters=filters,
            size=max_results,
            keyword_weight=0.3,
            semantic_weight=0.7,
        )

        # Convert to SearchResult format
        search_results = []
        for result in results:
            search_result = {
                "id": result.get("_id", result.get("pmid", "unknown")),
                "source_type": "pubmed",
                "title": result.get("title", ""),
                "abstract": result.get("abstract", ""),
                "authors": result.get("authors", []),
                "journal": result.get("journal", ""),
                "publication_date": result.get("publication_date", ""),
                "doi": result.get("doi", ""),
                "pmid": result.get("pmid", ""),
                "relevance_score": min(result.get("_score", 0) / 10.0, 1.0),  # Normalize score
                "metadata": {
                    "mesh_terms": result.get("mesh_terms", []),
                    "keywords": result.get("keywords", []),
                },
            }
            search_results.append(search_result)

        logger.info(f"Research agent found {len(search_results)} results")
        return search_results

    except Exception as e:
        logger.error(f"Error in research agent: {e}")
        return []


async def enrich_research_results(
    results: List[Dict[str, Any]], query: str
) -> List[Dict[str, Any]]:
    """
    Enrich research results with additional analysis.

    Args:
        results: Search results to enrich
        query: Original query for context

    Returns:
        Enriched results with relevance explanations
    """
    vertex_ai_service = get_vertex_ai_service()

    enriched_results = []

    for result in results:
        try:
            # Generate relevance explanation
            prompt = f"""Given this query: "{query}"

And this research article:
Title: {result['title']}
Abstract: {result['abstract'][:500]}...

Explain in 1-2 sentences why this article is relevant to the query.
"""

            explanation = await vertex_ai_service.generate_chat_response(
                prompt=prompt,
                temperature=0.3,
                max_output_tokens=150,
            )

            result["relevance_explanation"] = explanation.strip()
            enriched_results.append(result)

        except Exception as e:
            logger.error(f"Error enriching result: {e}")
            enriched_results.append(result)

    return enriched_results


def rank_research_results(
    results: List[Dict[str, Any]], query: str
) -> List[Dict[str, Any]]:
    """
    Re-rank research results based on multiple factors.

    Args:
        results: Search results to rank
        query: Original query

    Returns:
        Re-ranked results
    """
    query_lower = query.lower()

    for result in results:
        score = result.get("relevance_score", 0.5)

        # Boost recent publications
        pub_date = result.get("publication_date", "")
        if pub_date:
            try:
                year = int(pub_date[:4])
                if year >= 2020:
                    score *= 1.2
                elif year >= 2015:
                    score *= 1.1
            except (ValueError, IndexError):
                pass

        # Boost if query terms in title
        title_lower = result.get("title", "").lower()
        query_terms = query_lower.split()
        title_matches = sum(1 for term in query_terms if term in title_lower)
        if title_matches > 0:
            score *= (1 + 0.1 * title_matches)

        # Boost if has DOI (indicates peer-reviewed)
        if result.get("doi"):
            score *= 1.1

        result["final_score"] = min(score, 1.0)

    # Sort by final score
    results.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    return results

