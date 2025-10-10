#!/bin/bash
# Verify MedSearch project setup

set -e

echo "========================================="
echo "MedSearch Setup Verification"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ (missing)"
        return 1
    fi
}

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not installed"
        return 1
    fi
}

# Track errors
ERRORS=0

# Check prerequisites
echo "Checking Prerequisites..."
check_command docker || ((ERRORS++))

# Check docker-compose (can be standalone or plugin)
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} docker-compose installed"
else
    echo -e "${RED}✗${NC} docker-compose not installed"
    ((ERRORS++))
fi

check_command node || ((ERRORS++))
check_command python3 || ((ERRORS++))
echo ""

# Check project structure
echo "Checking Project Structure..."
check_dir backend || ((ERRORS++))
check_dir backend/app || ((ERRORS++))
check_dir backend/tests || ((ERRORS++))
check_dir frontend || ((ERRORS++))
check_dir frontend/app || ((ERRORS++))
check_dir frontend/lib || ((ERRORS++))
check_dir scripts || ((ERRORS++))
check_dir docs || ((ERRORS++))
echo ""

# Check configuration files
echo "Checking Configuration Files..."
check_file backend/requirements.txt || ((ERRORS++))
check_file backend/pyproject.toml || ((ERRORS++))
check_file backend/Dockerfile || ((ERRORS++))
check_file backend/.env.example || ((ERRORS++))
check_file frontend/package.json || ((ERRORS++))
check_file frontend/tsconfig.json || ((ERRORS++))
check_file frontend/Dockerfile || ((ERRORS++))
check_file frontend/.env.example || ((ERRORS++))
check_file docker-compose.yml || ((ERRORS++))
check_file docker-compose.prod.yml || ((ERRORS++))
check_file nginx.conf || ((ERRORS++))
echo ""

# Check scripts
echo "Checking Scripts..."
check_file scripts/provision-vm.sh || ((ERRORS++))
check_file scripts/dev-start.sh || ((ERRORS++))
check_file scripts/dev-stop.sh || ((ERRORS++))
check_file scripts/test-all.sh || ((ERRORS++))

# Check if scripts are executable
if [ -x scripts/provision-vm.sh ]; then
    echo -e "${GREEN}✓${NC} Scripts are executable"
else
    echo -e "${YELLOW}⚠${NC} Scripts not executable (run: chmod +x scripts/*.sh)"
fi
echo ""

# Check documentation
echo "Checking Documentation..."
check_file README.md || ((ERRORS++))
check_file QUICKSTART.md || ((ERRORS++))
check_file docs/SETUP.md || ((ERRORS++))
check_file docs/AGENT-1-COMPLETION.md || ((ERRORS++))
check_file internal_docs/vm-setup.md || ((ERRORS++))
echo ""

# Check service account key
echo "Checking Service Account Key..."
if [ -f backend/medsearch-key.json ]; then
    echo -e "${GREEN}✓${NC} backend/medsearch-key.json"
elif [ -f internal_docs/medsearch-key.json ]; then
    echo -e "${YELLOW}⚠${NC} Found in internal_docs/ (copy to backend/)"
    echo "  Run: cp internal_docs/medsearch-key.json backend/"
else
    echo -e "${RED}✗${NC} medsearch-key.json not found"
    echo "  Place your service account key at backend/medsearch-key.json"
    ((ERRORS++))
fi
echo ""

# Check environment files
echo "Checking Environment Files..."
if [ -f backend/.env ]; then
    echo -e "${GREEN}✓${NC} backend/.env"
else
    echo -e "${YELLOW}⚠${NC} backend/.env not found (copy from .env.example)"
    echo "  Run: cp backend/.env.example backend/.env"
fi

if [ -f frontend/.env.local ]; then
    echo -e "${GREEN}✓${NC} frontend/.env.local"
else
    echo -e "${YELLOW}⚠${NC} frontend/.env.local not found (copy from .env.example)"
    echo "  Run: cp frontend/.env.example frontend/.env.local"
fi
echo ""

# Check Docker
echo "Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker is running"
else
    echo -e "${RED}✗${NC} Docker is not running"
    echo "  Please start Docker Desktop"
    ((ERRORS++))
fi
echo ""

# Summary
echo "========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Setup verification passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Ensure backend/.env and frontend/.env.local are configured"
    echo "2. Run: ./scripts/dev-start.sh"
    echo "3. Access: http://localhost:3000"
else
    echo -e "${RED}❌ Setup verification failed with $ERRORS error(s)${NC}"
    echo ""
    echo "Please fix the errors above and run this script again."
    exit 1
fi
echo "========================================="

