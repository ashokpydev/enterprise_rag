"""
Makefile for common development tasks
"""

.PHONY: help build up down logs test lint format clean

help:
	@echo "Enterprise RAG Platform - Development Tasks"
	@echo "=========================================="
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - View logs (docker-compose logs -f)"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make init-db        - Initialize database"
	@echo ""

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	docker-compose exec api pytest tests/ -v

lint:
	docker-compose exec api pylint app/

format:
	docker-compose exec api black app/ --line-length=100
	docker-compose exec api isort app/

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

init-db:
	docker-compose exec api python -m app.core.database

shell-api:
	docker-compose exec api bash

shell-db:
	docker-compose exec postgres psql -U postgres -d enterprise_rag
