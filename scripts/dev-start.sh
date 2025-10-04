#!/bin/bash
# Start development environment

set -e

echo "🚀 Starting MedSearch Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Check if .env files exist
if [ ! -f backend/.env ]; then
    echo "⚠️  backend/.env not found, copying from .env.example"
    cp backend/.env.example backend/.env
    echo "📝 Please update backend/.env with your configuration"
fi

if [ ! -f frontend/.env.local ]; then
    echo "⚠️  frontend/.env.local not found, copying from .env.example"
    cp frontend/.env.example frontend/.env.local
fi

# Check if service account key exists
if [ ! -f backend/medsearch-key.json ] && [ ! -f internal_docs/medsearch-key.json ]; then
    echo "❌ Error: medsearch-key.json not found"
    echo "Please place your Google Cloud service account key at:"
    echo "  - backend/medsearch-key.json, or"
    echo "  - internal_docs/medsearch-key.json"
    exit 1
fi

# Copy service account key if needed
if [ -f internal_docs/medsearch-key.json ] && [ ! -f backend/medsearch-key.json ]; then
    cp internal_docs/medsearch-key.json backend/medsearch-key.json
    echo "✅ Copied service account key to backend/"
fi

# Start Docker Compose
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo ""
echo "✅ Development environment started!"
echo ""
echo "📊 Services:"
echo "  Frontend:       http://localhost:3000"
echo "  API:            http://localhost:8000"
echo "  API Docs:       http://localhost:8000/docs"
echo "  Elasticsearch:  http://localhost:9200"
echo "  Redis:          localhost:6379"
echo ""
echo "📝 View logs:"
echo "  docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "  docker-compose down"
echo ""

