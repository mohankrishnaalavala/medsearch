#!/bin/bash
# Stop development environment

set -e

echo "🛑 Stopping MedSearch Development Environment..."

docker-compose down

echo "✅ Development environment stopped!"

