"""
Common development tasks and commands.
"""

# Build images
docker-compose build

# Start services
docker-compose up -d
docker-compose up -d --build  # Rebuild before starting

# View logs
docker-compose logs -f                    # All services
docker-compose logs -f api                # API only
docker-compose logs -f api --tail=100    # Last 100 lines

# Run commands in containers
docker-compose exec api bash              # API shell
docker-compose exec postgres psql -U postgres

# Database operations
docker-compose exec api python -m app.core.database  # Initialize DB
docker-compose exec postgres pg_dump -U postgres enterprise_rag > backup.sql

# Celery operations
docker-compose exec celery celery -A app.tasks.celery_tasks inspect active
docker-compose logs -f celery

# Test operations
docker-compose exec api pytest tests/ -v
docker-compose exec api pytest tests/test_integration.py::TestMultiTenancy -v

# Clean up
docker-compose down                       # Stop all
docker-compose down -v                    # Stop + remove volumes
docker rmi $(docker images -q)            # Remove all images

# Performance monitoring
docker stats                              # Container resource usage

# API Testing (in separate terminal)
curl http://localhost:8000/health
curl http://localhost:8000/docs           # Interactive docs
curl http://localhost:8000/openapi.json   # OpenAPI spec

# Example query
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-Tenant-ID: tenant-1" \
  -H "X-User-ID: user-1" \
  -H "Content-Type: application/json" \
  -d '{"query":"test query"}'
