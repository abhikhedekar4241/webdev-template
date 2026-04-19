.PHONY: up down build restart logs migrate seed test lint format shell generate-types reset-db

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

restart:
	docker-compose restart

logs:
	docker-compose logs -f backend worker

migrate:
	docker-compose exec backend alembic upgrade head

seed:
	docker-compose exec backend python seed.py

test:
	docker-compose exec backend pytest tests/ -v
	cd frontend && npm test

lint:
	docker-compose exec backend ruff check app/ tests/
	docker-compose exec backend ruff format --check app/ tests/
	cd frontend && npm run lint
	cd frontend && npx prettier --check "src/**/*.{ts,tsx}"

format:
	docker-compose exec backend ruff format app/ tests/
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

shell:
	docker-compose exec backend python -i -c "from app.core.db import *; from sqlmodel import Session; session = Session(engine)"

generate-types:
	cd frontend && npx openapi-typescript http://localhost/api/openapi.json -o src/types/api.ts
	@echo "Types generated at frontend/src/types/api.ts"

reset-db:
	docker-compose down -v
	docker-compose up -d db redis
	@echo "Waiting for DB..."
	@sleep 3
	$(MAKE) migrate
	$(MAKE) seed
