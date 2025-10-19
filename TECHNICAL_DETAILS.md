# Technical Details

This document provides a deeper technical overview of MedSearch AI, focusing on architecture, data flow, search, orchestration, resilience, and operations.

## Architecture (High-level)
- Frontend: Next.js 15 (TypeScript), WebSocket streaming UI
- Backend: FastAPI (Python 3.11), LangGraph-based multi-agent workflow
- Search: Elasticsearch 8.x hybrid (BM25 + vector)
- AI: Google Cloud Vertex AI
  - Embeddings: text-embedding-004
  - LLM: Gemini (Flash) for synthesis and utility prompts
- Cache: Redis
- State: SQLite (agent workflow state)
- Reverse Proxy: Nginx (HTTPS)
- Container Orchestration: Docker Compose

## Data Flow Overview
1. User enters a query in the frontend and creates a search session (REST POST)
2. Frontend opens WebSocket at `/ws/{search_id}`
3. Backend workflow runs: analyze → research → clinical → drug → synthesis
4. Agents perform searches (ES when available; resilient fallback to mock data)
5. Results stream back over WebSocket; final response includes citations and confidence

## Multi-Agent Orchestration
- Query Analyzer: expands/clarifies the user query and extracts intent (research/clinical/drug/general)
- Research Agent: PubMed
- Clinical Agent: ClinicalTrials.gov
- Drug Agent: FDA drugs
- Synthesis Agent: Consolidates results, detects conflicts, and generates a concise response with citations

Routing
- General intent → run all agents, then synthesize
- Specific intent (e.g., clinical_trial) → run targeted agent(s), then synthesize

## Search Implementation (Elasticsearch)
Hybrid search combines:
- Keyword (BM25) for exact term precision
- Vector similarity for semantic recall using Vertex AI embeddings

Indexing
- Separate indices per source (pubmed, trials, drugs)
- Stored fields (e.g., title, abstract, authors, journal, dates, ids)

Querying
- Weighted combination (e.g., semantic_weight ~0.7, keyword_weight ~0.3)
- Filters support (date ranges, study types, etc.)
- Optional reranking via LLM when enabled

## Embeddings & Caching (Vertex AI + Redis)
- Generate query embeddings with text-embedding-004
- Cache recent embeddings in Redis to reduce latency and cost
- Fallback to cache on transient AI errors

## Resilience & Fallbacks
- If Elasticsearch unavailable or returns 0 hits → return curated mock results
- If embedding generation fails → force mock path
- Outer exception guards attempt a last-resort mock rescue before returning empty
- Synthesis only shows "no results" when all sources are truly empty (unlikely with fallbacks)

## Streaming & WebSocket
- REST POST `/api/v1/search` creates a search_id
- WebSocket `wss://<host>/ws/{search_id}` triggers and streams the workflow
- Frontend renders progressive updates and final output with citations

## API Endpoints (Core)
- POST `/api/v1/search` → `{ search_id, status }`
- GET `/api/v1/search/{search_id}` → result snapshot (when complete)
- WS `/ws/{search_id}` → streams progress, intermediate and final results
- GET `/health` → healthcheck

## Error Handling
- Granular try/except around external calls (ES, Redis, Vertex AI)
- Logged with context; degraded-mode messages on startup
- Synthesis fallback assembles a simple, citation-backed response even on model failure

## Security & Privacy Notes
- No PHI in demo; rely on public datasets / mock data
- Secrets loaded from environment and not committed
- HTTPS via Nginx reverse proxy

## Deployment Notes
- Docker Compose for API, frontend, nginx, ES, Redis
- Configurable through `.env` files (backend/frontend)
- VM: Google Compute Engine (e2-standard-2)
- Observability: container logs via `docker compose logs`

## Performance Considerations
- Embedding caching with Redis
- Minimal re-ranking for speed (optional LLM rerank toggle)
- Partial data rendering to avoid blocking on any single source

## Known Limitations / Future Work
- Expand datasets beyond curated subsets
- Add user accounts and saved searches
- Enable offline batch ingestion pipeline with backfill
- Advanced filters (population, outcomes, study design)
- Per-source quality signals and model-based reranking

