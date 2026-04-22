# Architecture Overview

This document provides a high-level overview of the project's architecture, data flow, and authentication model.

## Core Stack

- **Frontend:** Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui.
- **Backend:** FastAPI (Python 3.11+), SQLModel (SQLAlchemy 2.0 + Pydantic), Pydantic v2.
- **Database:** PostgreSQL 16.
- **Async Tasks:** Celery + Redis.
- **Monitoring/Observability:** InfluxDB 2 + Grafana.
- **Object Storage:** MinIO (S3-compatible).
- **Deployment:** Kamal.

## System Components

### 1. Frontend (Next.js)
The frontend is a React application built with the Next.js App Router. It uses `tanstack/react-query` for data fetching and caching, and `zustand` for client-side state management.

### 2. Backend (FastAPI)
The backend provides a RESTful API. It uses `SQLModel` for ORM, which allows for shared models between the database and the API schemas (via Pydantic).

### 3. Worker (Celery)
Background tasks (like sending emails or processing files) are handled by Celery workers, using Redis as a message broker.

### 4. Database (PostgreSQL)
The primary relational database. Migrations are managed by Alembic.

### 5. Reverse Proxy (Nginx)
In production/local-docker development, Nginx routes requests to either the frontend or the backend.

---

## Data Flow

### Request Lifecycle
1.  **Client** makes a request to `example.com`.
2.  **Nginx** receives the request:
    - Path starting with `/api` or `/docs` is routed to the **Backend (FastAPI)**.
    - Other paths are routed to the **Frontend (Next.js)**.
3.  **Backend** processes the request:
    - Validates input using Pydantic.
    - Interacts with **PostgreSQL** via SQLModel.
    - If needed, pushes a task to **Redis**.
4.  **Celery Worker** picks up the task from Redis and executes it.

### Observability Flow
- **Backend** sends metrics/logs to **InfluxDB**.
- **Grafana** visualizes data stored in InfluxDB.

---

## Authentication & Authorization

### Flow
1.  **User Login:** User submits credentials to `/api/v1/auth/login`.
2.  **JWT Issuance:** Backend validates credentials and returns a JSON Web Token (JWT).
3.  **Client Storage:** The frontend stores the JWT (typically in a secure cookie or local storage).
4.  **Authenticated Requests:** The frontend includes the JWT in the `Authorization: Bearer <token>` header for subsequent API calls.
5.  **Backend Validation:** FastAPI's dependency injection system (`Depends(get_current_user)`) validates the JWT and provides the user object to the route handler.

### Roles & Permissions
- **Superuser:** Can access admin-level endpoints.
- **Org Owner/Member:** Granular permissions within an organization.

---

## Folder Structure

Refer to the project-specific READMEs in `/backend` and `/frontend` for detailed directory breakdowns.
