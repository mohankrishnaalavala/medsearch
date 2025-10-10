"""Conversations API endpoints."""

import logging
import uuid
from typing import List

from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.models.schemas import ConversationCreate, ConversationResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: ConversationCreate) -> ConversationResponse:
    """
    Create a new conversation.

    Args:
        request: Conversation creation request

    Returns:
        Created conversation details
    """
    try:
        db = get_db()

        # Generate conversation ID
        conversation_id = str(uuid.uuid4())

        # Create conversation in database
        db.create_conversation(
            conversation_id=conversation_id,
            user_id=request.user_id,
            title=request.title,
        )

        # Get created conversation
        conversation = db.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=500, detail="Failed to create conversation")

        return ConversationResponse(
            conversation_id=conversation["conversation_id"],
            user_id=conversation["user_id"],
            title=conversation.get("title"),
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"],
            message_count=0,
        )

    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str) -> ConversationResponse:
    """
    Get conversation by ID.

    Args:
        conversation_id: Conversation identifier

    Returns:
        Conversation details
    """
    try:
        db = get_db()

        conversation = db.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # TODO: Get message count from search_sessions
        message_count = 0

        return ConversationResponse(
            conversation_id=conversation["conversation_id"],
            user_id=conversation["user_id"],
            title=conversation.get("title"),
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"],
            message_count=message_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(user_id: str, limit: int = 50) -> List[ConversationResponse]:
    """
    Get user's conversations.

    Args:
        user_id: User identifier
        limit: Maximum number of conversations to return

    Returns:
        List of conversations
    """
    try:
        db = get_db()

        conversations_data = db.get_user_conversations(user_id, limit)

        conversations = []
        for conv_data in conversations_data:
            conversation = ConversationResponse(
                conversation_id=conv_data["conversation_id"],
                user_id=conv_data["user_id"],
                title=conv_data.get("title"),
                created_at=conv_data["created_at"],
                updated_at=conv_data["updated_at"],
                message_count=0,  # TODO: Get actual count
            )
            conversations.append(conversation)

        return conversations

    except Exception as e:
        logger.error(f"Error getting user conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

