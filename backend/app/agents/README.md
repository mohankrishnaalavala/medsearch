# MedSearch AI - Multi-Agent System

This directory contains the LangGraph-based multi-agent orchestration system for MedSearch AI.

## Architecture

The system uses **LangGraph** to orchestrate multiple specialized agents that work together to answer medical research queries.

### Workflow

```
User Query
    ↓
Query Analysis (Intent Detection + Entity Extraction)
    ↓
┌─────────────────────────────────────┐
│  Parallel Agent Execution           │
│  ┌──────────────────────────────┐  │
│  │  Research Agent (PubMed)     │  │
│  │  Clinical Trials Agent       │  │
│  │  Drug Information Agent      │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
    ↓
Synthesis Agent (Combine Results)
    ↓
Final Response with Citations
```

## Components

### 1. State Management (`state.py`)

Defines the shared state that flows through the workflow:

- **AgentState**: TypedDict containing query, results, metadata
- **Input/Output Models**: Pydantic models for type safety
- **WorkflowConfig**: Configuration for workflow behavior

### 2. Workflow Orchestrator (`workflow.py`)

The main LangGraph workflow that:

- Builds the state graph with conditional routing
- Manages agent execution order
- Handles checkpointing for conversation continuity
- Provides the `execute()` method for running queries

### 3. Query Analyzer (`query_analyzer.py`)

Analyzes user queries to:

- Detect intent (research, clinical_trial, drug_info, general)
- Extract medical entities (diseases, drugs, procedures)
- Suggest which agents to execute

**Methods:**
- `analyze_query()`: Main entry point
- `detect_intent_heuristic()`: Rule-based intent detection
- `extract_entities_regex()`: Regex-based entity extraction

### 4. Research Agent (`research_agent.py`)

Searches PubMed for research articles:

- Uses hybrid search (BM25 + vector similarity)
- Ranks results by relevance and recency
- Extracts citations with metadata

**Key Functions:**
- `execute_research_agent()`: Main search function
- `rank_research_results()`: Re-ranking logic
- `enrich_research_results()`: Add relevance explanations

### 5. Clinical Trials Agent (`clinical_agent.py`)

Searches ClinicalTrials.gov:

- Filters by phase, status, location
- Prioritizes active/recruiting trials
- Extracts trial metadata (NCT ID, phase, sponsors)

**Key Functions:**
- `execute_clinical_agent()`: Main search function
- `filter_clinical_trials()`: Apply additional filters
- `rank_clinical_trials()`: Re-ranking logic

### 6. Drug Information Agent (`drug_agent.py`)

Searches FDA drug database:

- Finds drug information by name or indication
- Extracts safety information (warnings, adverse reactions)
- Compares multiple drugs

**Key Functions:**
- `execute_drug_agent()`: Main search function
- `rank_drug_results()`: Re-ranking logic
- `extract_drug_safety_info()`: Safety information extraction

### 7. Synthesis Agent (`synthesis_agent.py`)

Combines results from all agents:

- Generates coherent response using Vertex AI
- Extracts and formats citations
- Calculates confidence score
- Identifies key findings

**Key Functions:**
- `synthesize_results()`: Main synthesis function
- `calculate_confidence_score()`: Confidence calculation
- `extract_citations()`: Citation extraction

## Usage

### Basic Usage

```python
from app.agents.workflow import get_workflow

# Get workflow instance
workflow = get_workflow()

# Execute search
final_state = await workflow.execute(
    query="What are the latest treatments for diabetes?",
    search_id="search_123",
    user_id="user_456",
    filters={"date_range": {"start": "2020-01-01"}}
)

# Access results
response = final_state["final_response"]
citations = final_state["citations"]
confidence = final_state["confidence_score"]
```

### Configuration

```python
from app.agents.state import WorkflowConfig
from app.agents.workflow import MedSearchWorkflow

# Custom configuration
config = WorkflowConfig(
    max_results_per_agent=10,
    enable_parallel_execution=True,
    timeout_seconds=60,
    min_confidence_threshold=0.7,
    use_escalation_model=True  # Use gemini-2.5-pro for synthesis
)

workflow = MedSearchWorkflow(config=config)
```

## Agent Routing

The workflow uses conditional routing based on query intent:

| Intent | Agents Executed |
|--------|----------------|
| `research` | Research Agent only |
| `clinical_trial` | Clinical Trials Agent only |
| `drug_info` | Drug Information Agent only |
| `general` | All agents (parallel) |

## Confidence Scoring

Confidence scores (0-1) are calculated based on:

1. **Quantity**: Number of results found (max 0.7)
2. **Quality**: Average relevance score (max 0.3)

Formula:
```
confidence = min(num_results / 10 * 0.7 + avg_relevance * 0.3, 1.0)
```

## Citation Format

Citations include:

- **PubMed**: Title, authors, journal, DOI, PMID
- **Clinical Trials**: Title, NCT ID, phase, status
- **FDA Drugs**: Drug name, generic name, manufacturer, approval date

## Testing

Run tests:

```bash
cd backend
python3 -m pytest tests/test_agents.py -v
```

Tests cover:
- Intent detection (4 tests)
- Entity extraction (2 tests)
- Query analysis (2 tests)
- Confidence scoring (2 tests)
- Citation extraction (2 tests)

## Performance

Target metrics:
- **Response time**: < 3 seconds for typical queries
- **Parallel execution**: Research, Clinical, Drug agents run concurrently
- **Caching**: Query embeddings cached for 24 hours
- **Checkpointing**: Conversation state persisted in memory

## Future Enhancements

1. **AI-Powered Query Analysis**: Use Vertex AI for better intent detection
2. **SQLite Checkpointing**: Persist state to disk for recovery
3. **Result Enrichment**: Add relevance explanations for all results
4. **Multi-Turn Conversations**: Support follow-up questions
5. **Custom Agent Weights**: Allow users to prioritize certain sources
6. **Streaming Synthesis**: Stream response generation in real-time

## Dependencies

- `langgraph==0.2.28`: Workflow orchestration
- `langchain==0.3.1`: LangChain core
- `langchain-google-vertexai>=2.0.0`: Vertex AI integration
- `pydantic==2.9.1`: Data validation

## Error Handling

All agents include error handling:

```python
try:
    results = await execute_research_agent(...)
except Exception as e:
    logger.error(f"Research agent failed: {e}")
    return []  # Return empty results, don't fail entire workflow
```

Errors are collected in `state["errors"]` for debugging.

## Logging

All agents log:
- Query being processed
- Number of results found
- Execution time
- Errors encountered

Example:
```
INFO: Research agent searching for: What are treatments for diabetes...
INFO: Research agent found 5 results
ERROR: Error in research agent: Connection timeout
```

