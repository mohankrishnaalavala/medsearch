# Deploy APM & Kibana NOW - Quick Guide

## You're Currently On Production VM - Follow These Steps

### Step 1: Navigate to Project Directory
```bash
cd /path/to/medsearch
# Or wherever your docker-compose.yml is located
pwd  # Verify you're in the right directory
```

### Step 2: Pull Latest Code
```bash
git pull origin develop
```

### Step 3: Backup Current docker-compose.yml
```bash
cp docker-compose.yml docker-compose.yml.backup
```

### Step 4: Use Updated docker-compose with APM & Kibana
```bash
cp internal_docs/docker-compose.prod.yml docker-compose.yml
```

### Step 5: Update .env File

Open .env file:
```bash
nano .env
```

Add these lines at the end (if not already present):
```bash
# Elastic APM Configuration
APM_ENABLED=true
APM_SERVER_URL=http://apm-server:8200
APM_SECRET_TOKEN=changeme
APM_SERVICE_NAME=medsearch-api
APM_ENVIRONMENT=production
APM_TRANSACTION_SAMPLE_RATE=0.1
APM_CAPTURE_BODY=off

# AI Reranking Configuration
VERTEX_AI_RERANK_ENABLED=true
VERTEX_AI_RERANK_TOP_K=10
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 6: Verify .env Has Required Variables

Check that these exist in .env:
```bash
grep "ELASTICSEARCH_PASSWORD" .env
grep "GOOGLE_CLOUD_PROJECT" .env
grep "APM_ENABLED" .env
```

All three should show values. If not, add them.

### Step 7: Stop Current Containers
```bash
docker-compose down
```

### Step 8: Pull APM and Kibana Images
```bash
docker-compose pull apm-server kibana
```

### Step 9: Start All Containers
```bash
docker-compose up -d
```

### Step 10: Wait for Services to Start
```bash
# Wait 30 seconds for services to initialize
sleep 30
```

### Step 11: Check Container Status
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

You should see:
- ✅ medsearch-elasticsearch
- ✅ medsearch-redis
- ✅ medsearch-apm (NEW)
- ✅ medsearch-kibana (NEW)
- ✅ medsearch-api
- ✅ medsearch-frontend
- ✅ medsearch-nginx
- ✅ medsearch-certbot

### Step 12: Verify APM Server
```bash
docker logs medsearch-apm --tail 20
```

Look for: `"Listening on: 0.0.0.0:8200"`

### Step 13: Verify Kibana
```bash
docker logs medsearch-kibana --tail 20
```

Look for: `"http server running at http://0.0.0.0:5601"`

### Step 14: Check API APM Integration
```bash
docker logs medsearch-api --tail 50 | grep -i apm
```

Look for: `"Elastic APM initialized"` or similar

### Step 15: Test APM Server Endpoint
```bash
curl http://localhost:8200
```

Should return: `{"build_date":"...","build_sha":"...","version":"8.15.1"}`

### Step 16: Test Kibana Endpoint
```bash
curl http://localhost:5601/api/status
```

Should return JSON with status information

---

## Access Kibana from Your Local Machine

### Option 1: SSH Tunnel (Recommended)

**On your LOCAL machine** (not the VM), open a new terminal:
```bash
gcloud compute ssh medsearch-vm --zone=us-central1-a -- -L 5601:localhost:5601
```

Keep this terminal open. Then open browser: `http://localhost:5601`

### Option 2: Open Firewall (Less Secure)

**On the VM**:
```bash
sudo ufw allow 5601/tcp
sudo ufw status
```

Then access: `http://107.178.215.243:5601`

**Note**: This exposes Kibana to the internet. Use Option 1 (SSH tunnel) for better security.

---

## Navigate to APM in Kibana

1. Open Kibana: `http://localhost:5601` (via SSH tunnel)
2. Click on hamburger menu (☰) in top-left
3. Go to: **Observability** → **APM**
4. You should see "APM Server" status
5. Click "Check APM Server status" - should show green ✓

---

## Generate APM Data

Run some searches on your live site to generate APM data:

**From your local machine**:
```bash
# Test search 1
curl -X POST https://medsearch.mohankrishna.site/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes treatment"}'

# Test search 2
curl -X POST https://medsearch.mohankrishna.site/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "cancer immunotherapy"}'

# Test search 3
curl -X POST https://medsearch.mohankrishna.site/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "alzheimer disease"}'
```

Wait 1-2 minutes, then refresh Kibana APM page. You should see:
- Transaction timeline
- Response times
- Service map
- medsearch-api service

---

## Troubleshooting

### APM Container Not Starting

Check logs:
```bash
docker logs medsearch-apm
```

Common issues:
- Elasticsearch not ready → Wait 30 seconds and check again
- Wrong password → Check ELASTICSEARCH_PASSWORD in .env

Restart APM:
```bash
docker-compose restart apm-server
```

### Kibana Container Not Starting

Check logs:
```bash
docker logs medsearch-kibana
```

Common issues:
- Elasticsearch not ready → Wait 60 seconds (Kibana takes time)
- Wrong password → Check ELASTICSEARCH_PASSWORD in .env

Restart Kibana:
```bash
docker-compose restart kibana
```

### Kibana Shows "Kibana server is not ready yet"

This is normal. Kibana takes 1-2 minutes to start. Wait and refresh.

### APM Not Showing Data

1. Check API logs:
```bash
docker logs medsearch-api | grep -i apm
```

2. Verify APM_ENABLED=true in .env:
```bash
grep APM_ENABLED .env
```

3. Restart API:
```bash
docker-compose restart api
```

4. Generate test traffic (see "Generate APM Data" above)

5. Wait 1-2 minutes for data to appear

### Can't Access Kibana via SSH Tunnel

1. Verify tunnel is running:
```bash
# On local machine
ps aux | grep "5601:localhost:5601"
```

2. Try explicit zone:
```bash
gcloud compute ssh medsearch-vm --zone=us-central1-a -- -L 5601:localhost:5601
```

3. Try with IP:
```bash
ssh -L 5601:localhost:5601 your-user@107.178.215.243
```

---

## Quick Verification Commands

Run these to verify everything is working:

```bash
# 1. Check all containers running
docker ps --format "table {{.Names}}\t{{.Status}}" | grep medsearch

# 2. Check APM Server
curl http://localhost:8200

# 3. Check Kibana
curl http://localhost:5601/api/status

# 4. Check Redis cache
docker exec medsearch-redis redis-cli DBSIZE

# 5. Check Elasticsearch
curl -u elastic:YOUR_PASSWORD http://localhost:9200/_cluster/health

# 6. Check resource usage
docker stats --no-stream | head -8
```

---

## Summary

After following these steps, you should have:
- ✅ APM Server running on port 8200
- ✅ Kibana running on port 5601
- ✅ API sending APM data
- ✅ Kibana accessible via SSH tunnel
- ✅ APM dashboard showing transaction data

**For Demo**: Use SSH tunnel to access Kibana, show APM dashboard with real monitoring data!

