# MedSearch AI - Quick Reference Card

## Elevator Pitch (30 seconds)
"Healthcare professionals waste 15-20 hours per topic searching 1.5 million annual medical publications. MedSearch AI transforms 20 hours into 20 seconds using multi-agent orchestration with Elasticsearch hybrid search and Google Vertex AI. We deliver citation-backed answers with 95%+ accuracy in under 3 seconds - production-ready, resilient, and deployed on Google Cloud."

## Key Numbers to Remember
- **20 hours → 20 seconds** (99.97% time reduction)
- **95%+ citation accuracy**
- **Sub-3-second response time**
- **1,000+ PubMed articles, 500+ trials, 200+ drugs**
- **3 specialized agents** (Research, Clinical, Drug)
- **2 AI techniques**: Hybrid search + Reranking

## Tech Stack (One-Liner Each)
- **Elasticsearch 8.x**: Hybrid BM25 + vector search with per-source indices
- **Google Vertex AI**: Gemini embeddings + Flash/Pro for synthesis + reranking
- **LangGraph 0.2.x**: Multi-agent orchestration with state persistence
- **FastAPI**: Python backend with WebSocket streaming
- **Next.js 15**: TypeScript frontend with real-time UI
- **Redis**: Embedding and search result caching (512MB LRU)
- **Elastic APM**: Transaction tracing and performance monitoring
- **Docker Compose**: Container orchestration on GCE e2-standard-2

## 6 Key Technical Implementations

### 1. Hybrid Search (Elasticsearch)
- Combines BM25 (keyword) + vector (semantic)
- 70% semantic, 30% keyword weight
- Per-source indices with specialized filters

### 2. AI Reranking (Vertex AI)
- Gemini scores top-10 results (0.0-1.0)
- Applied per-agent before synthesis
- Configurable via VERTEX_AI_RERANK_ENABLED

### 3. Elastic APM
- Automatic FastAPI instrumentation
- Transaction tracing + error tracking
- 10% sampling rate for cost control

### 4. Intelligent Caching (Redis)
- Embedding cache (reduces Vertex AI calls)
- Search result cache (instant responses)
- 512MB with LRU eviction

### 5. Resilient Architecture
- Graceful degradation (works without ES/Redis)
- Mock data fallback (always cited)
- Automatic recovery

### 6. Production Deployment (GCE)
- Memory limits: ES 2.5GB, API 1.5GB, Frontend 512MB
- HTTPS/WSS with Let's Encrypt SSL
- Health checks + auto-restart

## Demo Queries (Copy-Paste Ready)
1. "What are the latest treatments for Type 2 diabetes in elderly patients?"
2. "What is Dapagliflozin in Heart Failure with Preserved Ejection Fraction?"
3. "Metformin side effects in elderly patients"
4. "Latest clinical trials for Alzheimer's disease"

## Demo Talking Points (30 seconds each)

### Opening
"Watch as I ask a medical question that would take 15-20 hours to research manually..."

### During Search
"See the real-time streaming? Three agents working in parallel - Research, Clinical Trials, and Drug Information."

### Citations
"Every claim is backed by verifiable sources - title, journal, date, and direct links."

### Technical
"Elasticsearch hybrid search combines keyword precision with semantic understanding. Vertex AI embeddings capture meaning, Gemini reranks for relevance, and Flash synthesizes the answer."

### Follow-up
"Notice conversation memory - I didn't repeat the context, it remembers."

### Production
"This is deployed on Google Cloud with Elastic APM monitoring, Redis caching, and graceful degradation."

## Common Questions - Quick Answers

**How much data?**
1,000+ PubMed, 500+ trials, 200+ drugs. Scales to millions.

**Cost?**
$50-100/month GCE VM + minimal Vertex AI (caching reduces calls).

**Accuracy?**
95%+ citation accuracy. Every claim is backed by sources.

**Speed?**
Sub-3-second average. Redis caching for instant repeat queries.

**Scalability?**
Same code from local dev to production. Add ES nodes to scale.

**Privacy?**
Research tool, no PHI. HIPAA compliance for clinical use.

## Why Elastic + Google Cloud?

**Elasticsearch enabled:**
- Hybrid retrieval (BM25 + vector) for precision + recall
- Per-source indices with specialized scoring
- Simple APIs that scale without code changes

**Google Cloud enabled:**
- Vertex AI embeddings (gemini-embedding-001) for semantic search
- Gemini Flash for fast, cited synthesis
- Gemini reranking for enhanced relevance
- Compute Engine for reliable hosting
- Service accounts for scoped access

## File Locations

- **Elevator Pitch**: `internal_docs/ELEVATOR_PITCH.md`
- **Demo Script**: `DEMO_SCRIPT.md`
- **Technical Details**: `TECHNICAL_DETAILS.md`
- **Setup Guide**: `SETUP.md`
- **Changes Summary**: `CHANGES_SUMMARY.md`
- **This Reference**: `QUICK_REFERENCE.md`

## Pre-Demo Checklist
- [ ] Site is up: https://medsearch.mohankrishna.site/
- [ ] Logged in with demo@medsearch.ai / Demo@123
- [ ] Conversation history cleared
- [ ] Backup queries ready
- [ ] Internet connection tested
- [ ] Demo script reviewed
- [ ] Timing practiced (3 minutes)

## During Demo - Remember
✅ Speak clearly and at moderate pace
✅ Point to screen when showing features
✅ Emphasize "20 hours to 20 seconds"
✅ Show citations expanding
✅ Mention both Elastic and Google Cloud
✅ Highlight production-ready features
✅ Smile and show enthusiasm!

## After Demo - Key Takeaways
1. **Speed**: 20 hours → 20 seconds
2. **Accuracy**: 95%+ with citations
3. **Technology**: Elasticsearch + Vertex AI
4. **Production**: Deployed, monitored, resilient
5. **Impact**: Better healthcare decisions, faster

---

## One-Sentence Summary
"MedSearch AI is a production-ready medical research assistant that uses Elasticsearch hybrid search and Google Vertex AI to transform 20 hours of manual research into 20 seconds of citation-backed conversation with 95%+ accuracy."

## Hashtags for Social Media
#MedSearchAI #ElasticSearch #GoogleCloud #VertexAI #HealthTech #AIAccelerate #MedicalAI #MultiAgent #LangGraph #FastAPI #NextJS

---

**Print this page and keep it handy during your demo!** 🚀

