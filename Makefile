# Better Business Builder — Makefile
# Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved.

COMPOSE := docker compose
COMPOSE_PROD := $(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml
SERVICE_API := api

.PHONY: help up down restart build test lint migrate migration logs shell deploy prod-up prod-down

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

up: ## Start all services (dev)
	$(COMPOSE) up -d

down: ## Stop all services
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

build: ## Rebuild Docker images
	$(COMPOSE) build --no-cache

logs: ## Tail logs for all services (Ctrl-C to stop)
	$(COMPOSE) logs -f --tail=100

shell: ## Open a bash shell in the API container
	$(COMPOSE) exec $(SERVICE_API) bash

# ---------------------------------------------------------------------------
# Testing & Linting
# ---------------------------------------------------------------------------

test: ## Run test suite with pytest
	$(COMPOSE) exec $(SERVICE_API) pytest --tb=short -q

lint: ## Run linters (black, isort, flake8)
	$(COMPOSE) exec $(SERVICE_API) black --check src/ tests/
	$(COMPOSE) exec $(SERVICE_API) isort --check-only src/ tests/
	$(COMPOSE) exec $(SERVICE_API) flake8 src/ tests/

# ---------------------------------------------------------------------------
# Database Migrations
# ---------------------------------------------------------------------------

migrate: ## Apply all pending Alembic migrations
	$(COMPOSE) exec $(SERVICE_API) alembic upgrade head

migration: ## Create a new migration (usage: make migration msg="description")
	$(COMPOSE) exec $(SERVICE_API) alembic revision --autogenerate -m "$(msg)"

# ---------------------------------------------------------------------------
# Production
# ---------------------------------------------------------------------------

prod-up: ## Start production stack (nginx-fronted, no exposed ports)
	$(COMPOSE_PROD) up -d --build

prod-down: ## Stop production stack
	$(COMPOSE_PROD) down

deploy: ## Run the full deploy script (pull, migrate, rebuild, restart, health)
	./scripts/deploy.sh
