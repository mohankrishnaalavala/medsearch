#!/bin/bash

# MedSearch AI Deployment Script
# This script deploys the application to Google Cloud VM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GCP_PROJECT="medsearch-ai"
GCP_ZONE="us-central1-a"
VM_NAME="medsearch-vm"
BRANCH="${1:-develop}"

echo -e "${GREEN}=== MedSearch AI Deployment ===${NC}"
echo "Project: $GCP_PROJECT"
echo "Zone: $GCP_ZONE"
echo "VM: $VM_NAME"
echo "Branch: $BRANCH"
echo ""

# Check if gcloud is authenticated
echo -e "${YELLOW}Checking Google Cloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}Error: Not authenticated with Google Cloud${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated${NC}"

# Deploy to VM
echo -e "${YELLOW}Deploying to VM...${NC}"
gcloud compute ssh $VM_NAME \
    --zone=$GCP_ZONE \
    --project=$GCP_PROJECT \
    --command="
        set -e
        
        echo '=== Pulling latest code ==='
        cd medsearch
        git fetch origin
        git checkout $BRANCH
        git pull origin $BRANCH
        
        echo '=== Stopping services ==='
        sudo docker compose down
        
        echo '=== Building containers ==='
        sudo docker compose build
        
        echo '=== Starting services ==='
        sudo docker compose up -d
        
        echo '=== Waiting for services to start ==='
        sleep 60
        
        echo '=== Checking service status ==='
        sudo docker compose ps
        
        echo '=== Testing endpoints ==='
        FRONTEND_STATUS=\$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000)
        API_STATUS=\$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)
        NGINX_STATUS=\$(curl -s -o /dev/null -w '%{http_code}' http://localhost:80)
        
        echo \"Frontend: \$FRONTEND_STATUS\"
        echo \"API: \$API_STATUS\"
        echo \"Nginx: \$NGINX_STATUS\"
        
        if [ \$FRONTEND_STATUS -eq 200 ] && [ \$API_STATUS -eq 200 ] && [ \$NGINX_STATUS -eq 200 ]; then
            echo '✅ All services are healthy'
        else
            echo '❌ Some services are not healthy'
            exit 1
        fi
    "

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Application is accessible at:"
echo "  - VM IP: http://$(gcloud compute instances describe $VM_NAME --zone=$GCP_ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
echo "  - Cloudflare Tunnel: Check /tmp/cloudflared.log on VM for URL"
echo ""
echo "To view logs:"
echo "  gcloud compute ssh $VM_NAME --zone=$GCP_ZONE --command='cd medsearch && sudo docker compose logs -f'"

