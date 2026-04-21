# Project Overview
You are an expert full-stack developer. Your task is to generate a production-ready, full-stack boilerplate template. This template will be used to clone and build future AI-assisted web applications. 

The stack is strictly defined as:
* **Frontend:** Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui.
* **Backend:** FastAPI (Python 3.11+), SQLModel, Pydantic.
* **Database:** PostgreSQL.
* **Infrastructure:** Docker & Docker Compose.

You must follow industry-standard folder structures and write clean, strongly-typed, fully documented code.

---

## 1. Infrastructure & Docker (Do this first)
Create a root directory structure that separates the frontend and backend. Tie them together using a `docker-compose.yml` file at the root.

* **Root Files:** `.gitignore`, `README.md`, `docker-compose.yml`, `.env.example`.
* **Services in Docker Compose:**
    * `db`: PostgreSQL 16 image. Expose port 5432. Include health checks.
    * `backend`: Build from `./backend/Dockerfile`. Expose port 8000. Depends on `db`.
    * `frontend`: Build from `./frontend/Dockerfile`. Expose port 3000. Depends on `backend`.
* **Networking:** Ensure the frontend container can communicate with the backend container via `http://backend:8000` internally, while exposing `localhost:8000` to the host machine.

---

## 2. Frontend Specifications (Next.js)
Initialize a Next.js project inside the `./frontend` directory. 

**Configuration:**
* Use App Router (`src/app`).
* Use TypeScript (`tsconfig.json` with strict mode enabled).
* Configure Tailwind CSS (`tailwind.config.ts`, `globals.css`).
* Configure ESLint and Prettier. Ensure Prettier auto-formats Tailwind classes using `prettier-plugin-tailwindcss`.

**UI & Components (shadcn/ui):**
* Initialize `shadcn/ui` configuration (`components.json`).
* **Folder Structure Rule:** * Place raw, generated shadcn components strictly in `src/components/ui/` (e.g., `button.tsx`, `dialog.tsx`).
    * Create a separate folder `src/components/shared/` for composite components that reuse the base UI library (e.g., `Navbar.tsx`, `DataTable.tsx`). Do not mix business logic components with base UI components.

**Directory Structure:**
```text
frontend/
├── src/
│   ├── app/              # Routes, pages, layouts, error handling
│   ├── components/
│   │   ├── ui/           # Base shadcn/ui components (Do not modify heavily)
│   │   └── shared/       # Composite components built from ui/ elements
│   ├── lib/              # Utility functions (e.g., utils.ts for Tailwind merge)
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API call wrappers fetching from FastAPI
│   └── types/            # Global TypeScript interfaces/types
├── Dockerfile            # Multi-stage build for Next.js
├── tailwind.config.ts
├── next.config.mjs
└── package.json
```

## 3. Backend Specifications (FastAPI)
Initialize a Python project inside the ./backend directory.

Configuration:

Use requirements.txt or pyproject.toml for dependency management.

Include: fastapi, uvicorn, sqlmodel, psycopg2-binary, pydantic-settings, alembic (for migrations), ruff (for linting and formatting).

Implement a global exception handler and CORS middleware allowing requests from http://localhost:3000.

Directory Structure:

Plaintext
backend/
├── app/
│   ├── main.py           # FastAPI application instance & routing
│   ├── api/              # API routers/endpoints (e.g., /api/v1/users)
│   ├── core/             # Config, security, database connection (config.py, db.py)
│   ├── models/           # SQLModel database models & Pydantic schemas
│   ├── services/         # Business logic (kept out of route handlers)
│   └── utils/            # Helper functions
├── alembic/              # Database migration scripts
├── Dockerfile            # Python slim-buster image setup
├── requirements.txt
└── alembic.ini


## 4. Execution Steps
Do not generate all files in a single response. Execute this prompt in the following order, waiting for my confirmation between steps:

Step 1: Generate the root .env.example and docker-compose.yml.

Step 2: Generate the frontend/Dockerfile and the complete Next.js folder structure, including configuration files (package.json, tailwind.config.ts, eslint and prettier configs, components.json).

Step 3: Generate the backend/Dockerfile and the complete FastAPI folder structure, including requirements.txt, main.py, and the database connection logic using SQLModel.

Step 4: Provide the terminal commands required to boot the entire system up from scratch.
