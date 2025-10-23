# Production Deployment Guide - Enable APM & Kibana

## Current Issue
Your production deployment (`internal_docs/docker-compose.prod.yml`) was missing APM Server and Kibana containers. This has been fixed.

## Step 1: Update Production Docker Compose

The `internal_docs/docker-compose.prod.yml` has been updated to include:
- ✅ APM Server (port 8200)
- ✅ Kibana (port 5601)
- ✅ APM environment variables in API service
- ✅ Reranking environment variables

## Step 2: Deploy to Production VM

### SSH into your VM
```bash
gcloud compute ssh medsearch-vm --zone=us-central1-a
# OR
ssh your-vm-user@107.178.215.243
```

### Navigate to project directory
```bash
cd /path/to/medsearch
```

### Pull latest code
```bash
git pull origin develop
```

### Copy production docker-compose
```bash
cp internal_docs/docker-compose.prod.yml docker-compose.yml
```

### Create/Update .env file
```bash
nano .env
```

Add these variables:
```bash
# Elasticsearch
ELASTICSEARCH_PASSWORD=your-secure-password

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
PUBMED_API_KEY=your-pubmed-key
FDA_API_KEY=your-fda-key

# Elastic APM (ENABLE THIS)
APM_ENABLED=true
APM_SERVER_URL=http://apm-server:8200
APM_SECRET_TOKEN=your-secret-token-here
APM_SERVICE_NAME=medsearch-api
APM_ENVIRONMENT=production
APM_TRANSACTION_SAMPLE_RATE=0.1
APM_CAPTURE_BODY=off

# AI Reranking (ENABLE THIS)
VERTEX_AI_RERANK_ENABLED=true
VERTEX_AI_RERANK_TOP_K=10
```

### Stop existing containers
```bash
docker-compose down
```

### Start with new configuration
```bash
docker-compose up -d
```

### Verify all containers are running
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

You should see:
- medsearch-elasticsearch
- medsearch-redis
- medsearch-apm
- medsearch-kibana
- medsearch-api
- medsearch-frontend
- medsearch-nginx
- medsearch-certbot

### Check APM Server logs
```bash
docker logs medsearch-apm --tail 50
```

Look for: `"Listening on: 0.0.0.0:8200"`

### Check Kibana logs
```bash
docker logs medsearch-kibana --tail 50
```

Look for: `"http server running at http://0.0.0.0:5601"`

## Step 3: Configure Firewall for Kibana Access

### Option A: SSH Tunnel (Recommended - Secure)
From your local machine:
```bash
gcloud compute ssh medsearch-vm --zone=us-central1-a -- -L 5601:localhost:5601
```

Then access Kibana at: `http://localhost:5601`

### Option B: Open Firewall (Less Secure - Use with caution)
```bash
# On VM
sudo ufw allow 5601/tcp
sudo ufw status

# OR using gcloud
gcloud compute firewall-rules create allow-kibana \
  --allow tcp:5601 \
  --source-ranges YOUR_IP_ADDRESS/32 \
  --target-tags medsearch-vm
```

Then access Kibana at: `http://107.178.215.243:5601`

**Security Note**: Only allow your IP address, not 0.0.0.0/0

## Step 4: Access Kibana and Setup APM

### Access Kibana
1. Open browser: `http://localhost:5601` (if using SSH tunnel)
2. Login with Elasticsearch credentials (if security enabled)
3. Navigate to: **Observability → APM**

### First Time Setup
1. Click "Add APM integration"
2. Select "APM Server" (already running)
3. Configure agent (already done in your API)
4. Click "Check APM Server status" - should show green

### Generate Some Traffic
Run a few queries on your live site to generate APM data:
```bash
# From your local machine
curl -X POST https://medsearch.mohankrishna.site/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes treatment"}'
```

### View APM Data
1. Go to: **Observability → APM → Services**
2. Click on "medsearch-api"
3. You should see:
   - Transaction timeline
   - Response times
   - Error rates
   - Service map

## Step 5: Verify Redis Cache

### Check Redis is working
```bash
docker exec -it medsearch-redis redis-cli

# Inside Redis CLI
INFO stats
DBSIZE
KEYS *embedding*
exit
```

### Expected output
```
# Stats
total_commands_processed:1234
keyspace_hits:567
keyspace_misses:123

# DBSIZE
(integer) 45

# KEYS
1) "embedding:hash:abc123"
2) "search:cache:xyz789"
```

## Step 6: Test Production Features

### Test APM Monitoring
```bash
# Check API logs for APM
docker logs medsearch-api --tail 100 | grep -i apm
```

Should see: `"Elastic APM initialized"`

### Test Reranking
```bash
# Check API logs for reranking
docker logs medsearch-api --tail 100 | grep -i rerank
```

Should see: `"Reranking enabled"` or reranking activity

### Test Graceful Degradation
```bash
# Stop Elasticsearch temporarily
docker stop medsearch-elasticsearch

# API should still respond (with fallback data)
curl https://medsearch.mohankrishna.site/api/health

# Restart Elasticsearch
docker start medsearch-elasticsearch
```

## Step 7: Demo Preparation

### For Demo - What to Show

**Option 1: Kibana APM Dashboard (BEST)**
1. SSH tunnel to Kibana before demo
2. Open `http://localhost:5601` in browser tab
3. Navigate to APM → Services → medsearch-api
4. During demo, switch to this tab and show:
   - Transaction timeline
   - Response times
   - Service dependencies

**Option 2: Terminal Commands (GOOD)**
```bash
# Show running containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Show Redis cache
docker exec medsearch-redis redis-cli DBSIZE

# Show resource usage
docker stats --no-stream | head -6

# Show recent API activity
docker logs medsearch-api --tail 20 | grep -i "INFO"
```

**Option 3: Screenshots (BACKUP)**
If live demo fails, have screenshots ready of:
- Kibana APM dashboard
- Docker containers running
- Redis cache stats

## Troubleshooting

### Kibana won't start
```bash
# Check logs
docker logs medsearch-kibana

# Common issue: Elasticsearch not ready
# Wait 30 seconds and check again
docker restart medsearch-kibana
```

### APM Server won't start
```bash
# Check logs
docker logs medsearch-apm

# Common issue: Elasticsearch connection
# Verify ES is running
docker ps | grep elasticsearch

# Check APM can reach ES
docker exec medsearch-apm curl http://elasticsearch:9200
```

### Kibana connection timeout
```bash
# Check if Kibana is listening
docker exec medsearch-kibana netstat -tlnp | grep 5601

# Check firewall
sudo ufw status

# Use SSH tunnel instead
gcloud compute ssh medsearch-vm --zone=us-central1-a -- -L 5601:localhost:5601
```

### APM not showing data
```bash
# Verify APM is enabled in API
docker exec medsearch-api env | grep APM

# Check API logs for APM initialization
docker logs medsearch-api | grep -i apm

# Generate test traffic
curl -X POST https://medsearch.mohankrishna.site/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

## Quick Commands Reference

```bash
# SSH with Kibana tunnel
gcloud compute ssh medsearch-vm --zone=us-central1-a -- -L 5601:localhost:5601

# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check APM status
docker logs medsearch-apm --tail 20

# Check Kibana status
docker logs medsearch-kibana --tail 20

# Check Redis cache
docker exec medsearch-redis redis-cli DBSIZE

# Check API APM integration
docker logs medsearch-api | grep -i apm

# Restart all services
docker-compose restart

# View resource usage
docker stats --no-stream
```

## Summary

After following these steps, you will have:
- ✅ APM Server running and collecting data
- ✅ Kibana accessible for visualization
- ✅ Redis cache working
- ✅ Reranking enabled
- ✅ Production-ready monitoring

**For Demo**: Use SSH tunnel to access Kibana, show APM dashboard with real transaction data.

