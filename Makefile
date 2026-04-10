# Better Business Builder - Makefile
# Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

.PHONY: help up down restart logs shell test lint migrate migration

# Docker Compose executable
DC=docker-compose

# Default target
help:
	@echo "Better Business Builder Makefile"
	@echo "================================"
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  up          Start development environment in background"
	@echo "  down        Stop and remove containers"
	@echo "  restart     Restart development environment"
	@echo "  logs        Tail logs for all services"
	@echo "  shell       Open a bash shell in the API container"
	@echo "  test        Run the test suite"
	@echo "  lint        Run linting (flake8, black)"
	@echo "  migrate     Run pending Alembic migrations"
	@echo "  migration   Create a new Alembic migration (usage: make migration m=\"message\")"
	@echo "  prod-up     Start production environment"

up:
	$(DC) up -d

down:
	$(DC) down

restart:
	$(DC) down
	$(DC) up -d

logs:
	$(DC) logs -f

shell:
	$(DC) exec api bash

test:
	pytest tests/

lint:
	flake8 src/ tests/
	black --check src/ tests/

migrate:
	$(DC) run --rm api alembic upgrade head

migration:
	@if [ -z "$(m)" ]; then echo "Migration message is required: make migration m=\"Your message\""; exit 1; fi
	$(DC) run --rm api alembic revision --autogenerate -m "$(m)"

prod-up:
	$(DC) -f docker-compose.yml -f docker-compose.prod.yml up -d
