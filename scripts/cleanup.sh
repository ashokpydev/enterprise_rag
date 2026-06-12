#!/bin/bash
set -e

echo "🧹 Cleaning up Enterprise RAG Platform"
echo "======================================"

# Stop containers
echo "Stopping containers..."
docker-compose down

# Remove volumes (optional)
read -p "Remove persistent data volumes? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing volumes..."
    docker-compose down -v
fi

# Remove images
read -p "Remove Docker images? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing images..."
    docker rmi enterprise_rag-api enterprise_rag-dashboard || true
fi

echo ""
echo "✅ Cleanup complete!"
