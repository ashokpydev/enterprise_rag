#!/bin/bash
set -e

echo "Testing Enterprise RAG Platform"
echo "==============================="

# Start services in background
echo "Starting test environment..."
docker-compose -f docker-compose.yml up -d

echo "Waiting for services to be ready..."
sleep 15

# Run tests
echo "Running integration tests..."
docker-compose exec -T api pytest tests/ -v --tb=short

# Run load test
echo ""
echo "Running load test..."
docker-compose exec -T api python -m tests.load_test

# Cleanup
echo ""
echo "Stopping test environment..."
docker-compose down

echo ""
echo "✅ Tests completed!"
