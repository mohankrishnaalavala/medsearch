"""SQLite database operations for agent state persistence."""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class SQLiteDatabase:
    """SQLite database manager for agent state persistence."""

    def __init__(self, db_path: str) -> None:
        """Initialize database connection."""
        self.db_path = db_path
        self._ensure_db_directory()

    def _ensure_db_directory(self) -> None:
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Search sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_sessions (
                    session_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    user_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    status TEXT CHECK(status IN ('processing', 'completed', 'failed', 'cancelled')) DEFAULT 'processing',
                    final_response TEXT,
                    confidence_score REAL,
                    execution_time REAL,
                    agents_used TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
                )
            """)

            # Citations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS citations (
                    citation_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    authors TEXT,
                    journal TEXT,
                    publication_date DATE,
                    abstract TEXT,
                    relevance_score REAL,
                    confidence_score REAL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES search_sessions(session_id)
                )
            """)

            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES search_sessions(session_id)
                )
            """)

            # Create indices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
                ON conversations(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_sessions_user_id 
                ON search_sessions(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_sessions_status 
                ON search_sessions(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_citations_session_id 
                ON citations(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_session_id 
                ON performance_metrics(session_id)
            """)

            conn.commit()
            logger.info("Database schema initialized successfully")

    def create_search_session(
        self, session_id: str, user_id: str, query: str, conversation_id: Optional[str] = None
    ) -> None:
        """Create a new search session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO search_sessions (session_id, user_id, query, conversation_id)
                VALUES (?, ?, ?, ?)
            """,
                (session_id, user_id, query, conversation_id),
            )

    def update_search_session(
        self,
        session_id: str,
        status: Optional[str] = None,
        final_response: Optional[str] = None,
        confidence_score: Optional[float] = None,
        execution_time: Optional[float] = None,
        agents_used: Optional[List[str]] = None,
    ) -> None:
        """Update search session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params: List[Any] = []

            if status:
                updates.append("status = ?")
                params.append(status)
            if final_response:
                updates.append("final_response = ?")
                params.append(final_response)
            if confidence_score is not None:
                updates.append("confidence_score = ?")
                params.append(confidence_score)
            if execution_time is not None:
                updates.append("execution_time = ?")
                params.append(execution_time)
            if agents_used:
                updates.append("agents_used = ?")
                params.append(",".join(agents_used))

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(session_id)

            query = f"UPDATE search_sessions SET {', '.join(updates)} WHERE session_id = ?"
            cursor.execute(query, params)

    def get_search_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get search session by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM search_sessions WHERE session_id = ?", (session_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_citation(
        self,
        citation_id: str,
        session_id: str,
        source_type: str,
        source_id: str,
        title: str,
        **kwargs: Any,
    ) -> None:
        """Add citation to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO citations (
                    citation_id, session_id, source_type, source_id, title,
                    authors, journal, publication_date, abstract,
                    relevance_score, confidence_score, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    citation_id,
                    session_id,
                    source_type,
                    source_id,
                    title,
                    kwargs.get("authors"),
                    kwargs.get("journal"),
                    kwargs.get("publication_date"),
                    kwargs.get("abstract"),
                    kwargs.get("relevance_score"),
                    kwargs.get("confidence_score"),
                    kwargs.get("metadata"),
                ),
            )

    def get_citations_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all citations for a session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM citations WHERE session_id = ?", (session_id,))
            return [dict(row) for row in cursor.fetchall()]

    def create_conversation(
        self, conversation_id: str, user_id: str, title: Optional[str] = None
    ) -> None:
        """Create a new conversation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversations (conversation_id, user_id, title)
                VALUES (?, ?, ?)
            """,
                (conversation_id, user_id, title),
            )

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?", (conversation_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's conversations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM conversations 
                WHERE user_id = ? 
                ORDER BY updated_at DESC 
                LIMIT ?
            """,
                (user_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]


# Global database instance
_db: Optional[SQLiteDatabase] = None


def init_db() -> None:
    """Initialize global database instance."""
    global _db
    _db = SQLiteDatabase(settings.SQLITE_PATH)
    _db.init_schema()
    logger.info(f"Database initialized at {settings.SQLITE_PATH}")


def get_db() -> SQLiteDatabase:
    """Get global database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db

