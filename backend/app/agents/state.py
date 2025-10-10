"""LangGraph state definitions for multi-agent workflow."""

from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langgraph.graph import add_messages
from pydantic import BaseModel, Field


# ============================================================================
# Agent State Schema
# ============================================================================


class AgentState(TypedDict):
    """State for the multi-agent workflow.
    
    This state is shared across all agents and persists throughout the workflow.
    """
    
    # Input
    query: str
    """Original user query"""
    
    search_id: str
    """Unique search session identifier"""
    
    user_id: str
    """User identifier"""
    
    conversation_id: Optional[str]
    """Conversation identifier for context"""
    
    filters: Optional[Dict[str, Any]]
    """Search filters (date range, study types, etc.)"""
    
    # Query Analysis
    intent: Optional[str]
    """Detected query intent (research, clinical_trial, drug_info, general)"""
    
    entities: Optional[Dict[str, List[str]]]
    """Extracted entities (diseases, drugs, procedures, etc.)"""
    
    query_embedding: Optional[List[float]]
    """Query embedding vector for semantic search"""
    
    # Agent Results
    research_results: Optional[List[Dict[str, Any]]]
    """Results from research agent (PubMed)"""
    
    clinical_results: Optional[List[Dict[str, Any]]]
    """Results from clinical trials agent"""
    
    drug_results: Optional[List[Dict[str, Any]]]
    """Results from drug information agent"""
    
    # Synthesis
    final_response: Optional[str]
    """Synthesized final response"""
    
    citations: Optional[List[Dict[str, Any]]]
    """List of citations with metadata"""
    
    confidence_score: Optional[float]
    """Overall confidence score (0-1)"""
    
    # Metadata
    agents_used: List[str]
    """List of agents that were executed"""
    
    errors: List[str]
    """List of errors encountered"""
    
    current_step: Optional[str]
    """Current workflow step"""
    
    progress: int
    """Progress percentage (0-100)"""
    
    # Messages (for LangGraph message passing)
    messages: Annotated[List[Any], add_messages]
    """Messages exchanged between agents"""


# ============================================================================
# Agent Input/Output Models
# ============================================================================


class QueryAnalysisInput(BaseModel):
    """Input for query analysis."""
    
    query: str = Field(..., description="User query to analyze")
    conversation_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Previous conversation context"
    )


class QueryAnalysisOutput(BaseModel):
    """Output from query analysis."""

    intent: Literal["research", "clinical_trial", "drug_info", "general"] = Field(
        ..., description="Detected query intent"
    )
    entities: Dict[str, List[str]] = Field(
        default_factory=dict, description="Extracted entities"
    )
    confidence: float = Field(..., ge=0, le=1, description="Analysis confidence")
    suggested_agents: List[str] = Field(
        default_factory=list, description="Agents to execute"
    )
    expanded_query: Optional[str] = Field(
        default=None, description="Expanded query for follow-up questions"
    )


class SearchResult(BaseModel):
    """Individual search result from an agent."""
    
    id: str = Field(..., description="Result identifier")
    source_type: Literal["pubmed", "clinical_trial", "fda_drug"] = Field(
        ..., description="Source type"
    )
    title: str = Field(..., description="Result title")
    abstract: Optional[str] = Field(default=None, description="Abstract or summary")
    authors: Optional[List[str]] = Field(default=None, description="Authors")
    publication_date: Optional[str] = Field(default=None, description="Publication date")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentResult(BaseModel):
    """Result from a specialized agent."""
    
    agent_name: str = Field(..., description="Name of the agent")
    results: List[SearchResult] = Field(default_factory=list, description="Search results")
    execution_time: float = Field(..., description="Execution time in seconds")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    success: bool = Field(default=True, description="Whether execution succeeded")


class SynthesisInput(BaseModel):
    """Input for synthesis agent."""
    
    query: str = Field(..., description="Original query")
    research_results: List[SearchResult] = Field(
        default_factory=list, description="Research results"
    )
    clinical_results: List[SearchResult] = Field(
        default_factory=list, description="Clinical trial results"
    )
    drug_results: List[SearchResult] = Field(
        default_factory=list, description="Drug information results"
    )


class SynthesisOutput(BaseModel):
    """Output from synthesis agent."""
    
    final_response: str = Field(..., description="Synthesized response")
    citations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Citations used"
    )
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence")
    key_findings: List[str] = Field(
        default_factory=list, description="Key findings extracted"
    )


# ============================================================================
# Workflow Configuration
# ============================================================================


class WorkflowConfig(BaseModel):
    """Configuration for the multi-agent workflow."""
    
    max_results_per_agent: int = Field(default=5, description="Max results per agent")
    enable_parallel_execution: bool = Field(
        default=True, description="Enable parallel agent execution"
    )
    timeout_seconds: int = Field(default=30, description="Workflow timeout")
    min_confidence_threshold: float = Field(
        default=0.5, ge=0, le=1, description="Minimum confidence threshold"
    )
    enable_caching: bool = Field(default=True, description="Enable result caching")
    use_escalation_model: bool = Field(
        default=False, description="Use escalation model for synthesis"
    )


# ============================================================================
# Agent Node Names
# ============================================================================


class AgentNodes:
    """Constants for agent node names in the workflow graph."""
    
    START = "start"
    ANALYZE_QUERY = "analyze_query"
    RESEARCH_AGENT = "research_agent"
    CLINICAL_AGENT = "clinical_agent"
    DRUG_AGENT = "drug_agent"
    SYNTHESIZE = "synthesize"
    END = "end"


# ============================================================================
# Workflow Edges
# ============================================================================


class WorkflowEdges:
    """Constants for workflow edge conditions."""
    
    CONTINUE = "continue"
    RESEARCH_ONLY = "research_only"
    CLINICAL_ONLY = "clinical_only"
    DRUG_ONLY = "drug_only"
    ALL_AGENTS = "all_agents"
    SKIP = "skip"

