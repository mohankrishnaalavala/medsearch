"""Tests for SQLite database operations."""

import os
import tempfile

import pytest

from app.database.sqlite import SQLiteDatabase


@pytest.fixture
def test_db() -> SQLiteDatabase:
    """Create a test database."""
    # Create temporary database file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    db = SQLiteDatabase(db_path)
    db.init_schema()

    yield db

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_create_search_session(test_db: SQLiteDatabase) -> None:
    """Test creating a search session."""
    test_db.create_search_session(
        session_id="test-session-1",
        user_id="user123",
        query="test query",
    )

    session = test_db.get_search_session("test-session-1")
    assert session is not None
    assert session["session_id"] == "test-session-1"
    assert session["user_id"] == "user123"
    assert session["query"] == "test query"
    assert session["status"] == "processing"


def test_update_search_session(test_db: SQLiteDatabase) -> None:
    """Test updating a search session."""
    test_db.create_search_session(
        session_id="test-session-2",
        user_id="user123",
        query="test query",
    )

    test_db.update_search_session(
        session_id="test-session-2",
        status="completed",
        final_response="Test response",
        confidence_score=0.95,
        execution_time=2.5,
        agents_used=["agent1", "agent2"],
    )

    session = test_db.get_search_session("test-session-2")
    assert session["status"] == "completed"
    assert session["final_response"] == "Test response"
    assert session["confidence_score"] == 0.95
    assert session["execution_time"] == 2.5
    assert session["agents_used"] == "agent1,agent2"


def test_add_citation(test_db: SQLiteDatabase) -> None:
    """Test adding a citation."""
    test_db.create_search_session(
        session_id="test-session-3",
        user_id="user123",
        query="test query",
    )

    test_db.add_citation(
        citation_id="citation-1",
        session_id="test-session-3",
        source_type="pubmed",
        source_id="pmid_12345",
        title="Test Article",
        authors="Smith J, Doe A",
        journal="Test Journal",
        relevance_score=0.95,
        confidence_score=0.89,
    )

    citations = test_db.get_citations_by_session("test-session-3")
    assert len(citations) == 1
    assert citations[0]["citation_id"] == "citation-1"
    assert citations[0]["title"] == "Test Article"


def test_create_conversation(test_db: SQLiteDatabase) -> None:
    """Test creating a conversation."""
    test_db.create_conversation(
        conversation_id="conv-1",
        user_id="user123",
        title="Test Conversation",
    )

    conversation = test_db.get_conversation("conv-1")
    assert conversation is not None
    assert conversation["conversation_id"] == "conv-1"
    assert conversation["user_id"] == "user123"
    assert conversation["title"] == "Test Conversation"


def test_get_user_conversations(test_db: SQLiteDatabase) -> None:
    """Test getting user conversations."""
    test_db.create_conversation(
        conversation_id="conv-1",
        user_id="user123",
        title="Conversation 1",
    )

    test_db.create_conversation(
        conversation_id="conv-2",
        user_id="user123",
        title="Conversation 2",
    )

    conversations = test_db.get_user_conversations("user123")
    assert len(conversations) == 2


def test_get_nonexistent_session(test_db: SQLiteDatabase) -> None:
    """Test getting a nonexistent session."""
    session = test_db.get_search_session("nonexistent")
    assert session is None


def test_get_nonexistent_conversation(test_db: SQLiteDatabase) -> None:
    """Test getting a nonexistent conversation."""
    conversation = test_db.get_conversation("nonexistent")
    assert conversation is None

