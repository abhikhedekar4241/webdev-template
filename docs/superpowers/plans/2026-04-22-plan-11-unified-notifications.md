# Plan 11: Unified Notification System

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a centralized notification system that replaces the standalone invitations page. This system will handle unread states, multiple notification types (starting with org invitations), and inline actions.

**Architecture:**
- **Database:** A `Notification` table stores system-wide alerts for users. It uses a JSON `data` field to store type-specific information (like `org_id` or `invitation_id`).
- **Integration:** The `NotificationService` acts as a side-effect handler. When an invitation is created, a corresponding notification is issued.
- **Frontend:** A unified `/notifications` page acts as a user's inbox. The existing `/invitations` logic is merged here.

---

## Task 1: Backend Foundation (Models & Migration)

- [ ] **Step 1: Create Notification Model**
    Create `backend/app/models/notification.py`:
    - `id`: UUID
    - `user_id`: UUID (FK to users)
    - `type`: String (e.g., "org_invitation")
    - `data`: JSON (payload)
    - `read_at`: DateTime | None
    - `created_at`: DateTime

- [ ] **Step 2: Database Migration**
    Generate and apply migration `005_add_notifications_table`.

- [ ] **Step 3: Notification Service**
    Implement `backend/app/services/notifications.py` with methods for `create`, `list_for_user`, `mark_as_read`, and `delete`.

---

## Task 2: Invitation Integration

- [ ] **Step 1: Hook into Invitation Creation**
    Modify `backend/app/services/invitations.py`. When `create_invitation` is called, search for an existing user with that email. If they exist, immediately create a `Notification` for them.

- [ ] **Step 2: Sync Actions**
    Ensure that when an invitation is accepted or declined via the API, the corresponding notification is marked as read or deleted to keep the inbox clean.

---

## Task 3: Notification API Endpoints

- [ ] **Step 1: Create Admin Router**
    Create `backend/app/api/v1/notifications.py`:
    - `GET /`: List unread/all notifications.
    - `PATCH /{id}/read`: Mark as read.
    - `DELETE /{id}`: Archive/Remove notification.

- [ ] **Step 2: Register Router**
    Register in `backend/app/main.py` under `/api/v1/notifications`.

---

## Task 4: Frontend - Unified Inbox

- [ ] **Step 1: API Integration**
    Create `frontend/src/services/notifications.ts` and TanStack Query hooks in `frontend/src/queries/notifications.ts`.

- [ ] **Step 2: Notifications Page**
    Create `frontend/src/app/notifications/page.tsx`. Implement a "Type Renderer" that shows:
    - Normal alerts as text.
    - `org_invitation` alerts with "Accept" and "Decline" buttons.

- [ ] **Step 3: AppShell Integration**
    - Update the Bell icon in `AppShell.tsx` to link to `/notifications`.
    - Add an unread count badge to the Bell icon.
    - Remove "Invitations" from the sidebar and redirect the old `/invitations` route.

---

## Validation Checklist

- [ ] Sending an invitation creates a notification record in the DB.
- [ ] Notification appears on the `/notifications` page for the target user.
- [ ] Clicking "Accept" on the notification successfully joins the user to the org.
- [ ] The notification is cleared/marked as read after the action.
- [ ] Bell icon shows the correct unread count.
