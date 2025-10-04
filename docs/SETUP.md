# MedSearch AI - Setup Guide

This guide will help you set up the MedSearch AI project for local development and production deployment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker Desktop** (latest version)
  - Download: https://www.docker.com/products/docker-desktop
  - Ensure Docker Compose is included

- **Node.js 20+** (for local frontend development)
  - Download: https://nodejs.org/
  - Verify: `node --version`

- **Python 3.11+** (for local backend development)
  - Download: https://www.python.org/downloads/
  - Verify: `python --version`

- **Google Cloud CLI** (for deployment)
  - Download: https://cloud.google.com/sdk/docs/install
  - Verify: `gcloud --version`

### Google Cloud Setup

1. **Create a GCP Project**
   ```bash
   gcloud projects create medsearch-ai --name="MedSearch AI"
   gcloud config set project medsearch-ai
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable compute.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

3. **Create Service Account**
   ```bash
   gcloud iam service-accounts create medsearch-sa \
       --display-name="MedSearch Service Account"
   
   gcloud projects add-iam-policy-binding medsearch-ai \
       --member="serviceAccount:medsearch-sa@medsearch-ai.iam.gserviceaccount.com" \
       --role="roles/aiplatform.user"
   
   gcloud iam service-accounts keys create medsearch-key.json \
       --iam-account=medsearch-sa@medsearch-ai.iam.gserviceaccount.com
   ```

4. **Place Service Account Key**
   ```bash
   # Copy to internal_docs (gitignored)
   cp medsearch-key.json internal_docs/
   
   # Or copy directly to backend
   cp medsearch-key.json backend/
   ```

---

## Local Development Setup

### Quick Start (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/mohankrishnaalavala/medsearch.git
   cd medsearch
   ```

2. **Setup environment files**
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   
   # Frontend
   cp frontend/.env.example frontend/.env.local
   ```

3. **Place service account key**
   ```bash
   # If you have it in internal_docs
   cp internal_docs/medsearch-key.json backend/
   ```

4. **Start all services**
   ```bash
   ./scripts/dev-start.sh
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Elasticsearch: http://localhost:9200 (user: elastic, password: changeme)

### Manual Setup

#### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run backend**
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Setup environment**
   ```bash
   cp .env.example .env.local
   ```

3. **Run frontend**
   ```bash
   npm run dev
   ```

#### Infrastructure Services

Start Elasticsearch and Redis:
```bash
docker-compose up elasticsearch redis -d
```

---

## Production Deployment

### Option 1: Automated Deployment (Recommended)

1. **Provision VM**
   ```bash
   ./scripts/provision-vm.sh medsearch-ai us-central1-a
   ```

2. **Setup GitHub Secrets**
   
   Go to your GitHub repository → Settings → Secrets and variables → Actions
   
   Add the following secrets:
   - `GCP_PROJECT_ID`: `medsearch-ai`
   - `GCP_SA_KEY`: Contents of `medsearch-key.json` (base64 encoded)
   
   ```bash
   # Encode service account key
   cat medsearch-key.json | base64
   ```

3. **Create production environment file**
   ```bash
   cp .env.production.example .env.production
   # Edit .env.production with secure values
   ```

4. **Deploy**
   ```bash
   git push origin main
   ```
   
   GitHub Actions will automatically:
   - Build Docker images
   - Push to Google Container Registry
   - Deploy to VM
   - Run health checks

### Option 2: Manual Deployment

See [internal_docs/vm-setup.md](../internal_docs/vm-setup.md) for detailed manual deployment instructions.

---

## Troubleshooting

### Docker Issues

**Problem:** Docker containers won't start
```bash
# Check Docker is running
docker info

# Check logs
docker-compose logs

# Restart Docker Desktop
```

**Problem:** Port already in use
```bash
# Find process using port
lsof -i :8000  # or :3000, :9200

# Kill process
kill -9 <PID>
```

### Backend Issues

**Problem:** Import errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Problem:** Vertex AI authentication errors
```bash
# Check service account key exists
ls -la backend/medsearch-key.json

# Verify GOOGLE_APPLICATION_CREDENTIALS in .env
cat backend/.env | grep GOOGLE_APPLICATION_CREDENTIALS
```

### Frontend Issues

**Problem:** Module not found errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Problem:** Build errors
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

### Elasticsearch Issues

**Problem:** Elasticsearch won't start
```bash
# Check memory limits
docker stats

# Increase Docker memory to at least 4GB in Docker Desktop settings
```

**Problem:** Connection refused
```bash
# Check Elasticsearch is running
docker ps | grep elasticsearch

# Check health
curl -u elastic:changeme http://localhost:9200/_cluster/health
```

### VM Deployment Issues

**Problem:** SSH connection failed
```bash
# Check VM is running
gcloud compute instances list

# Start VM if stopped
gcloud compute instances start medsearch-vm --zone=us-central1-a
```

**Problem:** Deployment failed
```bash
# SSH into VM
gcloud compute ssh medsearch-vm --zone=us-central1-a

# Check logs
cd ~/medsearch
docker-compose -f docker-compose.prod.yml logs
```

---

## Next Steps

After successful setup:

1. **Run tests** to verify everything works:
   ```bash
   ./scripts/test-all.sh
   ```

2. **Proceed to Agent 2** for backend implementation:
   - See `internal_docs/agent_prompts/agent-2-backend.md`

3. **Review documentation**:
   - [Product Requirements](../internal_docs/medsearch-prd.md)
   - [Technical Specification](../internal_docs/medsearch-technical-spec.md)

---

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review logs: `docker-compose logs -f`
- Contact: mohanalavala68@gmail.com

