"""Search API endpoints."""

import logging
import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.schemas import SearchRequest, SearchResponse, SearchResult
from app.services.elasticsearch_service import get_elasticsearch_service
from app.services.redis_service import get_redis_service
from app.services.vertex_ai_service import get_vertex_ai_service
from app.services.websocket_manager import get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/search", response_model=SearchResponse)
@limiter.limit("10/minute")
async def create_search(request: SearchRequest) -> SearchResponse:
    """
    Create a new search request.

    This endpoint initiates a search and returns a search_id.
    Clients should connect to WebSocket to receive real-time updates.
    """
    try:
        # Generate search ID
        search_id = str(uuid.uuid4())

        # Get database
        db = get_db()

        # Create search session in database
        # For now, using a default user_id
        user_id = "default_user"
        db.create_search_session(
            session_id=search_id,
            user_id=user_id,
            query=request.query,
            conversation_id=request.context.conversation_id if request.context else None,
        )

        logger.info(f"Created search session: {search_id}")

        return SearchResponse(
            search_id=search_id,
            status="processing",
            estimated_time=5,
            message="Search initiated successfully. Connect to WebSocket for updates.",
        )

    except Exception as e:
        logger.error(f"Error creating search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{search_id}", response_model=SearchResult)
async def get_search_result(search_id: str) -> SearchResult:
    """
    Get search result by ID.

    Returns the complete search result including final response and citations.
    """
    try:
        # Get database
        db = get_db()

        # Get search session
        session = db.get_search_session(search_id)

        if not session:
            raise HTTPException(status_code=404, detail="Search not found")

        # Get citations
        citations = db.get_citations_by_session(search_id)

        # Convert to SearchResult
        result = SearchResult(
            search_id=search_id,
            query=session["query"],
            final_response=session.get("final_response", ""),
            citations=[],  # TODO: Convert citations to Citation models
            confidence_score=session.get("confidence_score", 0.0),
            execution_time=session.get("execution_time", 0.0),
            agents_used=session.get("agents_used", "").split(",") if session.get("agents_used") else [],
            created_at=session["created_at"],
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting search result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/search")
async def websocket_search_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time search updates.

    Clients connect here to receive search progress, results, and errors.
    """
    connection_manager = get_connection_manager()

    # For now, using a default user_id
    # In production, extract from authentication
    user_id = "default_user"

    connection_id = await connection_manager.connect(websocket, user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "search_start":
                # Handle search start
                await handle_search_start(data, user_id, connection_manager)

            elif message_type == "search_cancel":
                # Handle search cancellation
                search_id = data.get("payload", {}).get("search_id")
                if search_id:
                    await handle_search_cancel(search_id, user_id, connection_manager)

            elif message_type == "keep_alive":
                # Respond to keep-alive ping
                await websocket.send_json({"type": "pong"})

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


async def handle_search_start(
    data: Dict[str, Any], user_id: str, connection_manager: Any
) -> None:
    """Handle search start message."""
    try:
        payload = data.get("payload", {})
        query = payload.get("query")
        search_id = payload.get("search_id")
        filters = payload.get("filters")

        if not query or not search_id:
            await connection_manager.send_search_error(
                user_id, search_id or "unknown", "INVALID_REQUEST", "Missing query or search_id"
            )
            return

        # Send initial progress
        await connection_manager.send_search_progress(
            user_id, search_id, "processing", "Starting search...", 0, "Initializing"
        )

        # Get services
        es_service = await get_elasticsearch_service()
        redis_service = await get_redis_service()
        vertex_ai_service = get_vertex_ai_service()
        db = get_db()

        start_time = time.time()

        # Check cache
        cached_result = await redis_service.get_search_result(query, filters)
        if cached_result:
            logger.info(f"Returning cached result for: {query[:50]}...")
            await connection_manager.send_search_complete(
                user_id,
                search_id,
                cached_result["final_response"],
                cached_result["citations"],
                cached_result["confidence_score"],
                cached_result["execution_time"],
            )
            return

        # Generate query embedding
        await connection_manager.send_search_progress(
            user_id, search_id, "processing", "Generating query embedding...", 20, "Embedding"
        )

        query_embedding = await vertex_ai_service.generate_embedding(query, "RETRIEVAL_QUERY")

        # Search PubMed
        await connection_manager.send_search_progress(
            user_id, search_id, "processing", "Searching PubMed...", 40, "PubMed Search"
        )

        pubmed_results = await es_service.hybrid_search(
            es_service.indices["pubmed"],
            query,
            query_embedding,
            filters,
            size=5,
        )

        # For now, create a simple response
        # TODO: Implement multi-agent orchestration in Agent 3
        final_response = f"Found {len(pubmed_results)} relevant articles in PubMed."

        execution_time = time.time() - start_time

        # Update database
        db.update_search_session(
            search_id,
            status="completed",
            final_response=final_response,
            confidence_score=0.8,
            execution_time=execution_time,
            agents_used=["research_agent"],
        )

        # Cache result
        result_to_cache = {
            "final_response": final_response,
            "citations": [],
            "confidence_score": 0.8,
            "execution_time": execution_time,
        }
        await redis_service.set_search_result(query, result_to_cache, filters)

        # Send completion
        await connection_manager.send_search_complete(
            user_id, search_id, final_response, [], 0.8, execution_time
        )

    except Exception as e:
        logger.error(f"Error handling search start: {e}")
        await connection_manager.send_search_error(
            user_id, search_id, "SEARCH_ERROR", str(e)
        )


async def handle_search_cancel(
    search_id: str, user_id: str, connection_manager: Any
) -> None:
    """Handle search cancellation."""
    try:
        # Update database
        db = get_db()
        db.update_search_session(search_id, status="cancelled")

        # Send cancellation confirmation
        await connection_manager.send_to_user(
            {
                "type": "search_cancelled",
                "payload": {"search_id": search_id},
            },
            user_id,
        )

        logger.info(f"Search cancelled: {search_id}")

    except Exception as e:
        logger.error(f"Error cancelling search: {e}")

