#!/bin/bash

# Deploy APM and Kibana to Production VM
# Run this script on your production VM

set -e  # Exit on error

echo "=========================================="
echo "MedSearch - Deploy APM & Kibana"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check if we're in the right directory
echo -e "${YELLOW}Step 1: Checking current directory...${NC}"
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found!${NC}"
    echo "Please run this script from the medsearch project directory"
    exit 1
fi
echo -e "${GREEN}✓ Found docker-compose.yml${NC}"
echo ""

# Step 2: Backup current docker-compose.yml
echo -e "${YELLOW}Step 2: Backing up current docker-compose.yml...${NC}"
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✓ Backup created${NC}"
echo ""

# Step 3: Check if updated docker-compose.prod.yml exists
echo -e "${YELLOW}Step 3: Checking for updated docker-compose.prod.yml...${NC}"
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}Error: docker-compose.prod.yml not found!${NC}"
    echo "Please pull the latest code first: git pull origin develop"
    exit 1
fi
echo -e "${GREEN}✓ Found docker-compose.prod.yml${NC}"
echo ""

# Step 4: Copy updated docker-compose
echo -e "${YELLOW}Step 4: Updating docker-compose.yml with APM and Kibana...${NC}"
cp docker-compose.prod.yml docker-compose.yml
echo -e "${GREEN}✓ docker-compose.yml updated${NC}"
echo ""

# Step 5: Check .env file
echo -e "${YELLOW}Step 5: Checking .env file...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env file with required variables"
    exit 1
fi

# Check for required variables
REQUIRED_VARS=("ELASTICSEARCH_PASSWORD" "GOOGLE_CLOUD_PROJECT")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}Error: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    exit 1
fi
echo -e "${GREEN}✓ Required environment variables found${NC}"
echo ""

# Step 6: Add APM variables to .env if not present
echo -e "${YELLOW}Step 6: Checking APM configuration in .env...${NC}"

if ! grep -q "^APM_ENABLED=" .env; then
    echo "" >> .env
    echo "# Elastic APM Configuration" >> .env
    echo "APM_ENABLED=true" >> .env
    echo "APM_SERVER_URL=http://apm-server:8200" >> .env
    echo "APM_SECRET_TOKEN=changeme" >> .env
    echo "APM_SERVICE_NAME=medsearch-api" >> .env
    echo "APM_ENVIRONMENT=production" >> .env
    echo "APM_TRANSACTION_SAMPLE_RATE=0.1" >> .env
    echo "APM_CAPTURE_BODY=off" >> .env
    echo -e "${GREEN}✓ Added APM configuration to .env${NC}"
else
    echo -e "${GREEN}✓ APM configuration already exists in .env${NC}"
    # Update APM_ENABLED to true if it's false
    sed -i 's/^APM_ENABLED=false/APM_ENABLED=true/' .env
fi
echo ""

# Step 7: Add Reranking variables to .env if not present
echo -e "${YELLOW}Step 7: Checking Reranking configuration in .env...${NC}"

if ! grep -q "^VERTEX_AI_RERANK_ENABLED=" .env; then
    echo "" >> .env
    echo "# AI Reranking Configuration" >> .env
    echo "VERTEX_AI_RERANK_ENABLED=true" >> .env
    echo "VERTEX_AI_RERANK_TOP_K=10" >> .env
    echo -e "${GREEN}✓ Added Reranking configuration to .env${NC}"
else
    echo -e "${GREEN}✓ Reranking configuration already exists in .env${NC}"
    # Update VERTEX_AI_RERANK_ENABLED to true if it's false
    sed -i 's/^VERTEX_AI_RERANK_ENABLED=false/VERTEX_AI_RERANK_ENABLED=true/' .env
fi
echo ""

# Step 8: Show what will be deployed
echo -e "${YELLOW}Step 8: Verifying configuration...${NC}"
echo "The following containers will be deployed:"
echo "  - elasticsearch (existing)"
echo "  - redis (existing)"
echo "  - apm-server (NEW)"
echo "  - kibana (NEW)"
echo "  - api (existing, with APM enabled)"
echo "  - frontend (existing)"
echo "  - nginx (existing)"
echo "  - certbot (existing)"
echo ""

# Step 9: Ask for confirmation
echo -e "${YELLOW}Step 9: Ready to deploy${NC}"
read -p "Do you want to proceed with deployment? (yes/no): " -r
echo ""
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 0
fi

# Step 10: Stop existing containers
echo -e "${YELLOW}Step 10: Stopping existing containers...${NC}"
docker-compose down
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Step 11: Pull new images
echo -e "${YELLOW}Step 11: Pulling APM and Kibana images...${NC}"
docker-compose pull apm-server kibana
echo -e "${GREEN}✓ Images pulled${NC}"
echo ""

# Step 12: Start all containers
echo -e "${YELLOW}Step 12: Starting all containers...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# Step 13: Wait for services to be ready
echo -e "${YELLOW}Step 13: Waiting for services to start (30 seconds)...${NC}"
sleep 30
echo -e "${GREEN}✓ Wait complete${NC}"
echo ""

# Step 14: Check container status
echo -e "${YELLOW}Step 14: Checking container status...${NC}"
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep medsearch
echo ""

# Step 15: Verify APM Server
echo -e "${YELLOW}Step 15: Verifying APM Server...${NC}"
if docker ps | grep -q medsearch-apm; then
    echo -e "${GREEN}✓ APM Server container is running${NC}"
    
    # Check APM logs
    echo "APM Server logs (last 10 lines):"
    docker logs medsearch-apm --tail 10
    echo ""
else
    echo -e "${RED}✗ APM Server container is not running${NC}"
    echo "Check logs: docker logs medsearch-apm"
fi
echo ""

# Step 16: Verify Kibana
echo -e "${YELLOW}Step 16: Verifying Kibana...${NC}"
if docker ps | grep -q medsearch-kibana; then
    echo -e "${GREEN}✓ Kibana container is running${NC}"
    
    # Check Kibana logs
    echo "Kibana logs (last 10 lines):"
    docker logs medsearch-kibana --tail 10
    echo ""
else
    echo -e "${RED}✗ Kibana container is not running${NC}"
    echo "Check logs: docker logs medsearch-kibana"
fi
echo ""

# Step 17: Check API APM integration
echo -e "${YELLOW}Step 17: Checking API APM integration...${NC}"
docker logs medsearch-api --tail 50 | grep -i apm || echo "No APM logs found yet (this is normal if API just started)"
echo ""

# Step 18: Show access instructions
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep medsearch
echo ""
echo "Access Information:"
echo "  - Kibana (via SSH tunnel): http://localhost:5601"
echo "  - APM Server: http://localhost:8200"
echo ""
echo "To access Kibana from your local machine:"
echo "  1. Open a new terminal on your LOCAL machine"
echo "  2. Run: gcloud compute ssh medsearch-vm --zone=us-central1-a -- -L 5601:localhost:5601"
echo "  3. Open browser: http://localhost:5601"
echo "  4. Navigate to: Observability → APM"
echo ""
echo "To check logs:"
echo "  - APM Server: docker logs medsearch-apm"
echo "  - Kibana: docker logs medsearch-kibana"
echo "  - API (APM integration): docker logs medsearch-api | grep -i apm"
echo ""
echo "To generate APM data:"
echo "  - Run some searches on your site: https://medsearch.mohankrishna.site/"
echo "  - Wait 1-2 minutes for data to appear in Kibana"
echo ""
echo -e "${GREEN}Done!${NC}"

