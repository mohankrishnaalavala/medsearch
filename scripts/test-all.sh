#!/bin/bash
# Run all tests

set -e

echo "🧪 Running MedSearch Test Suite..."

# Backend tests
echo ""
echo "📦 Backend Tests..."
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
fi
pytest --cov=app --cov-report=term-missing
cd ..

# Frontend tests
echo ""
echo "🎨 Frontend Tests..."
cd frontend
if [ -d "node_modules" ]; then
    npm run test
else
    echo "⚠️  node_modules not found, skipping frontend tests"
    echo "Run 'npm install' in frontend directory first"
fi
cd ..

echo ""
echo "✅ All tests completed!"

