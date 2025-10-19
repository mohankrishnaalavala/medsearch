#!/bin/bash

# MedSearch AI - Complete Deployment and Testing Script
# This script deploys the application to VM and runs comprehensive tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GCP_PROJECT="medsearch-ai"
GCP_ZONE="us-central1-a"
VM_NAME="medsearch-vm"
BRANCH="${1:-develop}"

# Get VM IP
VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$GCP_ZONE --project=$GCP_PROJECT --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       MedSearch AI - Deployment & Testing Suite          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Project: $GCP_PROJECT"
echo "  Zone: $GCP_ZONE"
echo "  VM: $VM_NAME"
echo "  VM IP: $VM_IP"
echo "  Branch: $BRANCH"
echo ""

# Function to print section header
print_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check authentication
print_section "Step 1: Checking Authentication"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "Not authenticated with Google Cloud"
    echo "Please run: gcloud auth login"
    exit 1
fi
print_success "Authenticated with Google Cloud"

# Deploy to VM
print_section "Step 2: Deploying to VM"
print_info "Connecting to VM and deploying application..."

gcloud compute ssh $VM_NAME \
    --zone=$GCP_ZONE \
    --project=$GCP_PROJECT \
    --command="
        set -e
        
        echo '→ Checking if repository exists...'
        if [ ! -d 'medsearch' ]; then
            echo '→ Cloning repository...'
            git clone https://github.com/mohankrishnaalavala/medsearch.git
            cd medsearch
        else
            echo '→ Repository exists, updating...'
            cd medsearch
            git fetch origin
        fi
        
        echo '→ Checking out branch: $BRANCH'
        git checkout $BRANCH
        git pull origin $BRANCH
        
        echo '→ Copying service account key...'
        if [ -f ~/medsearch-key.json ]; then
            cp ~/medsearch-key.json backend/medsearch-key.json
            cp ~/medsearch-key.json internal_docs/medsearch-key.json
        else
            echo '⚠ Warning: medsearch-key.json not found in home directory'
        fi
        
        echo '→ Stopping existing services...'
        sudo docker compose down || true
        
        echo '→ Cleaning up old containers and images...'
        sudo docker system prune -f
        
        echo '→ Building containers...'
        sudo docker compose build --no-cache
        
        echo '→ Starting services...'
        sudo docker compose up -d
        
        echo '→ Waiting for services to initialize (90 seconds)...'
        sleep 90
        
        echo '→ Checking service status...'
        sudo docker compose ps
    "

print_success "Deployment completed"

# Wait for services to be fully ready
print_section "Step 3: Waiting for Services"
print_info "Waiting additional 30 seconds for services to be fully ready..."
sleep 30
print_success "Services should be ready"

# Test backend API
print_section "Step 4: Testing Backend API"

print_info "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://$VM_IP/health || echo "000")
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HEALTH_CODE" = "200" ]; then
    print_success "Health endpoint: OK (200)"
    echo "$HEALTH_BODY" | jq '.' 2>/dev/null || echo "$HEALTH_BODY"
else
    print_error "Health endpoint: FAILED ($HEALTH_CODE)"
    echo "$HEALTH_BODY"
fi

print_info "Testing API docs endpoint..."
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$VM_IP/docs || echo "000")
if [ "$DOCS_CODE" = "200" ]; then
    print_success "API docs endpoint: OK (200)"
else
    print_error "API docs endpoint: FAILED ($DOCS_CODE)"
fi

# Test frontend
print_section "Step 5: Testing Frontend"

print_info "Testing frontend homepage..."
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$VM_IP/ || echo "000")
if [ "$FRONTEND_CODE" = "200" ]; then
    print_success "Frontend homepage: OK (200)"
else
    print_error "Frontend homepage: FAILED ($FRONTEND_CODE)"
fi

# Test search functionality
print_section "Step 6: Testing Search Functionality"

print_info "Creating test search query..."
SEARCH_RESPONSE=$(curl -s -X POST http://$VM_IP/api/v1/search \
    -H "Content-Type: application/json" \
    -d '{
        "query": "Type 2 diabetes treatment in elderly patients",
        "max_results": 5
    }' || echo '{"error": "request failed"}')

if echo "$SEARCH_RESPONSE" | jq -e '.search_id' > /dev/null 2>&1; then
    SEARCH_ID=$(echo "$SEARCH_RESPONSE" | jq -r '.search_id')
    print_success "Search created successfully"
    echo "  Search ID: $SEARCH_ID"
else
    print_error "Search creation failed"
    echo "$SEARCH_RESPONSE" | jq '.' 2>/dev/null || echo "$SEARCH_RESPONSE"
fi

# Check Docker containers
print_section "Step 7: Checking Docker Containers"

print_info "Fetching container status..."
CONTAINER_STATUS=$(gcloud compute ssh $VM_NAME \
    --zone=$GCP_ZONE \
    --project=$GCP_PROJECT \
    --command="cd medsearch && sudo docker compose ps --format json" 2>/dev/null || echo '[]')

echo "$CONTAINER_STATUS" | jq -r '.[] | "  \(.Name): \(.State) (\(.Status))"' 2>/dev/null || echo "$CONTAINER_STATUS"

# Check logs for errors
print_section "Step 8: Checking Logs for Errors"

print_info "Checking backend logs for errors..."
BACKEND_ERRORS=$(gcloud compute ssh $VM_NAME \
    --zone=$GCP_ZONE \
    --project=$GCP_PROJECT \
    --command="cd medsearch && sudo docker compose logs api --tail=50 | grep -i error || echo 'No errors found'" 2>/dev/null)

if echo "$BACKEND_ERRORS" | grep -q "No errors found"; then
    print_success "No errors in backend logs"
else
    print_warning "Found errors in backend logs:"
    echo "$BACKEND_ERRORS"
fi

# Performance test
print_section "Step 9: Performance Testing"

print_info "Testing response time..."
START_TIME=$(date +%s%3N)
curl -s -o /dev/null http://$VM_IP/health
END_TIME=$(date +%s%3N)
RESPONSE_TIME=$((END_TIME - START_TIME))

if [ $RESPONSE_TIME -lt 1000 ]; then
    print_success "Response time: ${RESPONSE_TIME}ms (Excellent)"
elif [ $RESPONSE_TIME -lt 2000 ]; then
    print_success "Response time: ${RESPONSE_TIME}ms (Good)"
else
    print_warning "Response time: ${RESPONSE_TIME}ms (Needs optimization)"
fi

# Final summary
print_section "Deployment Summary"

echo -e "${GREEN}Application deployed successfully!${NC}"
echo ""
echo "Access URLs:"
echo "  Frontend:  http://$VM_IP"
echo "  API:       http://$VM_IP/api/v1"
echo "  API Docs:  http://$VM_IP/docs"
echo "  Health:    http://$VM_IP/health"
echo ""
echo "Next Steps:"
echo "  1. Open http://$VM_IP in your browser"
echo "  2. Test the chat interface with medical queries"
echo "  3. Verify Pillar 3 features (citations, conflicts, confidence)"
echo "  4. Verify Pillar 4 features (badges, filters, streaming, accessibility)"
echo ""
echo "To view logs:"
echo "  gcloud compute ssh $VM_NAME --zone=$GCP_ZONE --command='cd medsearch && sudo docker compose logs -f'"
echo ""
echo "To restart services:"
echo "  gcloud compute ssh $VM_NAME --zone=$GCP_ZONE --command='cd medsearch && sudo docker compose restart'"
echo ""

print_success "Deployment and testing complete!"

