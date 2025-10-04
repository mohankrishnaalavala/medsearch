# MedSearch AI - Quick Start Guide

Get MedSearch AI running in 5 minutes! 🚀

## Prerequisites

- Docker Desktop installed and running
- Service account key (`medsearch-key.json`)

## Setup Steps

### 1. Clone and Navigate
```bash
git clone https://github.com/mohankrishnaalavala/medsearch.git
cd medsearch
```

### 2. Place Service Account Key
```bash
# Copy your service account key to backend directory
cp /path/to/medsearch-key.json backend/
```

### 3. Setup Environment Files
```bash
# Backend
cp backend/.env.example backend/.env

# Frontend  
cp frontend/.env.example frontend/.env.local
```

### 4. Start Development Environment
```bash
./scripts/dev-start.sh
```

That's it! 🎉

## Access Your Application

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Elasticsearch:** http://localhost:9200 (user: `elastic`, password: `changeme`)

## Verify Everything Works

### Check Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

### View Logs
```bash
docker-compose logs -f
```

### Run Tests
```bash
# Backend tests
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest

# Frontend tests (after npm install)
cd frontend
npm install
npm run test
```

## Stop Services

```bash
./scripts/dev-stop.sh
# or
docker-compose down
```

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process using port 8000
lsof -i :8000
kill -9 <PID>
```

### Docker Issues
```bash
# Restart Docker Desktop
# Then try again:
./scripts/dev-start.sh
```

### Service Account Key Not Found
```bash
# Make sure the key is in the right place
ls -la backend/medsearch-key.json

# Or copy from internal_docs
cp internal_docs/medsearch-key.json backend/
```

## Next Steps

1. **Review Documentation**
   - [Complete Setup Guide](docs/SETUP.md)
   - [Product Requirements](internal_docs/medsearch-prd.md)
   - [Technical Specification](internal_docs/medsearch-technical-spec.md)

2. **Start Development**
   - See [Agent 2 Prompt](internal_docs/agent_prompts/agent-2-backend.md) for backend development
   - See [Agent 5 Prompt](internal_docs/agent_prompts/agent-5-frontend.md) for frontend development

3. **Deploy to Production**
   - See [VM Setup Guide](internal_docs/vm-setup.md)
   - Run `./scripts/provision-vm.sh medsearch-ai us-central1-a`

## Need Help?

- Check [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions
- Review [Agent 1 Completion Report](docs/AGENT-1-COMPLETION.md)
- Contact: mohanalavala68@gmail.com

---

**Happy Coding! 🎉**

