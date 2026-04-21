# Boilerplate Setup Guide

Everything you need to configure when starting a new project from this template, plus a map of where things live.

---

## Quick Start (New Project Checklist)

Copy this repo, then work through the sections below in order.

---

## Step 1 — Rename the project

Replace "Boilerplate" / "boilerplate" with your project name everywhere. Run these from the repo root:

```bash
# Audit all occurrences first
grep -r "Boilerplate\|boilerplate" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.yml" --include="*.json" --include="*.env*" --include="*.conf" -l
```

Then update each file manually or with sed:

| File | What to change |
|------|----------------|
| `frontend/src/app/layout.tsx` | `title`, `description` in metadata export |
| `frontend/src/app/auth/login/page.tsx` | Logo text "Boilerplate" (×2) |
| `frontend/src/app/auth/signup/page.tsx` | Logo text "Boilerplate" (×2) |
| `frontend/src/components/shared/AppShell.tsx` | Sidebar logo text (×2) |
| `backend/app/main.py` | `title="Boilerplate API"` in FastAPI() call |
| `.env` | `POSTGRES_USER`, `POSTGRES_DB` (see Step 3) |
| `.env.example` | Same as .env |

---

## Step 2 — Configure the logo / brand icon

The logo is the `LayoutDashboard` lucide icon. Replace it with something relevant to your project.

**Locations to update** (all use the same icon):

- `frontend/src/components/shared/AppShell.tsx` — sidebar logo + mobile topbar logo (lines ~55–58 and ~164–167)
- `frontend/src/app/auth/login/page.tsx` — login page hero icon
- `frontend/src/app/auth/signup/page.tsx` — signup page hero icon

```tsx
// Current
import { LayoutDashboard } from "lucide-react";
<LayoutDashboard className="h-4 w-4 text-primary-foreground" />

// Replace with any lucide icon, e.g.:
import { Zap } from "lucide-react";
<Zap className="h-4 w-4 text-primary-foreground" />
```

**Custom favicon**: Drop a `favicon.ico` into `frontend/public/`. Next.js picks it up automatically.

**Brand color**: The primary color is CSS HSL in `frontend/src/app/globals.css`:

```css
/* Line ~13 (light mode) */
--primary: 234 89% 58%;   /* change this HSL value */

/* Line ~36 (dark mode) */
--primary: 234 89% 64%;   /* and this one */
```

---

## Step 3 — Set environment variables

Copy `.env.example` to `.env` and fill in real values. These are the ones that **must** change:

```bash
cp .env.example .env
```

### Required changes

```env
# --- Postgres ---
POSTGRES_USER=yourapp          # used as both DB user and DB name
POSTGRES_PASSWORD=strongpassword
POSTGRES_DB=yourapp

# --- Auth ---
# Generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<generate a random 64-char hex string>
ACCESS_TOKEN_EXPIRE_MINUTES=30  # adjust to taste (e.g. 1440 for 24h)

# --- Email (see Step 6) ---
SMTP_HOST=smtp.yourmailprovider.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=<your smtp password>
SMTP_FROM=noreply@yourdomain.com

# --- Frontend URL (used in invite emails etc) ---
FRONTEND_URL=https://yourdomain.com         # prod
# FRONTEND_URL=http://localhost:3000        # dev

# --- CORS ---
CORS_ORIGINS=["https://yourdomain.com"]
# dev: CORS_ORIGINS=["http://localhost:3000","http://localhost"]

# --- Next.js (only NEXT_PUBLIC_ vars are exposed to the browser) ---
NEXT_PUBLIC_API_URL=https://yourdomain.com  # prod (no trailing /api)
# NEXT_PUBLIC_API_URL=http://localhost      # dev
```

### Services you can leave as-is for dev

```env
# Redis — fine as default for dev
REDIS_URL=redis://redis:6379/0

# MinIO (local S3) — change bucket name to match your domain/project
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=uploads           # rename to e.g. "myapp-uploads"

# InfluxDB (metrics) — rename org/bucket to match your project
INFLUXDB_ORG=myorg             # rename e.g. "myapp"
INFLUXDB_BUCKET=metrics
INFLUXDB_TOKEN=my-super-secret-admin-token   # change in prod

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=changeme      # change in prod
```

---

## Step 4 — Update seed data

`backend/seed.py` creates dev users and a sample org. Update it to reflect your project:

```python
# backend/seed.py — change these values
admin = auth_service.create_user(
    session,
    email="admin@yourproject.com",   # ← your dev email
    password="devpassword123",
    full_name="Admin User",
)
# ... etc
org = org_service.create_org(
    session, name="My App", slug="my-app", created_by=admin.id
)
```

Re-seed after changing: `docker compose exec backend python seed.py`

---

## Step 5 — Add your own pages / nav items

The sidebar nav is defined in `frontend/src/components/shared/AppShell.tsx`:

```typescript
// Top nav items — main app pages
const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/users",     label: "Users",     icon: Users },
  { href: "/documents", label: "Documents", icon: FileText },
  // add your pages here
];

// Bottom nav items — system/admin pages
const bottomItems = [
  { href: ROUTES.orgs.list,    label: "Organizations", icon: Building2 },
  { href: ROUTES.invitations,  label: "Invitations",   icon: Mail },
  { href: "/settings",         label: "Settings",      icon: Settings },
];
```

Routes are centralised in `frontend/src/constants/routes.ts` — add new routes there.

---

## Step 6 — Wire up real email sending

The email service at `backend/app/services/email.py` currently only logs. To send real emails:

```python
# backend/app/services/email.py
# Replace the log-only send() with actual SMTP or a provider SDK (Resend, SendGrid, etc.)

import smtplib
from email.mime.text import MIMEText

class EmailService:
    def send(self, to: str, subject: str, template: str, context: dict) -> None:
        html = self._render(template, context)
        msg = MIMEText(html, "html")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
            s.starttls()
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)
```

Email templates live in `backend/app/emails/templates/`. Currently: `invite.html`. Add more as Jinja2 HTML files.

---

## Step 7 — Add background jobs (optional)

Tasks are defined in `backend/app/jobs/`. Currently contains example tasks in `examples.py`.

1. Create a new file: `backend/app/jobs/your_feature.py`
2. Register it in `backend/app/worker.py`:
   ```python
   celery_app = Celery(
       "worker",
       include=["app.jobs.examples", "app.jobs.your_feature"],  # add here
   )
   ```
3. For scheduled (periodic) tasks, add a beat schedule:
   ```python
   celery_app.conf.beat_schedule = {
       "cleanup-every-hour": {
           "task": "app.jobs.your_feature.cleanup_task",
           "schedule": 3600.0,
       },
   }
   ```
   Then run the beat scheduler: `docker compose exec worker celery -A app.worker beat`

---

## Step 8 — Production deployment

Before going to prod, also:

1. **Change all `changeme` passwords** in `.env` — Postgres, MinIO, InfluxDB, Grafana
2. **Rotate `SECRET_KEY`** — invalidates all existing JWTs
3. **Set `FRONTEND_URL`** to your real domain (used in invite email links)
4. **Update `CORS_ORIGINS`** to your real domain only
5. **Update nginx config** (`nginx/nginx.conf`) — add `server_name yourdomain.com;`
6. **Remove seed data** from prod — don't run `seed.py` in production
7. **Set `NEXT_PUBLIC_API_URL`** to your real domain (no `/api` suffix — paths include it)

---

## Codebase Map — Where Things Live

### Backend (`backend/`)

```
app/
├── api/
│   ├── deps.py              # Auth dependency (get_current_user)
│   └── v1/
│       ├── auth.py          # POST /login, /register, GET /me
│       ├── orgs.py          # CRUD for organizations + members
│       ├── invitations.py   # Invite flow
│       └── files.py         # File upload/download (MinIO)
├── core/
│   ├── config.py            # All settings (reads from env)
│   ├── db.py                # SQLModel session + engine setup
│   └── security.py          # JWT creation/verification, password hashing
├── emails/
│   └── templates/           # Jinja2 HTML email templates
├── jobs/
│   └── examples.py          # Celery task examples
├── models/
│   ├── user.py              # User SQLModel
│   ├── org.py               # Organization + OrgMembership SQLModels
│   ├── invitation.py        # OrgInvitation SQLModel
│   └── file.py              # FileRecord SQLModel
├── services/
│   ├── auth.py              # User creation, authentication logic
│   ├── orgs.py              # Org CRUD business logic
│   ├── invitations.py       # Invitation lifecycle logic
│   ├── files.py             # MinIO upload/download logic
│   └── email.py             # Email sending (implement real SMTP here)
├── main.py                  # FastAPI app, router registration, CORS
└── worker.py                # Celery app config

alembic/
└── versions/                # Database migrations (run in order: 000 → 001 → ...)

seed.py                      # Dev seed data (not for prod)
tests/                       # pytest test suite
```

**Adding a new feature (backend pattern):**
1. Add model to `app/models/your_feature.py`
2. Create migration: `alembic revision --autogenerate -m "add_your_feature"`
3. Add service to `app/services/your_feature.py`
4. Add router to `app/api/v1/your_feature.py`
5. Register router in `app/main.py`
6. Write tests in `tests/test_your_feature.py`

---

### Frontend (`frontend/src/`)

```
app/
├── layout.tsx               # Root layout — metadata title/description, ThemeProvider
├── globals.css              # Tailwind base styles + CSS variables (colors here)
├── auth/
│   ├── login/page.tsx       # Login form
│   └── signup/page.tsx      # Register form
├── dashboard/page.tsx       # Main dashboard (stat cards, chart, activity feed)
├── orgs/                    # Organization pages
│   ├── layout.tsx           # Wraps all org pages in AppShell
│   ├── page.tsx             # Org list
│   ├── new/page.tsx         # Create org form
│   └── [orgId]/
│       ├── page.tsx         # Org detail / settings
│       ├── members/page.tsx # Members list + role management
│       └── settings/page.tsx
└── invitations/page.tsx     # Pending invitations for current user

components/
├── shared/
│   └── AppShell.tsx         # Sidebar + topbar layout shell
└── ui/                      # shadcn/ui primitives (Badge, Button, etc.)

constants/
├── queryKeys.ts             # TanStack Query key factory (add new keys here)
└── routes.ts                # Centralised route strings (add new routes here)

hooks/
└── useOrg.ts                # Active org from Zustand store

lib/
├── apiError.ts              # Extract error detail from Axios errors
└── utils.ts                 # cn() helper (clsx + tailwind-merge)

queries/                     # TanStack Query hooks (data fetching + mutations)
├── auth.ts                  # useMe, useLogin, useLogout, useRegister
├── orgs.ts                  # useOrgs, useOrg, useCreateOrg, useOrgMembers, etc.
├── invitations.ts           # useInvitations, useCreateInvitation, etc.
└── files.ts                 # useUploadFile, useFiles

services/                    # Raw Axios API calls (no React)
├── api.ts                   # Axios instance (base URL from NEXT_PUBLIC_API_URL)
├── auth.ts                  # login(), register(), me(), logout()
├── orgs.ts                  # list(), get(), create(), update(), etc.
├── invitations.ts           # list(), create(), accept(), decline()
└── files.ts                 # upload(), list(), download(), delete()

store/
└── org.ts                   # Zustand store — activeOrg, persisted to localStorage
```

**Adding a new feature (frontend pattern):**
1. Add service to `services/your_feature.ts` (raw Axios calls)
2. Add query keys to `constants/queryKeys.ts`
3. Add hooks to `queries/your_feature.ts` (useQuery / useMutation wrappers)
4. Add route to `constants/routes.ts`
5. Create page at `app/your-feature/page.tsx`
6. Add nav item to `components/shared/AppShell.tsx` if needed

---

### Infrastructure

```
docker-compose.yml           # All services: db, redis, backend, worker, frontend, nginx, minio, influxdb, grafana
nginx/nginx.conf             # Reverse proxy — routes / → frontend:3000, /api → backend:8000
.env                         # All secrets + config (never commit this)
.env.example                 # Template for .env (safe to commit, no real secrets)
```

**Service ports (dev):**

| Service | URL |
|---------|-----|
| App (via nginx) | http://localhost |
| Frontend direct | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| MinIO console | http://localhost:9001 |
| Grafana | http://localhost:3001 |
| InfluxDB | http://localhost:8086 |

---

### Database migrations

```bash
# Create a new migration after changing a model
docker compose exec backend alembic revision --autogenerate -m "describe_your_change"

# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Roll back one migration
docker compose exec backend alembic downgrade -1

# Migration files live in:
backend/alembic/versions/    # numbered 000_, 001_, 002_, ...
```

---

### Running tests

```bash
# All tests
docker compose exec backend pytest

# Single file
docker compose exec backend pytest tests/test_orgs.py -v

# Single test
docker compose exec backend pytest tests/test_orgs.py::test_create_org -v
```

Tests use an in-memory SQLite database (configured in `backend/tests/conftest.py`) so they don't touch the dev Postgres instance.
