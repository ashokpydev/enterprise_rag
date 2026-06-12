#!/bin/bash
set -e

echo "🚀 Enterprise RAG Platform - Setup Script"
echo "=========================================="

# Check prerequisites
echo "✓ Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Please install Docker."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose not found. Please install Docker Compose."; exit 1; }

# Copy environment file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📋 Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env and add your OpenAI API key"
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose exec -T api curl -s http://localhost:8000/health | python3 -m json.tool || echo "API not ready yet"

# Initialize database
echo "🗄️  Initializing database..."
docker-compose exec -T api python -m app.core.database || echo "Database initialization failed (may be expected)"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Service URLs:"
echo "   • API:       http://localhost:8000"
echo "   • API Docs:  http://localhost:8000/docs"
echo "   • Dashboard: http://localhost:3000"
echo ""
echo "📝 Next steps:"
echo "   1. Edit backend/.env with your OpenAI API key"
echo "   2. Open http://localhost:8000/docs to test the API"
echo "   3. Open http://localhost:3000 to view the dashboard"
echo ""
echo "🛑 To stop all services: docker-compose down"
echo "📊 To view logs: docker-compose logs -f <service>"
