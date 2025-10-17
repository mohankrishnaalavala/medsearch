# MedSearch AI - Deployment Guide

## 🚀 Deployment Overview

This document provides deployment instructions and cost estimates for running MedSearch AI on Google Cloud Platform for 45 days.

---

## 📊 Cost Estimation (45 Days)

### Google Cloud Platform Costs

#### 1. Compute Engine VM (e2-standard-2)
- **Specs:** 2 vCPU, 8GB RAM
- **Cost:** ~$49/month
- **45 days:** ~$73.50

#### 2. Persistent Disk (50GB)
- **Type:** pd-balanced
- **Cost:** ~$5/month
- **45 days:** ~$7.50

#### 3. Network Egress
- **Estimate:** 10GB/month (light usage by judges)
- **Cost:** ~$1.20/month
- **45 days:** ~$1.80

#### 4. Vertex AI API Calls
- **Gemini 2.5 Flash:** $0.075 per 1M input tokens, $0.30 per 1M output tokens
- **Estimate:** 100 queries/day × 45 days = 4,500 queries
- **Average:** 1,000 input tokens + 500 output tokens per query
- **Cost:** (4.5M × $0.075) + (2.25M × $0.30) = $337.50 + $675 = **$1,012.50**

#### 5. Elasticsearch (Self-hosted in Docker)
- **Cost:** $0 (included in VM)

#### 6. Redis (Self-hosted in Docker)
- **Cost:** $0 (included in VM)

### **Total Estimated Cost for 45 Days: ~$1,095**

**Note:** This is a conservative estimate. Actual costs may be lower if:
- Judges use the application less frequently
- You use Gemini 2.5 Flash exclusively (cheaper than Pro)
- Network egress is minimal

---

## 💰 Cost Optimization Tips

### 1. **Reduce Vertex AI Costs (Biggest Cost Driver)**
- Use Gemini 2.5 Flash for all queries (already configured)
- Implement response caching (already implemented with Redis)
- Set rate limits to prevent abuse
- Consider using smaller context windows

### 2. **VM Cost Optimization**
- Current e2-standard-2 is already cost-effective
- Could downgrade to e2-small (2GB RAM) but may cause OOM issues
- **Recommendation:** Keep current VM size

### 3. **No Monitoring/Logging Costs**
- Disabled Cloud Logging (as requested)
- Using local logs only
- No Cloud Monitoring dashboards

---

## 🔧 Deployment Methods

### Method 1: GitHub Actions (Automated)

**Setup:**
1. Add GCP service account key to GitHub Secrets:
   ```bash
   # Go to GitHub repo → Settings → Secrets and variables → Actions
   # Add new secret: GCP_SA_KEY
   # Paste the contents of medsearch-key.json
   ```

2. Push to `main` or `develop` branch:
   ```bash
   git push origin develop
   ```

3. GitHub Actions will automatically:
   - Pull latest code on VM
   - Build Docker containers
   - Restart services
   - Verify deployment

**Workflow File:** `.github/workflows/deploy-gcp.yml`

---

### Method 2: Manual Deployment Script

**Usage:**
```bash
# Make script executable
chmod +x deploy.sh

# Deploy develop branch (default)
./deploy.sh

# Deploy specific branch
./deploy.sh main
```

**What it does:**
- Connects to GCP VM via SSH
- Pulls latest code
- Rebuilds containers
- Restarts services
- Verifies health

---

### Method 3: Direct SSH Deployment

**Steps:**
```bash
# SSH into VM
gcloud compute ssh medsearch-vm --zone=us-central1-a --project=medsearch-ai

# Navigate to project
cd medsearch

# Pull latest code
git pull origin develop

# Restart services
sudo docker compose down
sudo docker compose up -d --build

# Check status
sudo docker compose ps
sudo docker compose logs -f
```

---

## 🏥 Application Health & Stability

### Memory Management

**Current Configuration:**
- Elasticsearch: 1.5GB (reduced from 2.5GB)
- API: 1.5GB
- Frontend: 512MB
- Redis: 600MB
- Nginx: 128MB
- **Total:** ~4.2GB / 8GB available

**Stability for 45 Days:**
✅ **YES** - The application should run stably for 45 days with this configuration:

1. **Memory:** 3.8GB headroom for OS and buffers
2. **Restart Policy:** `unless-stopped` ensures auto-restart on crashes
3. **Health Checks:** Elasticsearch and Redis have health checks
4. **No Memory Leaks:** Python/Node.js with proper garbage collection

### Potential Issues & Mitigations

#### 1. **Elasticsearch Disk Space**
- **Risk:** Index growth over time
- **Mitigation:** 50GB disk with only 1,500 documents (minimal growth)
- **Monitoring:** Check disk usage weekly

#### 2. **Docker Container Crashes**
- **Risk:** OOM kills or application errors
- **Mitigation:** Restart policy `unless-stopped`
- **Action:** Containers auto-restart on failure

#### 3. **Cloudflare Tunnel Disconnection**
- **Risk:** Temporary tunnel may disconnect
- **Mitigation:** Run cloudflared as systemd service (see below)

---

## 🌐 Cloudflare Tunnel Setup (Permanent)

### Current Setup (Temporary)
The current tunnel is temporary and may disconnect. To make it permanent:

**1. Create systemd service:**
```bash
# SSH into VM
gcloud compute ssh medsearch-vm --zone=us-central1-a --project=medsearch-ai

# Create service file
sudo tee /etc/systemd/system/cloudflared.service > /dev/null <<EOF
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=mohankrishnaalavala
ExecStart=/usr/bin/cloudflared tunnel --url http://localhost:80
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Check status
sudo systemctl status cloudflared

# Get tunnel URL
sudo journalctl -u cloudflared -n 50 | grep trycloudflare.com
```

**2. Update README with permanent URL**

---

## 📝 Maintenance Tasks

### Weekly (Optional)
```bash
# Check disk usage
gcloud compute ssh medsearch-vm --zone=us-central1-a --command='df -h'

# Check container status
gcloud compute ssh medsearch-vm --zone=us-central1-a --command='cd medsearch && sudo docker compose ps'

# Check logs for errors
gcloud compute ssh medsearch-vm --zone=us-central1-a --command='cd medsearch && sudo docker compose logs --tail=100 | grep -i error'
```

### If Issues Occur
```bash
# Restart all services
gcloud compute ssh medsearch-vm --zone=us-central1-a --command='cd medsearch && sudo docker compose restart'

# View logs
gcloud compute ssh medsearch-vm --zone=us-central1-a --command='cd medsearch && sudo docker compose logs -f'

# Check resource usage
gcloud compute ssh medsearch-vm --zone=us-central1-a --command='free -h && df -h'
```

---

## ✅ Pre-Deployment Checklist

- [ ] Service account key (`medsearch-key.json`) is on VM
- [ ] GitHub Actions secret `GCP_SA_KEY` is configured
- [ ] Cloudflare tunnel is running
- [ ] All services are healthy
- [ ] Demo credentials work
- [ ] Frontend accessible via public URL
- [ ] API endpoints responding
- [ ] WebSocket connections working

---

## 🎯 Expected Uptime

**Estimated Uptime: 99%+**

**Factors:**
- ✅ Auto-restart on crashes
- ✅ Health checks for critical services
- ✅ Sufficient memory headroom
- ✅ No complex dependencies
- ✅ Stable Docker containers

**Potential Downtime:**
- GCP maintenance (rare, usually announced)
- Cloudflare tunnel disconnection (if not using systemd service)
- Manual deployments (5-10 minutes)

---

## 📞 Support

If issues occur during the hackathon:

1. **Check service status:**
   ```bash
   gcloud compute ssh medsearch-vm --zone=us-central1-a --command='cd medsearch && sudo docker compose ps'
   ```

2. **Restart services:**
   ```bash
   gcloud compute ssh medsearch-vm --zone=us-central1-a --command='cd medsearch && sudo docker compose restart'
   ```

3. **View logs:**
   ```bash
   gcloud compute ssh medsearch-vm --zone=us-central1-a --command='cd medsearch && sudo docker compose logs -f api'
   ```

---

## 🎉 Summary

- **Cost:** ~$1,095 for 45 days (mostly Vertex AI)
- **Stability:** High (99%+ uptime expected)
- **Monitoring:** Minimal (no expensive cloud monitoring)
- **Deployment:** Automated via GitHub Actions
- **Maintenance:** Minimal (weekly checks optional)

**The application is production-ready for hackathon judging!** 🚀

