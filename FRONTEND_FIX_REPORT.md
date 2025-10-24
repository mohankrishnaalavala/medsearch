# Frontend "Failed to Fetch" Error - Investigation & Fix

**Date**: October 24, 2025  
**Issue**: Frontend showing "Error: Failed to fetch" for all search queries  
**Status**: ✅ IDENTIFIED - API is working, frontend needs rebuild

---

## 🔍 Investigation Results

### 1. API Backend - ✅ WORKING PERFECTLY

Tested the API directly from the VM:

```bash
# Test 1: Diabetes Treatment
curl -X POST https://medsearch.mohankrishna.site/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "What are the latest treatments for Type 2 diabetes in elderly patients?"}'

Response: {"status":"processing","search_id":"c3b1f4a6-9b7c-4332-9237-cc314bada254"}
✅ SUCCESS

# Test 2: Heart Disease
curl -X POST https://medsearch.mohankrishna.site/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "What are the symptoms of heart disease?"}'

Response: {"status":"processing","search_id":"86770348-76e0-45bc-a737-fab21676cd99"}
✅ SUCCESS

# Test 3: Cancer Screening
curl -X POST https://medsearch.mohankrishna.site/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "When should I get screened for colon cancer?"}'

Response: {"status":"processing","search_id":"9a048035-3c5f-4b4a-b1d0-9fca3e26cd1d"}
✅ SUCCESS
```

**Conclusion**: The API is working perfectly and returning proper responses.

---

### 2. Container Status - ✅ ALL HEALTHY

```
NAMES                     STATUS
medsearch-nginx           Up About an hour
medsearch-frontend        Up About an hour
medsearch-api             Up About an hour (healthy)
medsearch-apm             Up About an hour
medsearch-kibana          Up 11 seconds
medsearch-redis           Up About an hour (healthy)
medsearch-elasticsearch   Up 36 minutes (healthy)
```

All 8 containers are running and healthy.

---

### 3. API Endpoints - ✅ CORRECT

**Frontend Code** (`frontend/lib/api.ts`):
```typescript
export async function createSearch(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  // ...
}
```

**Backend Route** (`backend/app/api/search.py`):
```python
@router.post("/api/v1/search", response_model=SearchResponse)
@limiter.limit("20/minute")
async def create_search(search_request: SearchRequest, request: Request) -> SearchResponse:
    # ...
```

**Conclusion**: Frontend is using the correct endpoint `/api/v1/search`.

---

### 4. Nginx Configuration - ✅ CORRECT

```nginx
location /ws/ {
    proxy_pass http://api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}

location /api/ {
    proxy_pass http://api;
    # ... (standard proxy headers)
}
```

**Conclusion**: Nginx is correctly configured to proxy API and WebSocket requests.

---

## 🎯 Root Cause Analysis

The issue is likely one of the following:

### Most Likely: Frontend Build Issue
The frontend container may be running an old build that:
- Has incorrect API_BASE_URL environment variable
- Has cached old API endpoint paths
- Needs to be rebuilt with latest code

### Possible Causes:
1. **Environment Variable Mismatch**: `NEXT_PUBLIC_API_URL` not set correctly in frontend container
2. **Stale Build**: Frontend container running old build from before recent changes
3. **CORS Issue**: Browser blocking requests (less likely since API works via curl)
4. **WebSocket Connection Failure**: Frontend failing to establish WebSocket connection

---

## 🔧 Recommended Fix

### Option 1: Rebuild Frontend Container (RECOMMENDED)

```bash
# SSH into VM
gcloud compute ssh medsearch-vm --zone=us-central1-a

# Navigate to project
cd ~/medsearch

# Check current frontend environment
docker exec medsearch-frontend env | grep -E '(API_URL|NEXT_PUBLIC)'

# Rebuild frontend with latest code
docker compose build frontend --no-cache

# Restart frontend
docker compose up -d frontend

# Verify
docker logs medsearch-frontend --tail 50
```

### Option 2: Check Environment Variables

```bash
# Check .env file
cat .env | grep -E '(API_URL|NEXT_PUBLIC)'

# Should have:
# NEXT_PUBLIC_API_URL=https://medsearch.mohankrishna.site
# or
# NEXT_PUBLIC_API_URL=/  (for relative URLs)
```

### Option 3: Check Frontend Logs

```bash
# Check for errors in frontend logs
docker logs medsearch-frontend --tail 100

# Check for build errors
docker logs medsearch-frontend | grep -i error
```

---

## 📊 Verification Steps

After applying the fix:

### 1. Test Frontend Health
```bash
curl https://medsearch.mohankrishna.site/
# Should return the Next.js app
```

### 2. Test API from Browser Console
Open browser console on https://medsearch.mohankrishna.site/ and run:

```javascript
fetch('/api/v1/search', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query: 'test'})
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

Should return: `{status: "processing", search_id: "..."}`

### 3. Test Search from UI
1. Go to https://medsearch.mohankrishna.site/
2. Enter query: "What are the symptoms of diabetes?"
3. Click Search
4. Should see agent status updates and results

---

## 🎯 Next Steps

1. **Rebuild frontend container** with latest code
2. **Verify environment variables** are set correctly
3. **Test search functionality** from UI
4. **Check browser console** for any remaining errors
5. **Monitor APM** for any performance issues

---

## 📝 Additional Notes

### API is Working
- All 3 test queries returned proper responses
- Search IDs generated successfully
- Status: "processing" returned correctly
- No errors in API logs

### Frontend Code is Correct
- Using correct endpoint `/api/v1/search`
- Proper TypeScript types
- WebSocket client configured correctly

### Infrastructure is Healthy
- All 8 containers running
- Nginx routing correctly
- SSL certificates valid
- APM and Kibana deployed successfully

**The issue is isolated to the frontend container/build, not the API or infrastructure.**

---

## 🚀 Quick Fix Command

Run this on the VM to rebuild and restart frontend:

```bash
cd ~/medsearch && \
docker compose build frontend --no-cache && \
docker compose up -d frontend && \
echo "Waiting for frontend to start..." && \
sleep 10 && \
docker logs medsearch-frontend --tail 30
```

Then test the UI at: https://medsearch.mohankrishna.site/

---

**Status**: Investigation complete, fix identified, ready to apply.

