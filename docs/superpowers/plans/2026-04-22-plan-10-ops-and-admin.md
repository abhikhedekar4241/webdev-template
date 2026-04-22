# Plan 10: Admin UI, Onboarding, Documentation, and Kamal Deployment

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the boilerplate into a production-ready SaaS template by adding global administrative controls, a multi-step user onboarding flow, structured documentation, and a robust deployment configuration using Kamal.

**Architecture:**
- **Admin:** Adds an `is_superuser` flag to `User`. A dedicated `/admin` route in the frontend provides system-wide visibility. Impersonation works by allowing a superuser to request a "short-lived" JWT for any user ID.
- **Onboarding:** A dedicated `/onboarding` route that intercepts users who haven't completed their profile or joined an organization.
- **Documentation:** MkDocs with the Material theme, served as a static site.
- **Deployment:** Kamal (formerly MRSK) for zero-downtime Docker deployments to any VPS.

---

## File Map

**New Files (Backend):**
- `backend/app/api/v1/admin.py` — Superuser-only endpoints (stats, user management)
- `backend/alembic/versions/004_add_superuser_and_onboarding.py` — Migration
- `docs/mkdocs.yml` — Documentation config
- `docs/index.md` — Documentation home

**New Files (Frontend):**
- `frontend/src/app/admin/page.tsx` — Admin dashboard
- `frontend/src/app/admin/users/page.tsx` — User management
- `frontend/src/app/onboarding/page.tsx` — Multi-step onboarding wizard
- `frontend/src/components/admin/AdminSidebar.tsx` — Navigation for admin tools

**New Files (DevOps):**
- `config/deploy.yml` — Kamal deployment configuration
- `.env.deploy` — Deployment secrets template

**Modified Files:**
- `backend/app/models/user.py` — Add `is_superuser` and `onboarding_completed_at`
- `backend/app/api/deps.py` — Add `get_current_superuser` dependency
- `backend/app/main.py` — Register admin router
- `frontend/src/middleware.ts` — Add onboarding redirect logic

---

## Task 1: Admin & Superuser Foundation (Backend)

- [ ] **Step 1: Update User Model**
    Add `is_superuser: bool = Field(default=False)` and `onboarding_completed_at: datetime | None = Field(default=None)` to `backend/app/models/user.py`.

- [ ] **Step 2: Create Migration**
    ```bash
    cd backend && alembic revision --autogenerate -m "add superuser and onboarding fields"
    ```

- [ ] **Step 3: Define `get_current_superuser` Dependency**
    In `backend/app/api/deps.py`:
    ```python
    def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="The user does not have enough privileges")
        return current_user
    ```

- [ ] **Step 4: Implement Admin Router**
    Create `backend/app/api/v1/admin.py` with endpoints for:
    - `GET /stats`: Global user count, org count, and file storage usage.
    - `GET /users`: Paginated list of all system users.
    - `POST /impersonate/{user_id}`: Issues a JWT for a target user (superuser only).

- [ ] **Step 5: Register Router**
    Add `app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])` to `backend/app/main.py`.

---

## Task 2: Admin Dashboard (Frontend)

- [ ] **Step 1: Create Admin Layout**
    Implement a layout in `frontend/src/app/admin/layout.tsx` that verifies the user's superuser status before rendering.

- [ ] **Step 2: Build Stats Overview**
    Display high-level system metrics using simple card components in `frontend/src/app/admin/page.tsx`.

- [ ] **Step 3: User Management Table**
    Create a searchable table in `frontend/src/app/admin/users/page.tsx` with actions to:
    - Toggle `is_active` status.
    - Trigger "Login As" (impersonation) which stores the new token and redirects to `/dashboard`.

---

## Task 3: Multi-Step Onboarding Flow

- [ ] **Step 1: Onboarding Wizard UI**
    Create `frontend/src/app/onboarding/page.tsx` using a state-driven multi-step form:
    - **Step 1:** Profile Setup (Full Name, Avatar).
    - **Step 2:** Organization Creation (Name, Slug).
    - **Step 3:** Optional: Invite first team member.

- [ ] **Step 4: Middleware Redirect**
    Update `frontend/src/middleware.ts` to check if `onboarding_completed_at` is null for the logged-in user. If so, redirect all non-onboarding routes to `/onboarding`.

---

## Task 4: Documentation Template

- [ ] **Step 1: Initialize MkDocs**
    Create `docs/mkdocs.yml` using the `mkdocs-material` theme. Configure navigation for "Architecture", "API Reference", and "Deployment".

- [ ] **Step 2: Build Documentation Content**
    Convert `SETUP.md` and `CONTEXT.md` into pages within the `docs/` folder (e.g., `docs/getting-started.md`).

---

## Task 5: Kamal Deployment Config

- [ ] **Step 1: Create `config/deploy.yml`**
    Define the service name, image, and server IP. Configure `accessories` for PostgreSQL, Redis, and MinIO.

- [ ] **Step 2: Add Health Checks**
    Configure Kamal's `healthcheck` to point to the backend's `/health` and the frontend's `/` route.

- [ ] **Step 3: Deployment Makefile Commands**
    Add `deploy`, `deploy-setup`, and `deploy-rollback` to the root `Makefile`.

---

## Validation Checklist

- [ ] Superuser can access `/admin` and see all users.
- [ ] Regular user receives 403 when hitting admin endpoints.
- [ ] New user is automatically redirected to `/onboarding` until they finish the steps.
- [ ] `kamal config validate` passes with the new configuration.
- [ ] `mkdocs build` generates a clean `site/` directory.
