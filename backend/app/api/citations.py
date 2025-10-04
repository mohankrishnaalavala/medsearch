"""Citations API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.models.schemas import Citation

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/citations/{citation_id}", response_model=Citation)
async def get_citation(citation_id: str) -> Citation:
    """
    Get citation details by ID.

    Args:
        citation_id: Unique citation identifier

    Returns:
        Citation details
    """
    try:
        db = get_db()

        # Get citation from database
        # TODO: Implement get_citation_by_id in database
        # For now, return a placeholder

        raise HTTPException(status_code=404, detail="Citation not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting citation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{search_id}/citations", response_model=List[Citation])
async def get_search_citations(search_id: str) -> List[Citation]:
    """
    Get all citations for a search session.

    Args:
        search_id: Search session identifier

    Returns:
        List of citations
    """
    try:
        db = get_db()

        # Get citations from database
        citations_data = db.get_citations_by_session(search_id)

        # Convert to Citation models
        citations = []
        for citation_data in citations_data:
            citation = Citation(
                id=citation_data["citation_id"],
                source_type=citation_data["source_type"],
                title=citation_data["title"],
                authors=citation_data.get("authors", "").split(",") if citation_data.get("authors") else None,
                journal=citation_data.get("journal"),
                publication_date=citation_data.get("publication_date"),
                abstract=citation_data.get("abstract"),
                relevance_score=citation_data.get("relevance_score", 0.0),
                confidence_score=citation_data.get("confidence_score", 0.0),
            )
            citations.append(citation)

        return citations

    except Exception as e:
        logger.error(f"Error getting search citations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

