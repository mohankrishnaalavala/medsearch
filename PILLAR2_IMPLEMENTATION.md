# Pillar 2 Implementation Summary

## Google Cloud Depth (Multi-Partner Spirit)

This document summarizes the implementation of Pillar 2 workstreams for the MedSearch AI project.

## Implemented Workstreams

### 1. Vertex AI Integration Depth

#### Embeddings
- **Model**: `text-embedding-004` (768 dimensions)
- **Usage**: Per-call embedding generation for semantic search
- **Integration**: Fully integrated across backend and data ingestion pipelines
- **Caching**: Redis-based caching to minimize API calls and costs

#### Reranker (Optional)
- **Implementation**: Gemini Flash-based per-call reranker
- **Cost Control**: 
  - Disabled by default (`VERTEX_AI_RERANK_ENABLED=false`)
  - Truncates content to ~600 chars per item
  - Limits to top-k candidates (default: 10)
  - Temperature 0.0 for deterministic results
  - JSON-only responses to minimize tokens
- **Integration**: Integrated into research, clinical, and drug agents
- **Fallback**: Gracefully falls back to original ranking on errors

**Why Gemini Flash?**
- Most cost-effective option for this project
- No dedicated Vertex AI deployment required (strictly per-call)
- Single API call per agent invocation
- Suitable for production with proper cost controls

**Configuration**:
```bash
# Enable reranker
VERTEX_AI_RERANK_ENABLED=true
VERTEX_AI_RERANK_TOP_K=10
```

### 2. Secret Manager Integration

#### Implementation
- **Lazy Loading**: Secret Manager client loaded only when configured
- **Automatic Service Account Detection**: Detects SA JSON keys and writes to `/tmp/medsearch-sa.json` with 0600 permissions
- **Environment Variable Injection**: Automatically sets `GOOGLE_APPLICATION_CREDENTIALS`
- **Fallback Support**: Falls back to dotenv-style or JSON key-value pairs for other secrets
- **No Hard Dependency**: Works without Secret Manager when not configured

#### IAM Least-Privilege
- **Runtime Permission**: `roles/secretmanager.secretAccessor` on specific secret only
- **Setup Permission**: Admin needs `roles/secretmanager.admin` or equivalent for one-time setup
- **Service Account**: `medsearch-sa@medsearch-ai.iam.gserviceaccount.com` granted accessor role

#### Setup Process

1. **Enable Secret Manager API**:
```bash
gcloud services enable secretmanager.googleapis.com --project=medsearch-ai
```

2. **Create Secret and Upload SA Key**:
```bash
gcloud secrets create medsearch-sa-key \
  --replication-policy="automatic" \
  --project=medsearch-ai

gcloud secrets versions add medsearch-sa-key \
  --data-file=internal_docs/medsearch-key.json \
  --project=medsearch-ai
```

3. **Grant IAM Permission**:
```bash
gcloud secrets add-iam-policy-binding medsearch-sa-key \
  --member="serviceAccount:medsearch-sa@medsearch-ai.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=medsearch-ai
```

4. **Configure Application**:
```bash
# In backend/.env
SECRET_MANAGER_SECRET_NAME=medsearch-sa-key
SECRET_MANAGER_SECRET_VERSION=latest
GOOGLE_CLOUD_PROJECT=medsearch-ai
```

#### Helper Script
A setup script is provided at `backend/scripts/secret_manager_setup.py`:
```bash
python backend/scripts/secret_manager_setup.py \
  --project medsearch-ai \
  --secret medsearch-sa-key \
  --key-file internal_docs/medsearch-key.json
```

## Files Modified

### Core Configuration
- `backend/app/core/config.py`: Added Secret Manager loader and reranker toggles
- `backend/.env`: Configured Secret Manager and reranker settings

### Services
- `backend/app/services/vertex_ai_service.py`: Added `rerank_results()` method
- `backend/app/main.py`: Made Elasticsearch/Redis non-blocking in dev mode

### Agents
- `backend/app/agents/research_agent.py`: Integrated optional reranking
- `backend/app/agents/clinical_agent.py`: Integrated optional reranking
- `backend/app/agents/drug_agent.py`: Integrated optional reranking

### Database
- `backend/app/database/sqlite.py`: Added lazy initialization for tests

### Health Check
- `backend/app/api/health.py`: Made service failures non-critical in dev mode

### Tests
- `backend/tests/test_config.py`: Updated embedding model assertion
- `backend/test_queries.py`: Added integration test script

### Scripts
- `backend/scripts/secret_manager_setup.py`: One-time Secret Manager setup helper

### Dependencies
- `backend/requirements.txt`: Added `google-cloud-secret-manager==2.20.2`

## Test Results

### Unit Tests
```
49 passed, 6 warnings in 3.92s
```

### Integration Tests
```
✓ PASS: Health Endpoint
✓ PASS: Secret Manager
✓ PASS: Vertex AI SDK

Overall: ✓ ALL TESTS PASSED
```

### Vertex AI Verification
- ✓ Chat model (gemini-2.5-flash) working
- ✓ Embedding model (text-embedding-004) working
- ✓ Embedding dimension: 768
- ✓ Health endpoint reports Vertex AI as "up"

## Cost Considerations

### Embeddings
- Per-call usage only
- Redis caching reduces redundant API calls
- No standing deployments

### Reranker
- **Disabled by default** to avoid unexpected costs
- When enabled:
  - Single Gemini Flash call per agent
  - Content truncated to ~600 chars/item
  - Limited to top-k candidates (default: 10)
  - Estimated cost: ~$0.0001 per search query

### Secret Manager
- Free tier: 6 active secret versions
- Access operations: $0.03 per 10,000 operations
- Minimal cost for this use case

## Security Best Practices

1. **Credentials Not in Code**: Service account key stored in Secret Manager
2. **Least Privilege**: Runtime SA only has `secretAccessor` role on one secret
3. **Secure File Permissions**: Temp credentials file created with 0600 permissions
4. **Rotation Ready**: Secret Manager supports versioning for key rotation
5. **Environment-Specific**: Dev mode allows local file fallback

## Next Steps (Optional)

1. **Remove Local Key File**: After confirming Secret Manager works in production, remove `internal_docs/medsearch-key.json` from repository
2. **Key Rotation**: Implement periodic service account key rotation via Secret Manager versions
3. **Native Reranker**: If Google releases a dedicated Vertex AI Reranker model in your region, swap the Gemini-based implementation
4. **Monitoring**: Add Cloud Monitoring alerts for Secret Manager access failures
5. **Multi-Environment**: Create separate secrets for dev/staging/prod environments

## Deployment Notes

### Local Development
- Can use local SA key file via `GOOGLE_APPLICATION_CREDENTIALS`
- Secret Manager optional for local dev

### Cloud Run / GKE / Compute Engine
- Set environment variables:
  ```
  SECRET_MANAGER_SECRET_NAME=medsearch-sa-key
  SECRET_MANAGER_SECRET_VERSION=latest
  GOOGLE_CLOUD_PROJECT=medsearch-ai
  ```
- Ensure runtime service account has `secretAccessor` role
- Application will automatically load credentials from Secret Manager on startup

### Cost Control
- Keep `VERTEX_AI_RERANK_ENABLED=false` in production until cost analysis is complete
- Monitor Vertex AI usage via Cloud Console
- Set budget alerts for Vertex AI API usage

## Conclusion

Both Pillar 2 workstreams have been successfully implemented:
1. ✅ Vertex AI integration depth (embeddings + optional reranker)
2. ✅ Secret Manager with IAM least-privilege

The implementation follows Google Cloud best practices, maintains cost control, and provides a secure, scalable foundation for the MedSearch AI application.

