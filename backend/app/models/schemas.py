"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Citation Models
# ============================================================================


class Citation(BaseModel):
    """Citation model for search results."""

    id: str = Field(..., description="Unique citation identifier")
    source_type: Literal["pubmed", "clinical_trial", "fda_drug"] = Field(
        ..., description="Type of source"
    )
    title: str = Field(..., description="Title of the source")
    authors: Optional[List[str]] = Field(default=None, description="List of authors")
    journal: Optional[str] = Field(default=None, description="Journal name")
    publication_date: Optional[str] = Field(default=None, description="Publication date")
    doi: Optional[str] = Field(default=None, description="DOI identifier")
    pmid: Optional[str] = Field(default=None, description="PubMed ID")
    nct_id: Optional[str] = Field(default=None, description="ClinicalTrials.gov ID")
    abstract: Optional[str] = Field(default=None, description="Abstract text")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score (0-1)")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "pmid_12345678",
                "source_type": "pubmed",
                "title": "Treatment of Type 2 Diabetes in Elderly Patients",
                "authors": ["Smith J", "Johnson A"],
                "journal": "New England Journal of Medicine",
                "publication_date": "2024-01-15",
                "doi": "10.1056/NEJMoa2024001",
                "pmid": "12345678",
                "abstract": "This study examines...",
                "relevance_score": 0.95,
                "confidence_score": 0.89,
            }
        }


# ============================================================================
# Search Models
# ============================================================================


class SearchFilters(BaseModel):
    """Filters for search queries."""

    date_range: Optional[Dict[str, str]] = Field(
        default=None, description="Date range filter with 'start' and 'end' keys"
    )
    study_types: Optional[List[str]] = Field(
        default=None, description="Filter by study types"
    )
    locations: Optional[List[str]] = Field(default=None, description="Filter by locations")
    languages: Optional[List[str]] = Field(default=None, description="Filter by languages")


class ConversationContext(BaseModel):
    """Context from previous conversation."""

    previous_queries: List[str] = Field(default_factory=list, description="Previous queries")
    entities_mentioned: Dict[str, List[str]] = Field(
        default_factory=dict, description="Entities mentioned in conversation"
    )
    conversation_id: str = Field(..., description="Unique conversation identifier")


class SearchRequest(BaseModel):
    """Request model for search endpoint."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    filters: Optional[SearchFilters] = Field(default=None, description="Search filters")
    context: Optional[ConversationContext] = Field(
        default=None, description="Conversation context"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is not empty after stripping."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the latest treatments for Type 2 diabetes in elderly patients?",
                "filters": {
                    "date_range": {"start": "2020-01-01", "end": "2024-12-31"},
                    "study_types": ["randomized_controlled_trial"],
                },
            }
        }


class SearchResponse(BaseModel):
    """Response model for search endpoint."""

    search_id: str = Field(..., description="Unique search identifier")
    status: Literal["processing", "completed", "failed"] = Field(
        ..., description="Search status"
    )
    estimated_time: Optional[int] = Field(
        default=None, description="Estimated completion time in seconds"
    )
    message: Optional[str] = Field(default=None, description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "search_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "estimated_time": 5,
                "message": "Search initiated successfully",
            }
        }


class SearchResult(BaseModel):
    """Complete search result."""

    search_id: str = Field(..., description="Unique search identifier")
    query: str = Field(..., description="Original query")
    final_response: str = Field(..., description="Synthesized response")
    citations: List[Citation] = Field(default_factory=list, description="List of citations")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence score")
    execution_time: float = Field(..., ge=0, description="Execution time in seconds")
    agents_used: List[str] = Field(default_factory=list, description="Agents that were used")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "search_id": "550e8400-e29b-41d4-a716-446655440000",
                "query": "What are the latest treatments for Type 2 diabetes?",
                "final_response": "Based on current research, first-line treatment...",
                "citations": [],
                "confidence_score": 0.89,
                "execution_time": 2.5,
                "agents_used": ["research_agent", "drug_agent"],
                "created_at": "2024-10-04T12:00:00",
            }
        }


# ============================================================================
# WebSocket Message Models
# ============================================================================


class SearchProgressMessage(BaseModel):
    """WebSocket message for search progress."""

    type: Literal["search_progress"] = "search_progress"
    payload: Dict[str, Any] = Field(..., description="Progress payload")


class SearchResultMessage(BaseModel):
    """WebSocket message for search results."""

    type: Literal["search_result"] = "search_result"
    payload: Dict[str, Any] = Field(..., description="Result payload")


class SearchErrorMessage(BaseModel):
    """WebSocket message for search errors."""

    type: Literal["search_error"] = "search_error"
    payload: Dict[str, Any] = Field(..., description="Error payload")


class SearchCompleteMessage(BaseModel):
    """WebSocket message for search completion."""

    type: Literal["search_complete"] = "search_complete"
    payload: Dict[str, Any] = Field(..., description="Completion payload")


# ============================================================================
# Conversation Models
# ============================================================================


class ConversationCreate(BaseModel):
    """Request to create a new conversation."""

    user_id: str = Field(..., description="User identifier")
    title: Optional[str] = Field(default=None, description="Conversation title")


class ConversationResponse(BaseModel):
    """Response for conversation."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    user_id: str = Field(..., description="User identifier")
    title: Optional[str] = Field(default=None, description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(default=0, description="Number of messages")


# ============================================================================
# Error Models
# ============================================================================


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: str = Field(..., description="Request identifier for tracking")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: ErrorDetail = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid query parameter",
                    "details": {"field": "query", "issue": "Query cannot be empty"},
                    "timestamp": "2024-10-04T12:00:00",
                    "request_id": "req_123456",
                }
            }
        }


# ============================================================================
# Health Check Models
# ============================================================================


class ServiceStatus(BaseModel):
    """Status of individual service."""

    status: Literal["up", "down", "degraded"] = Field(..., description="Service status")
    latency_ms: Optional[float] = Field(default=None, description="Service latency in ms")
    message: Optional[str] = Field(default=None, description="Status message")


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Overall system status"
    )
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    services: Dict[str, ServiceStatus] = Field(
        default_factory=dict, description="Individual service statuses"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "environment": "production",
                "services": {
                    "elasticsearch": {"status": "up", "latency_ms": 15.2},
                    "redis": {"status": "up", "latency_ms": 2.1},
                    "vertex_ai": {"status": "up", "latency_ms": 120.5},
                },
                "timestamp": "2024-10-04T12:00:00",
            }
        }

