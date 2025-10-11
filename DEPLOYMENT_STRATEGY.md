# Google Cloud Deployment Strategy for MedSearch AI

## Executive Summary

**Recommendation: Google Cloud Run (Managed Services)**

For this multi-container application, I recommend a **hybrid approach** using Google Cloud Run for stateless services (frontend, backend API) combined with managed services (Cloud SQL, Memorystore Redis, Elasticsearch Service) for optimal cost, scalability, and ease of management.

---

## Deployment Options Comparison

### Option 1: Google Compute Engine (VM) ⭐ **Current Setup**

**Architecture:**
```
Single e2-standard-2 VM (2 vCPU, 8GB RAM)
├── Docker Compose orchestration
├── Frontend (Next.js)
├── Backend API (FastAPI)
├── Elasticsearch
└── Redis
```

**Pros:**
- ✅ Full control over infrastructure
- ✅ Simple Docker Compose deployment
- ✅ All services on one machine (low latency)
- ✅ Predictable monthly cost
- ✅ Easy to debug and monitor
- ✅ No cold starts

**Cons:**
- ❌ Manual scaling (vertical only)
- ❌ Single point of failure
- ❌ Requires VM management and patching
- ❌ No automatic failover
- ❌ Limited to VM capacity
- ❌ Always running (even with no traffic)

**Cost Estimate:**
- e2-standard-2 VM: ~$50/month (24/7)
- 50GB SSD: ~$8/month
- Egress (100GB): ~$12/month
- **Total: ~$70/month**

**Best For:**
- Development and testing
- Proof of concept
- Low to medium traffic (<1000 requests/day)
- Budget-conscious deployments

---

### Option 2: Google Cloud Run (Serverless) ⭐ **Recommended for Production**

**Architecture:**
```
Cloud Run Services (Serverless)
├── Frontend Service (Next.js)
├── Backend API Service (FastAPI)
├── Cloud SQL for PostgreSQL (agent state)
├── Memorystore Redis (caching)
└── Elastic Cloud (managed Elasticsearch)
```

**Pros:**
- ✅ Auto-scaling (0 to N instances)
- ✅ Pay only for actual usage
- ✅ Automatic HTTPS and load balancing
- ✅ Built-in CI/CD with Cloud Build
- ✅ High availability and fault tolerance
- ✅ No server management
- ✅ Generous free tier (2M requests/month)
- ✅ WebSocket support (for real-time streaming)

**Cons:**
- ❌ Cold starts (1-3 seconds)
- ❌ Requires restructuring from Docker Compose
- ❌ Managed services cost more than self-hosted
- ❌ Request timeout limits (60 minutes max)
- ❌ More complex architecture

**Cost Estimate (Low Traffic):**
- Cloud Run Frontend: $0-5/month (within free tier)
- Cloud Run Backend: $0-10/month (within free tier)
- Cloud SQL (db-f1-micro): ~$7/month
- Memorystore Redis (1GB): ~$50/month
- Elastic Cloud (4GB): ~$95/month
- **Total: ~$152-167/month**

**Cost Estimate (Medium Traffic - 100K requests/month):**
- Cloud Run Frontend: ~$15/month
- Cloud Run Backend: ~$25/month
- Cloud SQL (db-g1-small): ~$25/month
- Memorystore Redis (1GB): ~$50/month
- Elastic Cloud (8GB): ~$190/month
- **Total: ~$305/month**

**Best For:**
- Production deployments
- Variable traffic patterns
- Need for high availability
- Scalability requirements
- Professional/commercial use

---

### Option 3: Hybrid Approach (VM + Managed Services)

**Architecture:**
```
Compute Engine VM (e2-medium)
├── Frontend (Next.js)
└── Backend API (FastAPI)

Managed Services
├── Elastic Cloud (managed Elasticsearch)
├── Memorystore Redis
└── Cloud SQL (optional)
```

**Pros:**
- ✅ Balance of control and managed services
- ✅ Offload heavy services (Elasticsearch)
- ✅ Better resource utilization
- ✅ Easier to scale individual components

**Cons:**
- ❌ More complex networking
- ❌ Higher cost than pure VM
- ❌ Still requires VM management

**Cost Estimate:**
- e2-medium VM: ~$25/month
- Elastic Cloud (4GB): ~$95/month
- Memorystore Redis (1GB): ~$50/month
- **Total: ~$170/month**

---

## Cloud Run Free Tier Details

### Request Limits (Free Tier)
- **2 million requests per month** (free)
- **360,000 GB-seconds of memory** (free)
- **180,000 vCPU-seconds** (free)
- **1 GB network egress per month** (free)

### What This Means for MedSearch AI
Assuming average request takes 2 seconds with 512MB memory:
- **Free tier covers:** ~90,000 requests/month
- **Beyond free tier:** $0.40 per million requests

For a hackathon demo or MVP, you'll likely stay within free tier!

---

## Technical Considerations for Cloud Run Migration

### 1. Restructuring Required

**Current (Docker Compose):**
```yaml
services:
  frontend:
    build: ./frontend
  api:
    build: ./backend
  elasticsearch:
    image: elasticsearch:8.15
  redis:
    image: redis:7-alpine
```

**Cloud Run (Separate Services):**
```
frontend/
├── Dockerfile (optimized for Cloud Run)
└── cloudbuild.yaml

backend/
├── Dockerfile (optimized for Cloud Run)
└── cloudbuild.yaml

# Replace with managed services
- Elastic Cloud
- Memorystore Redis
- Cloud SQL (optional)
```

### 2. Code Changes Needed

**Backend API (`backend/app/core/config.py`):**
```python
# Before (Docker Compose)
ELASTICSEARCH_URL = "http://elasticsearch:9200"
REDIS_URL = "redis://redis:6379"

# After (Cloud Run)
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")  # Elastic Cloud URL
REDIS_URL = os.getenv("REDIS_URL")  # Memorystore Redis URL
```

**Frontend (`frontend/next.config.mjs`):**
```javascript
// Before
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// After
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api-xxxxx.run.app'
```

### 3. WebSocket Considerations

Cloud Run **supports WebSockets** (since 2021), but:
- Connection timeout: 60 minutes max
- Idle timeout: 15 minutes (can be extended)
- Need to handle reconnection logic

**Recommendation:** Implement heartbeat/ping-pong to keep connection alive.

### 4. State Management

**Current:** SQLite file on VM disk  
**Cloud Run:** Ephemeral filesystem (data lost on restart)

**Solutions:**
- Use Cloud SQL for PostgreSQL (persistent state)
- Use Cloud Firestore (NoSQL, serverless)
- Use Cloud Storage (for file-based state)

---

## Deployment Steps for Cloud Run

### Phase 1: Setup Managed Services

```bash
# 1. Create Elastic Cloud deployment
# Visit: https://cloud.elastic.co/
# Select: 4GB RAM, Google Cloud, us-central1

# 2. Create Memorystore Redis
gcloud redis instances create medsearch-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_7_0

# 3. (Optional) Create Cloud SQL
gcloud sql instances create medsearch-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1
```

### Phase 2: Deploy Backend API

```bash
# 1. Build and deploy
gcloud run deploy medsearch-api \
    --source ./backend \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars ELASTICSEARCH_URL=$ELASTIC_URL \
    --set-env-vars REDIS_URL=$REDIS_URL \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10
```

### Phase 3: Deploy Frontend

```bash
# 1. Build and deploy
gcloud run deploy medsearch-frontend \
    --source ./frontend \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars NEXT_PUBLIC_API_URL=$API_URL \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5
```

### Phase 4: Setup Custom Domain (Optional)

```bash
# 1. Map custom domain
gcloud run domain-mappings create \
    --service medsearch-frontend \
    --domain medsearch.example.com \
    --region us-central1
```

---

## Cost Optimization Strategies

### For VM Deployment
1. **Use Preemptible VMs** - 80% cheaper (but can be terminated)
2. **Committed Use Discounts** - 37% discount for 1-year commitment
3. **Right-size VM** - Start with e2-small, scale up as needed
4. **Use Cloud CDN** - Cache static assets
5. **Compress responses** - Reduce egress costs

### For Cloud Run Deployment
1. **Set min-instances=0** - Scale to zero when idle
2. **Optimize container size** - Smaller images = faster cold starts
3. **Use Cloud CDN** - Cache frontend assets
4. **Implement caching** - Reduce database queries
5. **Use Cloud Scheduler** - Keep services warm during business hours

---

## Final Recommendation

### For Hackathon Submission (Current)
**Stick with Compute Engine VM**
- ✅ Already working
- ✅ Simple to demonstrate
- ✅ Lower cost for short-term
- ✅ No migration risk

### For Production/Post-Hackathon
**Migrate to Cloud Run + Managed Services**
- ✅ Better scalability
- ✅ Higher availability
- ✅ Professional architecture
- ✅ Pay-per-use pricing
- ✅ Easier to maintain long-term

### Migration Timeline
1. **Week 1:** Setup Elastic Cloud and Memorystore Redis
2. **Week 2:** Migrate backend API to Cloud Run
3. **Week 3:** Migrate frontend to Cloud Run
4. **Week 4:** Testing, optimization, and cutover

---

## Questions & Answers

**Q: Will Cloud Run work with our Docker Compose setup?**  
A: Not directly. You need to deploy each service separately and replace Elasticsearch/Redis with managed services.

**Q: What about the free tier limits?**  
A: For a demo/MVP, you'll likely stay within free tier (2M requests/month). Production use will exceed it.

**Q: Can we use Cloud Run for Elasticsearch?**  
A: No. Elasticsearch requires persistent storage and stateful operation. Use Elastic Cloud or self-hosted on VM.

**Q: How do we handle WebSocket connections?**  
A: Cloud Run supports WebSockets with 60-minute timeout. Implement heartbeat to keep connections alive.

**Q: What's the best option for cost?**  
A: VM is cheaper for consistent traffic. Cloud Run is cheaper for variable/low traffic.

---

**Prepared by:** Mohan Krishna Alavala  
**Date:** October 2025  
**For:** MedSearch AI - AI Accelerate Hackathon

