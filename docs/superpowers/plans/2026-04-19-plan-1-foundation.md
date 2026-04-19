# Foundation & Infrastructure Implementation Plan (Plan 1 of 6)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the full 9-service Docker stack, backend skeleton (FastAPI + config + DB + security + middleware + health), and frontend skeleton (Next.js + Tailwind + shadcn + TanStack Query + Zustand + middleware) with working tests and CI.

**Architecture:** Nginx is the single entry point routing `/api/*` and `/health` to FastAPI, everything else to Next.js. Backend and frontend source directories are volume-mounted for hot reload in dev. All 9 services (db, backend, frontend, redis, worker, influxdb, grafana, minio, nginx) are defined in a single `docker-compose.yml`.

**Tech Stack:** Docker Compose, Nginx, FastAPI 0.111, SQLModel, Alembic, pydantic-settings, python-jose, passlib[bcrypt], structlog, slowapi, Next.js 14, TanStack Query 5, Zustand 4, Axios, shadcn/ui, next-themes, Tailwind CSS, TypeScript

---

## File Map

**Root:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `nginx/nginx.conf`
- Create: `grafana/provisioning/datasources/.gitkeep`
- Create: `grafana/provisioning/dashboards/.gitkeep`
- Create: `Makefile`
- Create: `.pre-commit-config.yaml`
- Create: `.github/workflows/ci.yml`

**Backend:**
- Create: `backend/Dockerfile`
- Create: `backend/requirements.txt`
- Create: `backend/ruff.toml`
- Create: `backend/alembic.ini`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/worker.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/db.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/middleware.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/health.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/utils/__init__.py`
- Create: `backend/app/utils/pagination.py`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/.gitkeep`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/tests/test_security.py`
- Create: `backend/tests/test_pagination.py`

**Frontend:**
- Create: `frontend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.mjs`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/.eslintrc.json`
- Create: `frontend/.prettierrc`
- Create: `frontend/components.json`
- Create: `frontend/src/app/globals.css`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/error.tsx`
- Create: `frontend/src/app/not-found.tsx`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/lib/providers.tsx`
- Create: `frontend/src/middleware.ts`
- Create: `frontend/src/constants/routes.ts`
- Create: `frontend/src/constants/queryKeys.ts`
- Create: `frontend/src/constants/roles.ts`
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/components/ui/button.tsx` (via shadcn CLI)
- Create: `frontend/src/components/ui/input.tsx` (via shadcn CLI)
- Create: `frontend/src/components/ui/card.tsx` (via shadcn CLI)
- Create: `frontend/src/components/ui/sonner.tsx` (via shadcn CLI)
- Create: `frontend/src/components/shared/Navbar.tsx`

---

## Task 1: Root Structure

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `grafana/provisioning/datasources/.gitkeep`
- Create: `grafana/provisioning/dashboards/.gitkeep`

- [ ] **Step 1: Create `.gitignore`**

```
# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
.ruff_cache/
.mypy_cache/

# Node
node_modules/
.next/
npm-debug.log*

# Environment
.env
.env.local
.env.*.local

# Docker volumes
.docker/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Generated
frontend/src/types/api.ts
```

- [ ] **Step 2: Create `.env.example`**

```bash
# Database
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=boilerplate
POSTGRES_PASSWORD=changeme
POSTGRES_DB=boilerplate

# Auth
SECRET_KEY=change-this-to-a-long-random-secret-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (SMTP)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=changeme
SMTP_FROM=noreply@example.com

# InfluxDB
INFLUXDB_USER=admin
INFLUXDB_PASSWORD=changeme123
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=metrics
INFLUXDB_TOKEN=my-super-secret-admin-token

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=changeme

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=uploads

# Redis
REDIS_URL=redis://redis:6379/0

# Frontend
FRONTEND_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost/api

# CORS (JSON array)
CORS_ORIGINS=["http://localhost:3000","http://localhost"]
```

- [ ] **Step 3: Create Grafana provisioning placeholder directories**

```bash
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards
touch grafana/provisioning/datasources/.gitkeep
touch grafana/provisioning/dashboards/.gitkeep
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore .env.example grafana/
git commit -m "chore: add root project structure and env template"
```

---

## Task 2: Docker Compose + Nginx

**Files:**
- Create: `docker-compose.yml`
- Create: `nginx/nginx.conf`

- [ ] **Step 1: Create `nginx/nginx.conf`**

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;

        # Backend: API routes + health + OpenAPI docs
        location ~ ^/(api|health|docs|openapi.json|redoc) {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Request-ID $request_id;
        }

        # Next.js HMR WebSocket (dev hot reload)
        location /_next/webpack-hmr {
            proxy_pass http://frontend/_next/webpack-hmr;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        # Frontend: everything else
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

- [ ] **Step 2: Create `docker-compose.yml`**

```yaml
version: '3.9'

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    ports:
      - "6379:6379"

  influxdb:
    image: influxdb:2
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: ${INFLUXDB_USER}
      DOCKER_INFLUXDB_INIT_PASSWORD: ${INFLUXDB_PASSWORD}
      DOCKER_INFLUXDB_INIT_ORG: ${INFLUXDB_ORG}
      DOCKER_INFLUXDB_INIT_BUCKET: ${INFLUXDB_BUCKET}
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: ${INFLUXDB_TOKEN}
    volumes:
      - influxdb_data:/var/lib/influxdb2
    ports:
      - "8086:8086"

  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_USER}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - influxdb
    ports:
      - "3001:3000"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 5
    ports:
      - "9000:9000"
      - "9001:9001"

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    env_file: .env
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"

  worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    env_file: .env
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build: ./frontend
    command: npm run dev
    environment:
      NEXT_PUBLIC_API_URL: http://localhost/api
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    depends_on:
      - backend
    ports:
      - "3000:3000"

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
    ports:
      - "80:80"

volumes:
  postgres_data:
  influxdb_data:
  grafana_data:
  minio_data:
```

- [ ] **Step 3: Validate compose syntax**

```bash
docker-compose config
```

Expected: YAML output with all 9 services, no errors.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml nginx/
git commit -m "chore: add docker-compose with all 9 services and nginx config"
```

---

## Task 3: Backend Dockerfile + requirements.txt + ruff config

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/requirements.txt`
- Create: `backend/ruff.toml`

- [ ] **Step 1: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create `backend/requirements.txt`**

```
# Web framework
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9

# Database
sqlmodel==0.0.19
psycopg2-binary==2.9.9
alembic==1.13.1

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Config
pydantic-settings==2.2.1
email-validator==2.1.1

# HTTP client
httpx==0.27.0

# Rate limiting
slowapi==0.1.9

# Logging
structlog==24.1.0

# Cache & Queue
redis==5.0.4
celery==5.4.0

# Metrics
influxdb-client==1.43.0

# Storage
minio==7.2.7

# Email
aiosmtplib==3.0.1
jinja2==3.1.4

# Testing
pytest==8.2.0
pytest-asyncio==0.23.6
factory-boy==3.3.0
faker==25.2.0

# Linting
ruff==0.4.4
```

- [ ] **Step 3: Create `backend/ruff.toml`**

```toml
target-version = "py311"
line-length = 88

[lint]
select = ["E", "F", "W", "I", "N", "UP"]
ignore = ["E501"]

[lint.isort]
known-first-party = ["app"]
```

- [ ] **Step 4: Build backend image to verify Dockerfile**

```bash
docker build ./backend -t boilerplate-backend:test
```

Expected: Successfully built (image ID printed). No errors.

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile backend/requirements.txt backend/ruff.toml
git commit -m "chore: add backend Dockerfile and dependencies"
```

---

## Task 4: Backend Config

**Files:**
- Create: `backend/app/__init__.py` (empty)
- Create: `backend/app/core/__init__.py` (empty)
- Create: `backend/app/core/config.py`

- [ ] **Step 1: Create empty `__init__.py` files**

```bash
touch backend/app/__init__.py
touch backend/app/core/__init__.py
touch backend/app/api/__init__.py
touch backend/app/api/v1/__init__.py
touch backend/app/models/__init__.py
touch backend/app/services/__init__.py
touch backend/app/utils/__init__.py
touch backend/tests/__init__.py
```

- [ ] **Step 2: Create `backend/app/core/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Email
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str

    # InfluxDB
    INFLUXDB_URL: str = "http://influxdb:8086"
    INFLUXDB_TOKEN: str
    INFLUXDB_ORG: str
    INFLUXDB_BUCKET: str

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "uploads"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
```

- [ ] **Step 3: Verify config loads (run from backend/ directory)**

```bash
cd backend && python -c "from app.core.config import settings; print(settings.ALGORITHM)"
```

Expected: `HS256`

Note: This requires a `.env` file in `backend/` or the root. Copy `.env.example` to `.env` first:
```bash
cp .env.example .env
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/
git commit -m "feat: add backend config with pydantic-settings"
```

---

## Task 5: Backend Database + Alembic

**Files:**
- Create: `backend/app/core/db.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/.gitkeep`

- [ ] **Step 1: Create `backend/app/core/db.py`**

```python
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
```

- [ ] **Step 2: Create `backend/alembic.ini`**

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 3: Create `backend/alembic/env.py`**

```python
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel

# Import all models here as they are created in later plans so Alembic
# can detect schema changes. Example (uncomment as models are added):
# from app.models.user import User  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def get_url() -> str:
    from app.core.config import settings
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Create `backend/alembic/versions/.gitkeep`**

```bash
mkdir -p backend/alembic/versions
touch backend/alembic/versions/.gitkeep
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/db.py backend/alembic.ini backend/alembic/
git commit -m "feat: add SQLModel DB engine and Alembic migration setup"
```

---

## Task 6: Backend Security (JWT + bcrypt)

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/tests/test_security.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_security.py`:

```python
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_is_not_plaintext():
    hashed = hash_password("supersecret")
    assert hashed != "supersecret"


def test_correct_password_verifies():
    hashed = hash_password("supersecret")
    assert verify_password("supersecret", hashed) is True


def test_wrong_password_fails_verification():
    hashed = hash_password("supersecret")
    assert verify_password("wrongpassword", hashed) is False


def test_create_and_decode_token():
    token = create_access_token(subject="user-abc-123")
    subject = decode_access_token(token)
    assert subject == "user-abc-123"


def test_decode_invalid_token_returns_none():
    result = decode_access_token("not.a.valid.token")
    assert result is None


def test_decode_tampered_token_returns_none():
    token = create_access_token(subject="user-123")
    tampered = token + "tampered"
    result = decode_access_token(tampered)
    assert result is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && pytest tests/test_security.py -v
```

Expected: `ImportError` — `app.core.security` does not exist yet.

- [ ] **Step 3: Create `backend/app/core/security.py`**

```python
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    payload = {"exp": expire, "sub": str(subject)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend && pytest tests/test_security.py -v
```

Expected:
```
tests/test_security.py::test_password_hash_is_not_plaintext PASSED
tests/test_security.py::test_correct_password_verifies PASSED
tests/test_security.py::test_wrong_password_fails_verification PASSED
tests/test_security.py::test_create_and_decode_token PASSED
tests/test_security.py::test_decode_invalid_token_returns_none PASSED
tests/test_security.py::test_decode_tampered_token_returns_none PASSED
6 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security.py backend/tests/test_security.py
git commit -m "feat: add JWT token creation/decoding and bcrypt password hashing"
```

---

## Task 7: Backend Middleware (Request ID + structlog + rate limiting)

**Files:**
- Create: `backend/app/core/middleware.py`

- [ ] **Step 1: Create `backend/app/core/middleware.py`**

```python
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/middleware.py
git commit -m "feat: add request ID middleware with structlog"
```

---

## Task 8: Backend App Entry Point + Celery Worker

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/worker.py`

- [ ] **Step 1: Create `backend/app/worker.py`**

```python
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.jobs.examples"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
```

- [ ] **Step 2: Create `backend/app/main.py`**

```python
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import health
from app.core.config import settings
from app.core.middleware import RequestIDMiddleware

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Boilerplate API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
```

- [ ] **Step 3: Verify app imports without error**

```bash
cd backend && python -c "from app.main import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py backend/app/worker.py
git commit -m "feat: wire up FastAPI app with middleware and Celery worker stub"
```

---

## Task 9: Health Endpoint + Tests

**Files:**
- Create: `backend/app/api/v1/health.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.db import get_session
from app.main import app


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

Create `backend/tests/test_health.py`:

```python
def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body_has_status_ok(client):
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_body_has_db_ok(client):
    response = client.get("/health")
    data = response.json()
    assert data["db"] == "ok"


def test_health_has_request_id_header(client):
    response = client.get("/health")
    assert "x-request-id" in response.headers
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && pytest tests/test_health.py -v
```

Expected: `ImportError` or `404` — health router not wired yet.

- [ ] **Step 3: Create `backend/app/api/v1/health.py`**

```python
from fastapi import APIRouter, Depends
from sqlmodel import Session, text

from app.core.db import get_session

router = APIRouter()


@router.get("/health")
def health_check(session: Session = Depends(get_session)) -> dict:
    try:
        session.exec(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
    }
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend && pytest tests/test_health.py -v
```

Expected:
```
tests/test_health.py::test_health_returns_ok PASSED
tests/test_health.py::test_health_body_has_status_ok PASSED
tests/test_health.py::test_health_body_has_db_ok PASSED
tests/test_health.py::test_health_has_request_id_header PASSED
4 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/health.py backend/tests/conftest.py backend/tests/test_health.py
git commit -m "feat: add health endpoint with DB connectivity check"
```

---

## Task 10: Pagination Utility + Tests

**Files:**
- Create: `backend/app/utils/pagination.py`
- Create: `backend/tests/test_pagination.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_pagination.py`:

```python
from app.utils.pagination import PaginatedResponse, paginate


def test_paginate_calculates_pages_correctly():
    result = paginate(items=list(range(10)), total=25, page=1, size=10)
    assert result.pages == 3


def test_paginate_returns_correct_metadata():
    result = paginate(items=list(range(10)), total=25, page=2, size=10)
    assert result.total == 25
    assert result.page == 2
    assert result.size == 10


def test_paginate_preserves_items():
    items = ["a", "b", "c"]
    result = paginate(items=items, total=3, page=1, size=10)
    assert list(result.items) == ["a", "b", "c"]


def test_paginate_empty_result():
    result = paginate(items=[], total=0, page=1, size=10)
    assert result.total == 0
    assert result.pages == 0
    assert list(result.items) == []


def test_paginate_last_page_with_remainder():
    # 25 items, 10 per page → 3 pages
    result = paginate(items=list(range(5)), total=25, page=3, size=10)
    assert result.pages == 3
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && pytest tests/test_pagination.py -v
```

Expected: `ImportError` — module doesn't exist yet.

- [ ] **Step 3: Create `backend/app/utils/pagination.py`**

```python
from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int
    pages: int


def paginate(
    items: Sequence[T],
    total: int,
    page: int,
    size: int,
) -> PaginatedResponse[T]:
    pages = (total + size - 1) // size if size > 0 else 0
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend && pytest tests/test_pagination.py -v
```

Expected:
```
tests/test_pagination.py::test_paginate_calculates_pages_correctly PASSED
tests/test_pagination.py::test_paginate_returns_correct_metadata PASSED
tests/test_pagination.py::test_paginate_preserves_items PASSED
tests/test_pagination.py::test_paginate_empty_result PASSED
tests/test_pagination.py::test_paginate_last_page_with_remainder PASSED
5 passed
```

- [ ] **Step 5: Run full test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: 15 tests, all passing.

- [ ] **Step 6: Run linter**

```bash
cd backend && ruff check app/ tests/ && ruff format --check app/ tests/
```

Expected: No errors.

- [ ] **Step 7: Commit**

```bash
git add backend/app/utils/pagination.py backend/tests/test_pagination.py
git commit -m "feat: add generic pagination utility"
```

---

## Task 11: Frontend Setup (Dockerfile + package.json + config files)

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.mjs`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/.eslintrc.json`
- Create: `frontend/.prettierrc`

- [ ] **Step 1: Create `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

- [ ] **Step 2: Create `frontend/package.json`**

```json
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest --passWithNoTests",
    "test:watch": "jest --watch"
  },
  "dependencies": {
    "next": "14.2.3",
    "react": "^18",
    "react-dom": "^18",
    "@tanstack/react-query": "^5.37.1",
    "zustand": "^4.5.2",
    "axios": "^1.7.2",
    "next-themes": "^0.3.0",
    "react-hook-form": "^7.51.5",
    "zod": "^3.23.8",
    "@hookform/resolvers": "^3.4.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.3.0",
    "lucide-react": "^0.383.0",
    "sonner": "^1.5.0",
    "tailwindcss-animate": "^1.0.7"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "tailwindcss": "^3.4.4",
    "autoprefixer": "^10.4.19",
    "postcss": "^8",
    "eslint": "^8",
    "eslint-config-next": "14.2.3",
    "prettier": "^3.3.2",
    "prettier-plugin-tailwindcss": "^0.6.5",
    "jest": "^29.7.0",
    "@jest/globals": "^29.7.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.4.6",
    "jest-environment-jsdom": "^29.7.0",
    "openapi-typescript": "^6.7.6"
  }
}
```

- [ ] **Step 3: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 4: Create `frontend/next.config.mjs`**

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
};

export default nextConfig;
```

- [ ] **Step 5: Create `frontend/tailwind.config.ts`**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
```

- [ ] **Step 6: Create `frontend/postcss.config.js`**

```js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 7: Create `frontend/.eslintrc.json`**

```json
{
  "extends": ["next/core-web-vitals", "next/typescript"]
}
```

- [ ] **Step 8: Create `frontend/.prettierrc`**

```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

- [ ] **Step 9: Commit**

```bash
git add frontend/
git commit -m "chore: add frontend project config (Next.js, Tailwind, TypeScript, ESLint, Prettier)"
```

---

## Task 12: Frontend shadcn/ui Setup + Base Components

**Files:**
- Create: `frontend/components.json`
- Create: `frontend/src/app/globals.css`
- Create: `frontend/src/components/ui/` (via shadcn CLI)

- [ ] **Step 1: Create `frontend/components.json`**

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsx": false,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/app/globals.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

- [ ] **Step 2: Create `frontend/src/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

- [ ] **Step 3: Create `frontend/src/lib/utils.ts`**

```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 4: Install dependencies and add shadcn components**

```bash
cd frontend && npm install
npx shadcn-ui@latest add button input card sonner --yes
```

Expected: Creates files in `src/components/ui/` — `button.tsx`, `input.tsx`, `card.tsx`, `sonner.tsx`.

- [ ] **Step 5: Commit**

```bash
git add frontend/components.json frontend/src/
git commit -m "feat: add shadcn/ui config and base components (button, input, card, sonner)"
```

---

## Task 13: Frontend Core Pages + Providers

**Files:**
- Create: `frontend/src/lib/providers.tsx`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/error.tsx`
- Create: `frontend/src/app/not-found.tsx`

- [ ] **Step 1: Create `frontend/src/lib/providers.tsx`**

```tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      })
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```

- [ ] **Step 2: Create `frontend/src/app/layout.tsx`**

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { Toaster } from "@/components/ui/sonner";
import { QueryProvider } from "@/lib/providers";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Boilerplate",
  description: "Full-stack boilerplate",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <QueryProvider>
            {children}
            <Toaster />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Create `frontend/src/app/page.tsx`**

```tsx
import { redirect } from "next/navigation";
import { ROUTES } from "@/constants/routes";

export default function Home() {
  redirect(ROUTES.dashboard);
}
```

Note: `ROUTES` will be created in Task 14. Create it after that task if there are import errors.

- [ ] **Step 4: Create `frontend/src/app/error.tsx`**

```tsx
"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h2 className="text-2xl font-semibold">Something went wrong</h2>
      <p className="text-muted-foreground">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
```

- [ ] **Step 5: Create `frontend/src/app/not-found.tsx`**

```tsx
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/constants/routes";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h2 className="text-2xl font-semibold">Page not found</h2>
      <p className="text-muted-foreground">
        The page you are looking for does not exist.
      </p>
      <Button asChild>
        <Link href={ROUTES.dashboard}>Go home</Link>
      </Button>
    </div>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/providers.tsx frontend/src/app/
git commit -m "feat: add Next.js root layout with ThemeProvider, QueryProvider, and Toaster"
```

---

## Task 14: Frontend Constants + API Client + Middleware

**Files:**
- Create: `frontend/src/constants/routes.ts`
- Create: `frontend/src/constants/queryKeys.ts`
- Create: `frontend/src/constants/roles.ts`
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/middleware.ts`
- Create: `frontend/src/components/shared/Navbar.tsx`

- [ ] **Step 1: Create `frontend/src/constants/routes.ts`**

```typescript
export const ROUTES = {
  home: "/",
  dashboard: "/dashboard",
  auth: {
    login: "/auth/login",
    signup: "/auth/signup",
    forgotPassword: "/auth/forgot-password",
    resetPassword: "/auth/reset-password",
  },
  orgs: {
    list: "/orgs",
    new: "/orgs/new",
    detail: (orgId: string) => `/orgs/${orgId}`,
    members: (orgId: string) => `/orgs/${orgId}/members`,
    settings: (orgId: string) => `/orgs/${orgId}/settings`,
  },
  invitations: "/invitations",
} as const;
```

- [ ] **Step 2: Create `frontend/src/constants/queryKeys.ts`**

```typescript
export const QUERY_KEYS = {
  me: ["me"] as const,
  orgs: {
    list: ["orgs"] as const,
    detail: (orgId: string) => ["orgs", orgId] as const,
    members: (orgId: string) => ["orgs", orgId, "members"] as const,
    flags: (orgId: string) => ["orgs", orgId, "flags"] as const,
  },
  invitations: {
    list: ["invitations"] as const,
  },
  files: {
    list: (orgId: string) => ["files", orgId] as const,
  },
} as const;
```

- [ ] **Step 3: Create `frontend/src/constants/roles.ts`**

```typescript
export const ROLES = {
  OWNER: "owner",
  ADMIN: "admin",
  MEMBER: "member",
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];

export const ROLE_LABELS: Record<Role, string> = {
  owner: "Owner",
  admin: "Admin",
  member: "Member",
};
```

- [ ] **Step 4: Create `frontend/src/services/api.ts`**

```typescript
import axios from "axios";
import { ROUTES } from "@/constants/routes";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      // Also clear auth cookie for middleware
      document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;";
      window.location.href = ROUTES.auth.login;
    }
    return Promise.reject(error);
  }
);

export default api;
```

- [ ] **Step 5: Create `frontend/src/middleware.ts`**

```typescript
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = [
  "/auth/login",
  "/auth/signup",
  "/auth/forgot-password",
  "/auth/reset-password",
];

export function middleware(request: NextRequest) {
  const token = request.cookies.get("access_token")?.value;
  const { pathname } = request.nextUrl;

  const isPublicPath = PUBLIC_PATHS.some(
    (path) => pathname === path || pathname.startsWith(path + "/")
  );

  // Unauthenticated user hitting a protected route → redirect to login
  if (!token && !isPublicPath) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Authenticated user hitting login → redirect to dashboard
  if (token && pathname === "/auth/login") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|public/).*)"],
};
```

- [ ] **Step 6: Create `frontend/src/components/shared/Navbar.tsx`**

```tsx
"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Moon, Sun } from "lucide-react";
import { ROUTES } from "@/constants/routes";

export function Navbar() {
  const { theme, setTheme } = useTheme();

  return (
    <nav className="border-b bg-background px-4 py-3">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <Link href={ROUTES.dashboard} className="text-lg font-semibold">
          Boilerplate
        </Link>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label="Toggle theme"
          >
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </div>
      </div>
    </nav>
  );
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/constants/ frontend/src/services/ frontend/src/middleware.ts frontend/src/components/shared/
git commit -m "feat: add frontend constants, API client with auth interceptors, and edge middleware"
```

---

## Task 15: Makefile + GitHub Actions CI + Pre-commit

**Files:**
- Create: `Makefile`
- Create: `.github/workflows/ci.yml`
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Create `Makefile`**

```makefile
.PHONY: up down build restart logs migrate seed test lint shell generate-types reset-db

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
```

- [ ] **Step 2: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
        working-directory: backend
      - name: Lint
        run: ruff check app/ tests/
        working-directory: backend
      - name: Format check
        run: ruff format --check app/ tests/
        working-directory: backend
      - name: Test
        env:
          POSTGRES_HOST: localhost
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
          SECRET_KEY: ci-test-secret-key-not-for-production
          SMTP_HOST: localhost
          SMTP_PORT: 587
          SMTP_USER: test@test.com
          SMTP_PASSWORD: test
          SMTP_FROM: test@test.com
          INFLUXDB_URL: http://localhost:8086
          INFLUXDB_TOKEN: test-token
          INFLUXDB_ORG: test
          INFLUXDB_BUCKET: test
          MINIO_ENDPOINT: localhost:9000
          MINIO_ACCESS_KEY: test
          MINIO_SECRET_KEY: test
          REDIS_URL: redis://localhost:6379/0
        run: pytest tests/ -v
        working-directory: backend

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json
      - name: Install dependencies
        run: npm ci
        working-directory: frontend
      - name: Lint
        run: npm run lint
        working-directory: frontend
      - name: Format check
        run: npx prettier --check "src/**/*.{ts,tsx}"
        working-directory: frontend
      - name: Test
        run: npm test
        working-directory: frontend
```

- [ ] **Step 3: Create `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
        files: ^backend/
      - id: ruff-format
        files: ^backend/

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        files: ^frontend/src/.*\.(ts|tsx)$
        additional_dependencies:
          - prettier@3.3.2
          - prettier-plugin-tailwindcss@0.6.5
```

- [ ] **Step 4: Verify docker-compose brings everything up**

```bash
cp .env.example .env
docker-compose up -d
docker-compose ps
```

Expected: All 9 services show as `Up` or `healthy`.

- [ ] **Step 5: Verify health endpoint is reachable through Nginx**

```bash
curl http://localhost/health
```

Expected:
```json
{"status": "ok", "db": "ok"}
```

- [ ] **Step 6: Run full backend test suite one final time**

```bash
docker-compose exec backend pytest tests/ -v
```

Expected: 15 tests, all passing.

- [ ] **Step 7: Commit**

```bash
git add Makefile .github/ .pre-commit-config.yaml
git commit -m "chore: add Makefile, GitHub Actions CI, and pre-commit hooks"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] All 9 Docker services defined in docker-compose.yml
- [x] Nginx routing `/api/*` and `/health` → backend, `/*` → frontend
- [x] Hot reload via volume mounts (backend and frontend)
- [x] Backend: FastAPI, pydantic-settings, SQLModel engine, Alembic setup
- [x] Backend: JWT (create/decode), bcrypt (hash/verify)
- [x] Backend: Request ID middleware with structlog
- [x] Backend: slowapi rate limiting wired to app
- [x] Backend: `/health` endpoint with DB check
- [x] Backend: Pagination utility
- [x] Frontend: Next.js 14, Tailwind, TypeScript, shadcn/ui
- [x] Frontend: TanStack Query provider
- [x] Frontend: Zustand (stores scaffolded in Plan 2)
- [x] Frontend: `middleware.ts` auth guard with redirect logic
- [x] Frontend: Axios with Bearer token + 401 interceptor
- [x] Frontend: `ROUTES`, `QUERY_KEYS`, `ROLES` constants
- [x] Frontend: Dark mode via next-themes + Navbar toggle
- [x] Frontend: shadcn Toaster in root layout
- [x] Frontend: `error.tsx` global error boundary
- [x] Makefile with all required targets
- [x] GitHub Actions CI (lint + test for both)
- [x] Pre-commit hooks (ruff + prettier)
- [x] `.env.example` with all variables documented

**Notes for implementer:**
- `seed.py` will be created in Plan 5. `make seed` will fail until then.
- `app.jobs.examples` referenced in `worker.py` — create `backend/app/jobs/__init__.py` and `backend/app/jobs/examples.py` (empty) to prevent import errors.
- The `ROUTES` import in `page.tsx` and `not-found.tsx` requires `constants/routes.ts` to exist first — create Task 14 files before Task 13 files if running out of order.
- Zustand stores (`src/store/auth.ts`, `src/store/org.ts`) are created in Plan 2.
