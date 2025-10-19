# Technical Details

This document provides a deeper technical overview of MedSearch AI, focusing on architecture, data flow, search, orchestration, resilience, and operations.

## Architecture (High-level)
- Frontend: Next.js 15 (TypeScript), WebSocket streaming UI
- Backend: FastAPI (Python 3.11), LangGraph-based multi-agent workflow
- Search: Elasticsearch 8.x hybrid (BM25 + vector)
- AI: Google Cloud Vertex AI
  - Embeddings: gemini-embedding-001
  - LLM: Gemini 2.5 Flash (with escalation to Gemini 2.5 Pro) for synthesis and utility prompts
  - Optional AI-powered reranking using Gemini models
- Cache: Redis (embedding cache + search result cache)
- State: SQLite (agent workflow state)
- Reverse Proxy: Nginx (HTTPS with Let's Encrypt SSL)
- Container Orchestration: Docker Compose
- Monitoring: Elastic APM (optional, configurable)

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
- Dense vector fields for semantic search

Querying
- Weighted combination (e.g., semantic_weight ~0.7, keyword_weight ~0.3)
- Configurable fusion strategy: weighted or RRF (Reciprocal Rank Fusion)
- Filters support (date ranges, study types, phases, etc.)
- Query synonym expansion (optional)

Reranking (Optional)
- AI-powered reranking using Gemini models
- Configurable via `VERTEX_AI_RERANK_ENABLED` flag
- Scores top-k results (default: 10) for relevance
- Applied per-agent (research, clinical, drug) before synthesis
- Fallback to original ranking on errors

## Embeddings & Caching (Vertex AI + Redis)
- Generate query embeddings with gemini-embedding-001
- Cache recent embeddings in Redis to reduce latency and cost
- Fallback to cache on transient AI errors
- Search result caching with TTL for frequently asked queries
- Configurable cache expiration and max connections

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

## Monitoring & Observability (Elastic APM)
Elastic APM provides comprehensive application performance monitoring:

Configuration (Optional)
- Enable via `APM_ENABLED=true` environment variable
- Configure APM server URL, secret token, and service name
- Adjustable transaction sample rate (default: 0.1 or 10%)
- Configurable body capture: off/errors/transactions/all

Features
- Automatic instrumentation of FastAPI endpoints
- Transaction tracing across multi-agent workflow
- Error tracking with stack traces
- Performance metrics (response times, throughput)
- Service dependencies visualization
- Custom transaction sampling for cost control

## Error Handling
- Granular try/except around external calls (ES, Redis, Vertex AI)
- Logged with context; degraded-mode messages on startup
- Synthesis fallback assembles a simple, citation-backed response even on model failure
- APM error tracking captures exceptions with full context

## Security & Privacy Notes
- No PHI in demo; rely on public datasets / mock data
- Secrets loaded from environment and not committed
- HTTPS via Nginx reverse proxy

## Deployment Notes
- Docker Compose for API, frontend, nginx, ES, Redis
- Configurable through `.env` files (backend/frontend)
- VM: Google Compute Engine (e2-standard-2, 8GB RAM, 2 vCPU)
- SSL: Let's Encrypt certificates via Certbot
- Observability:
  - Container logs via `docker compose logs`
  - Elastic APM for application performance monitoring (optional)
  - Health checks for all services

Production Configuration
- Memory limits per container (ES: 2.5GB, API: 1.5GB, Frontend: 512MB, Redis: 600MB, Nginx: 256MB)
- CPU limits to prevent resource contention
- Automatic restart policies (unless-stopped)
- Health checks with retries for service reliability

## Performance Considerations
- Embedding caching with Redis (reduces Vertex AI API calls)
- Search result caching for frequently asked queries
- Minimal re-ranking for speed (optional LLM rerank toggle)
- Partial data rendering to avoid blocking on any single source
- Configurable search timeouts and result limits
- Rate limiting to prevent abuse (10/min, 100/hour default)
- Memory management with max concurrent request limits

## Known Limitations / Future Work
- Expand datasets beyond curated subsets
- Add user accounts and saved searches
- Enable offline batch ingestion pipeline with backfill
- Advanced filters (population, outcomes, study design)
- Per-source quality signals and model-based reranking

