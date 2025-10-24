#!/bin/bash
set -e

echo "=== MedSearch APM & Kibana Deployment ==="
echo ""

# Navigate to project directory
cd ~/medsearch || cd /home/*/medsearch || { echo "Error: medsearch directory not found"; exit 1; }

echo "Current directory: $(pwd)"
echo ""

# Pull latest code
echo "Pulling latest code..."
git pull origin develop || echo "Git pull failed, continuing with existing code"
echo ""

# Backup current docker-compose
echo "Backing up docker-compose.yml..."
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S) || true
echo ""

# Copy updated docker-compose
echo "Updating docker-compose.yml..."
if [ -f "docker-compose.prod.yml" ]; then
    cp docker-compose.prod.yml docker-compose.yml
    echo "✓ docker-compose.yml updated"
else
    echo "Error: docker-compose.prod.yml not found"
    exit 1
fi
echo ""

# Update .env file
echo "Updating .env file..."
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Add APM configuration if not present
if ! grep -q "^APM_ENABLED=" .env; then
    cat >> .env << 'EOF'

# Elastic APM Configuration
APM_ENABLED=true
APM_SERVER_URL=http://apm-server:8200
APM_SECRET_TOKEN=changeme
APM_SERVICE_NAME=medsearch-api
APM_ENVIRONMENT=production
APM_TRANSACTION_SAMPLE_RATE=0.1
APM_CAPTURE_BODY=off
EOF
    echo "✓ Added APM configuration"
else
    # Update APM_ENABLED to true
    sed -i 's/^APM_ENABLED=false/APM_ENABLED=true/' .env
    echo "✓ APM configuration exists, enabled APM"
fi

# Add Reranking configuration if not present
if ! grep -q "^VERTEX_AI_RERANK_ENABLED=" .env; then
    cat >> .env << 'EOF'

# AI Reranking Configuration
VERTEX_AI_RERANK_ENABLED=true
VERTEX_AI_RERANK_TOP_K=10
EOF
    echo "✓ Added Reranking configuration"
else
    sed -i 's/^VERTEX_AI_RERANK_ENABLED=false/VERTEX_AI_RERANK_ENABLED=true/' .env
    echo "✓ Reranking configuration exists, enabled reranking"
fi
echo ""

# Stop containers
echo "Stopping containers..."
docker-compose down
echo "✓ Containers stopped"
echo ""

# Pull images
echo "Pulling APM and Kibana images..."
docker-compose pull apm-server kibana
echo "✓ Images pulled"
echo ""

# Start containers
echo "Starting all containers..."
docker-compose up -d
echo "✓ Containers started"
echo ""

# Wait for services
echo "Waiting for services to start (30 seconds)..."
sleep 30
echo ""

# Show container status
echo "=== Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Check APM
echo "=== APM Server Status ==="
if docker ps | grep -q medsearch-apm; then
    echo "✓ APM container is running"
    echo ""
    echo "APM Server logs (last 15 lines):"
    docker logs medsearch-apm --tail 15
else
    echo "✗ APM container not running"
    docker logs medsearch-apm --tail 20 || true
fi
echo ""

# Check Kibana
echo "=== Kibana Status ==="
if docker ps | grep -q medsearch-kibana; then
    echo "✓ Kibana container is running"
    echo ""
    echo "Kibana logs (last 15 lines):"
    docker logs medsearch-kibana --tail 15
else
    echo "✗ Kibana container not running"
    docker logs medsearch-kibana --tail 20 || true
fi
echo ""

# Test endpoints
echo "=== Testing Endpoints ==="
echo "APM Server:"
curl -s http://localhost:8200 | head -5 || echo "APM Server not responding yet"
echo ""
echo ""
echo "Kibana:"
curl -s http://localhost:5601/api/status | head -5 || echo "Kibana not responding yet (this is normal, takes 1-2 minutes)"
echo ""

echo "=== Deployment Complete ==="
echo ""
echo "Access Kibana via SSH tunnel from your local machine:"
echo "  gcloud compute ssh medsearch-vm --zone=us-central1-a -- -L 5601:localhost:5601"
echo ""
echo "Then open: http://localhost:5601"

