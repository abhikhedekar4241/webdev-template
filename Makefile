.PHONY: help up down build restart logs migrate seed test lint format shell generate-types docs-serve docs-build reset-db

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services in the background
	docker-compose up -d

down: ## Stop and remove all containers
	docker-compose down

build: ## Build or rebuild services
	docker-compose build

restart: ## Restart all services
	docker-compose restart

logs: ## Follow logs from backend and worker
	docker-compose logs -f backend worker

migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

seed: ## Seed the database with initial data
	docker-compose exec backend python seed.py

test: ## Run backend and frontend tests
	docker-compose exec backend pytest tests/ -v
	cd frontend && npm test

lint: ## Run linters and format checks for both backend and frontend
	docker-compose exec backend ruff check app/ tests/
	docker-compose exec backend ruff format --check app/ tests/
	cd frontend && npm run lint
	cd frontend && npx prettier --check "src/**/*.{ts,tsx}"

format: ## Automatically format code for both backend and frontend
	docker-compose exec backend ruff format app/ tests/
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

shell: ## Open an interactive Python shell with database session
	docker-compose exec backend python -i -c "from app.core.db import *; from sqlmodel import Session; session = Session(engine)"

generate-types: ## Generate TypeScript types from the FastAPI OpenAPI schema
	cd frontend && npx openapi-typescript http://localhost/api/openapi.json -o src/types/api.ts
	@echo "Types generated at frontend/src/types/api.ts"

docs-serve: ## Serve documentation using Docker
	docker-compose --profile docs up docs

docs-build: ## Build documentation site using Docker
	docker-compose --profile docs run --rm docs build -f docs/mkdocs.yml

reset-db: ## Wipe the database, run migrations, and re-seed
	docker-compose down -v
	docker-compose up -d db redis
	@echo "Waiting for DB..."
	@sleep 3
	$(MAKE) migrate
	$(MAKE) seed

# Deployment
deploy: ## Deploy the application using Kamal
	kamal deploy

deploy-setup: ## Set up the deployment environment using Kamal
	kamal setup

deploy-rollback: ## Roll back to the previous deployment using Kamal
	kamal rollback
