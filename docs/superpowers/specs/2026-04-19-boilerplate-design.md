# Full-Stack Boilerplate Design

**Date:** 2026-04-19  
**Status:** Approved

## Overview

A production-ready, full-stack boilerplate template for cloning and building AI-assisted web applications. Ships with authentication, multi-tenant org management, email invitations, metrics, audit logs, feature flags, background jobs, file uploads, and email notifications — all wired up and ready to extend.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, SQLModel, Pydantic, Python 3.11+ |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Metrics | InfluxDB 2 + Grafana |
| File Storage | MinIO |
| Reverse Proxy | Nginx |
| Infrastructure | Docker + Docker Compose |

---

## Infrastructure

### Docker Services (9 total)

| Service | Image | Port | Purpose |
|---|---|---|---|
| `db` | postgres:16 | 5432 | Primary database |
| `backend` | ./backend | 8000 (internal) | FastAPI app |
| `frontend` | ./frontend | 3000 (internal) | Next.js app |
| `redis` | redis:7 | 6379 | Celery broker + cache |
| `worker` | ./backend | — | Celery worker (same image, different command) |
| `influxdb` | influxdb:2 | 8086 | Time-series metrics |
| `grafana` | grafana/grafana | 3001 | Metrics dashboard |
| `minio` | minio/minio | 9000 / 9001 | S3-compatible file storage |
| `nginx` | nginx:alpine | 80 | Reverse proxy (single entry point) |

**Nginx routing:**
- `/api/*` → `backend:8000`
- `/*` → `frontend:3000`

Eliminates CORS issues entirely. In production, SSL terminates at Nginx.

**Dev hot reload:** `./backend` and `./frontend` mounted as volumes so code changes reflect without rebuilding containers.

---

## Data Models

### Users
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| email | str | unique |
| hashed_password | str | |
| full_name | str | |
| is_active | bool | default true |
| deleted_at | datetime | soft delete |
| created_at | datetime | |

### Organizations
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | str | |
| slug | str | unique, URL-safe |
| created_by | UUID | FK → users |
| deleted_at | datetime | soft delete |
| created_at | datetime | |

### OrgMemberships
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → organizations |
| user_id | UUID | FK → users |
| role | enum | `owner` \| `admin` \| `member` |
| joined_at | datetime | |

Unique constraint on `(org_id, user_id)`.

### OrgInvitations
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → organizations |
| invited_email | str | |
| role | enum | `owner` \| `admin` \| `member` |
| invited_by | UUID | FK → users |
| status | enum | `pending` \| `accepted` \| `declined` |
| expires_at | datetime | |
| created_at | datetime | |

### AuditLogs
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| event | str | e.g. `user.login`, `org.created` |
| user_id | UUID | FK → users, nullable |
| org_id | UUID | FK → organizations, nullable |
| metadata | JSON | extra context |
| created_at | datetime | |

### FeatureFlagOverrides
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → organizations |
| flag_name | str | must exist in `flags.yml` |
| enabled | bool | org-level override |
| updated_at | datetime | |

Unique constraint on `(org_id, flag_name)`.

### Files
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → organizations |
| uploaded_by | UUID | FK → users |
| filename | str | original filename |
| storage_key | str | MinIO object key |
| content_type | str | MIME type |
| size_bytes | int | |
| deleted_at | datetime | soft delete |
| created_at | datetime | |

---

## Backend

### Module Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, middleware registration, router inclusion
│   ├── worker.py                # Celery app instance
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # /register, /login, /me
│   │       ├── orgs.py          # org CRUD + members
│   │       ├── invitations.py   # list, accept, decline
│   │       ├── files.py         # upload, download, delete
│   │       └── health.py        # /health
│   ├── core/
│   │   ├── config.py            # pydantic-settings — all env vars validated at startup
│   │   ├── db.py                # SQLModel engine + session dependency
│   │   ├── security.py          # JWT encode/decode, bcrypt password hashing
│   │   ├── middleware.py        # Request ID injection, rate limiting (slowapi)
│   │   └── influx.py            # InfluxDB client wrapper
│   ├── models/
│   │   ├── user.py
│   │   ├── org.py
│   │   ├── invitation.py
│   │   ├── audit_log.py
│   │   ├── feature_flag.py
│   │   └── file.py
│   ├── services/
│   │   ├── base.py              # CRUDBase — get, get_multi, create, update, delete
│   │   ├── auth.py
│   │   ├── orgs.py
│   │   ├── invitations.py
│   │   ├── email.py             # SMTP client + Jinja2 template renderer
│   │   ├── stats.py             # stats.inc / avg / set / max → InfluxDB
│   │   ├── audit.py             # log_event(event, user_id, org_id, metadata)
│   │   ├── flags.py             # is_enabled(org_id, flag_name)
│   │   ├── files.py             # MinIO upload/download/delete
│   │   └── cache.py             # Redis @cache(ttl) decorator
│   ├── jobs/
│   │   ├── __init__.py
│   │   └── examples.py          # Example Celery tasks
│   ├── emails/
│   │   └── templates/
│   │       ├── invite.html
│   │       ├── welcome.html
│   │       └── password_reset.html
│   └── utils/
│       ├── pagination.py        # paginate(query, page, size) → PaginatedResponse
│       └── request_id.py
├── alembic/
├── tests/
│   ├── conftest.py              # pytest fixtures, test DB, Factory Boy setup
│   ├── factories.py             # UserFactory, OrgFactory, InvitationFactory (Faker)
│   ├── test_auth.py
│   ├── test_orgs.py
│   └── test_invitations.py
├── flags.yml                    # Feature flag definitions + default values
├── seed.py                      # Populates dev data: users, orgs, memberships
├── Dockerfile
├── requirements.txt
└── alembic.ini
```

### API Endpoints

**Auth — `/api/v1/auth`**
- `POST /register` — create user, send welcome email
- `POST /login` — returns JWT access token
- `GET /me` — current user profile (protected)

**Organizations — `/api/v1/orgs`**
- `POST /` — create org; creator auto-assigned `owner` role
- `GET /` — list orgs the current user belongs to
- `GET /{org_id}` — org details (members only)
- `PATCH /{org_id}` — update name/slug (`owner` or `admin`)
- `DELETE /{org_id}` — soft delete (`owner` only)
- `GET /{org_id}/members` — list members with roles
- `PATCH /{org_id}/members/{user_id}` — change role (`owner`/`admin`)
- `DELETE /{org_id}/members/{user_id}` — remove member (`owner`/`admin`)

**Invitations — `/api/v1/invitations`**
- `POST /` — create invite (org_id, email, role — `owner`/`admin` only)
- `GET /` — pending invitations for current user (matched by `invited_email == current_user.email`)
- `POST /{id}/accept` — accept; 403 if `invited_email != current_user.email`
- `POST /{id}/decline` — decline; same email guard

**Files — `/api/v1/files`**
- `POST /` — multipart upload → MinIO, metadata saved to DB
- `GET /{file_id}` — presigned download URL
- `DELETE /{file_id}` — soft delete

**Health — `/health`**
- `GET /health` — returns `{"status": "ok", "db": "ok", "redis": "ok", "influxdb": "ok"}`

### Cross-Cutting Concerns

- **Logging:** `structlog` — JSON lines, every log automatically includes `request_id`, `user_id`, `org_id`
- **Request ID:** UUID injected by middleware, returned as `X-Request-ID` response header
- **Rate limiting:** `slowapi` — configurable per-route (e.g., 5 login attempts/minute per IP)
- **Pagination:** `paginate(query, page, size)` returns `{ items, total, page, size, pages }`
- **Cache:** `@cache(ttl=60)` decorator backed by Redis
- **CRUDBase:** all services inherit generic `get`, `get_multi`, `create`, `update`, `delete`
- **Soft deletes:** `deleted_at` on `users`, `organizations`, `files` — queries filter `deleted_at IS NULL` by default
- **Env validation:** `pydantic-settings` validates all required vars at startup; app refuses to start if misconfigured

### Stats Module

Python client in `services/stats.py` wraps InfluxDB writes:

```python
stats.inc("org1.req.n", 1)
stats.avg("org1.success.ms", 1000)
stats.set("org1.member_count", 10)
stats.max("org1.success.ms_max", 2000)
```

- Called from route handlers and services (not exposed as an HTTP API)
- Grafana provisioned with a starter dashboard on boot
- InfluxDB data source auto-configured via Grafana provisioning files

### Feature Flags

`flags.yml` is the source of truth for which flags exist and their defaults:

```yaml
flags:
  new_dashboard: false
  beta_exports: false
```

`services/flags.py` exposes `is_enabled(org_id, flag_name)`:
1. Check `feature_flag_overrides` table for org-level override
2. Fall back to `flags.yml` default

Admin API for managing per-org overrides: `PATCH /api/v1/orgs/{org_id}/flags/{flag_name}`

### Email Notifications

`services/email.py` — SMTP client with Jinja2 template rendering:

```python
await email.send(to="user@example.com", template="invite", context={...})
```

Templates: `invite.html`, `welcome.html`, `password_reset.html`

Invitation email contains a plain link to `{FRONTEND_URL}/invitations` — no tokens in the URL.

---

## Frontend

### Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx               # Root layout, ThemeProvider, Toaster
│   │   ├── page.tsx                 # Redirects to /dashboard or /auth/login
│   │   ├── error.tsx                # Global error boundary
│   │   ├── auth/
│   │   │   ├── login/page.tsx
│   │   │   └── signup/page.tsx
│   │   ├── dashboard/page.tsx
│   │   ├── orgs/
│   │   │   ├── new/page.tsx
│   │   │   └── [orgId]/
│   │   │       ├── page.tsx
│   │   │       ├── members/page.tsx
│   │   │       └── settings/page.tsx
│   │   └── invitations/page.tsx
│   ├── components/
│   │   ├── ui/                      # Raw shadcn/ui components (do not edit)
│   │   └── shared/
│   │       ├── Navbar.tsx
│   │       ├── OrgSwitcher.tsx
│   │       └── InvitationCard.tsx
│   ├── services/
│   │   ├── api.ts                   # Axios instance; 401 interceptor → auto-logout
│   │   ├── auth.ts
│   │   ├── orgs.ts
│   │   ├── invitations.ts
│   │   └── files.ts
│   ├── store/
│   │   ├── auth.ts                  # Zustand: user, token, login(), logout()
│   │   └── org.ts                   # Zustand: activeOrg, setActiveOrg()
│   ├── queries/                     # TanStack Query hooks
│   │   ├── auth.ts                  # useMe()
│   │   ├── orgs.ts                  # useOrgs(), useOrgMembers()
│   │   ├── invitations.ts           # useInvitations(), useAcceptInvitation()
│   │   └── files.ts
│   ├── hooks/
│   │   ├── useAuth.ts               # Reads from Zustand auth store
│   │   └── useOrg.ts                # Reads from Zustand org store
│   ├── types/
│   │   └── api.ts                   # Auto-generated by openapi-typescript from FastAPI schema
│   ├── constants/
│   │   ├── routes.ts                # ROUTES.dashboard, ROUTES.orgs.list, etc.
│   │   ├── queryKeys.ts             # TanStack Query key constants
│   │   └── roles.ts                 # Role enum: OWNER | ADMIN | MEMBER
│   └── lib/
│       └── utils.ts                 # cn() Tailwind merge helper
├── middleware.ts                    # Next.js edge middleware — auth guard, redirect logic
├── Dockerfile
├── tailwind.config.ts
├── next.config.mjs
├── components.json                  # shadcn/ui config
└── package.json
```

### Key Patterns

**Auth guard:** `middleware.ts` intercepts all requests. Unauthenticated users hitting protected routes are redirected to `/auth/login?redirect=<path>`. After login, redirected back.

**Invitation flow:** User clicks email link → `/invitations`. If not logged in, `middleware.ts` redirects to `/auth/login?redirect=/invitations`. After login/signup, redirected to `/invitations` where pending invites are shown. User accepts/declines manually.

**Type safety:** `make generate-types` runs `openapi-typescript` against the running backend to regenerate `types/api.ts`. All service functions use these generated types.

**Forms:** React Hook Form + Zod schemas. Zod types derived from generated API types where possible.

**Toasts:** shadcn `Toaster` mounted in root layout. TanStack Query mutation callbacks trigger toasts on success/error.

**Dark mode:** `next-themes` ThemeProvider in root layout. Toggle component in Navbar.

---

## Linting & Formatting

| Tool | Scope | Runs |
|---|---|---|
| `ruff` | Backend lint + format | pre-commit, CI |
| ESLint | Frontend lint | pre-commit, CI |
| Prettier + `prettier-plugin-tailwindcss` | Frontend format | pre-commit, CI |

Pre-commit hooks configured via `.pre-commit-config.yaml`.

---

## Testing

**Backend:** `pytest` + `httpx` (async test client) + `Factory Boy` + `Faker`
- Isolated test DB spun up in Docker
- `conftest.py` provides session-scoped DB, per-test transaction rollback
- `factories.py`: `UserFactory`, `OrgFactory`, `InvitationFactory`

**Frontend:** `Jest` + React Testing Library
- Unit tests for hooks, stores, utility functions
- Integration tests for key pages

**CI:** GitHub Actions workflow on every PR push:
1. Backend: `ruff check` → `pytest`
2. Frontend: `eslint` → `prettier --check` → `jest`

---

## Dev Experience

**Makefile commands:**

| Command | Action |
|---|---|
| `make up` | Start all Docker services |
| `make down` | Stop all services |
| `make migrate` | Run Alembic migrations |
| `make seed` | Run `seed.py` to populate dev data |
| `make test` | Run backend + frontend tests |
| `make lint` | Run ruff + eslint + prettier |
| `make generate-types` | Regenerate `types/api.ts` from FastAPI OpenAPI schema |
| `make shell` | Open backend Python shell |

**Seed data (`seed.py`):** Creates 2 users, 1 org, assigns roles, creates a pending invitation — enough to develop against immediately.

**Hot reload:** Backend and frontend source directories mounted as Docker volumes. Changes reflect without container rebuilds.

---

## Environment Variables

All defined in `.env.example`. `pydantic-settings` validates presence at startup.

Key groups:
- Database: `POSTGRES_*`
- Auth: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- Email: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`
- InfluxDB: `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET`
- MinIO: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`
- Redis: `REDIS_URL`
- Frontend: `NEXT_PUBLIC_API_URL`
