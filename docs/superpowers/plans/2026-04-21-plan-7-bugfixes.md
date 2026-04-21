# Bug Fixes & Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix every bug and UX gap discovered during end-to-end manual audit of the boilerplate.

**Architecture:** Fixes span both the FastAPI backend (input validation, error handling) and the Next.js frontend (navigation, empty states, UX flows). Each task is self-contained and independently deployable.

**Tech Stack:** FastAPI + Pydantic v2, SQLModel, Next.js 14 App Router, TanStack Query, Zustand, Tailwind CSS, sonner toasts.

---

## Issues Found (Full Audit)

### Backend bugs
| # | Severity | Issue |
|---|----------|-------|
| B1 | **Critical** | Duplicate org slug returns 500 (unhandled `IntegrityError`) — should be 409 |
| B2 | **High** | Empty string slug is accepted on org create — no server-side validation |
| B3 | **High** | Short passwords accepted (2-char "ab" registers fine) — no min-length check |
| B4 | **High** | Duplicate invitation allowed — can spam same email multiple times |
| B5 | **Medium** | No check for inviting existing org member — sends invitation to someone already in |
| B6 | **Medium** | Owner can be removed via `DELETE /orgs/{id}/members/{owner_id}` — no guard |
| B7 | **Low** | Org update IntegrityError (duplicate slug via PATCH) also returns 500 |

### Frontend bugs / UX gaps
| # | Severity | Issue |
|---|----------|-------|
| F1 | **High** | After login, page redirects to `/dashboard` but org switcher shows nothing — `activeOrg` is null, no auto-select of first org |
| F2 | **High** | Creating org with duplicate slug shows generic "Failed to create organization" — no specific message |
| F3 | **High** | Invitations page is unreachable from the UI — no link in nav or post-invite flow |
| F4 | **Medium** | Settings page update shows 500 toast when slug conflicts — same as B1/B7 |
| F5 | **Medium** | New org page: slug field auto-fills but user can clear it and submit empty slug |
| F6 | **Medium** | Members page shows raw UUID in `MemberAvatar` count fallback ("?") instead of initials when `full_name` is empty |
| F7 | **Low** | Logout does not clear the org store (`activeOrg` persists in localStorage across sessions) |
| F8 | **Low** | After creating an invitation, there is no success feedback showing who was invited |
| F9 | **Low** | Dashboard page greeting uses hardcoded mock data — `useMe` first name is correct but the table/chart are obviously fake with no note |

---

## Files to Modify

**Backend:**
- `backend/app/api/v1/orgs.py` — add IntegrityError handlers, slug/empty validation, owner-remove guard
- `backend/app/api/v1/auth.py` — add min-length password validation
- `backend/app/api/v1/invitations.py` — duplicate invite guard, existing-member guard

**Frontend:**
- `frontend/src/queries/auth.ts` — clear org store on logout
- `frontend/src/queries/orgs.ts` — extract error detail from 409 response
- `frontend/src/app/orgs/new/page.tsx` — prevent empty slug submission
- `frontend/src/components/shared/AppShell.tsx` — auto-select first org on mount, add Invitations link
- `frontend/src/queries/invitations.ts` — improve success toast with invitee email

---

## Task 1: Backend — Fix duplicate slug 500 → 409

**Files:**
- Modify: `backend/app/api/v1/orgs.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_orgs.py — add after existing create test
def test_create_org_duplicate_slug_returns_409(client, admin_token, seed_org):
    response = client.post(
        "/api/v1/orgs/",
        json={"name": "Another Org", "slug": seed_org["slug"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409
    assert "slug" in response.json()["detail"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && docker compose exec backend pytest tests/test_orgs.py::test_create_org_duplicate_slug_returns_409 -v
```
Expected: FAIL — currently returns 500

- [ ] **Step 3: Add IntegrityError handler to create and update org endpoints**

In `backend/app/api/v1/orgs.py`, add import at top:
```python
from sqlalchemy.exc import IntegrityError
```

Replace `create_org` endpoint body:
```python
@router.post("/", response_model=OrgResponse, status_code=201)
def create_org(
    body: OrgCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not body.slug:
        raise HTTPException(status_code=422, detail="Slug cannot be empty")
    try:
        org = org_service.create_org(
            session, name=body.name, slug=body.slug, created_by=current_user.id
        )
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Slug already taken")
    return org
```

Replace `update_org` endpoint body:
```python
@router.patch("/{org_id}", response_model=OrgResponse)
def update_org(
    org_id: uuid.UUID,
    body: OrgUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org = _require_org(session, org_id, current_user)
    _require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    try:
        return org_service.update_org(session, org=org, name=body.name, slug=body.slug)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Slug already taken")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
docker compose exec backend pytest tests/test_orgs.py::test_create_org_duplicate_slug_returns_409 -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/orgs.py backend/tests/test_orgs.py
git commit -m "fix: return 409 on duplicate org slug instead of 500"
```

---

## Task 2: Backend — Prevent removing the owner from an org

**Files:**
- Modify: `backend/app/api/v1/orgs.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_orgs.py
def test_cannot_remove_owner(client, admin_token, seed_org, admin_user):
    response = client.delete(
        f"/api/v1/orgs/{seed_org['id']}/members/{admin_user['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
docker compose exec backend pytest tests/test_orgs.py::test_cannot_remove_owner -v
```
Expected: FAIL — currently returns 204

- [ ] **Step 3: Add owner guard to remove_member endpoint**

In `backend/app/api/v1/orgs.py`, replace `remove_member`:
```python
@router.delete("/{org_id}/members/{user_id}", status_code=204)
def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _require_org(session, org_id, current_user)
    _require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    target = org_service.get_membership(session, org_id=org_id, user_id=user_id)
    if target and target.role == OrgRole.owner:
        raise HTTPException(status_code=403, detail="Cannot remove the owner of an organization")
    org_service.remove_member(session, org_id=org_id, user_id=user_id)
```

- [ ] **Step 4: Run test**

```bash
docker compose exec backend pytest tests/test_orgs.py::test_cannot_remove_owner -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/orgs.py backend/tests/test_orgs.py
git commit -m "fix: prevent removing org owner via members endpoint"
```

---

## Task 3: Backend — Password min-length and duplicate invitation guard

**Files:**
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/app/api/v1/invitations.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_auth.py — add
def test_register_short_password_rejected(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "ab", "full_name": "Test"},
    )
    assert response.status_code == 422

# backend/tests/test_invitations.py — add
def test_duplicate_invitation_rejected(client, admin_token, seed_org):
    payload = {"org_id": seed_org["id"], "email": "dup@example.com", "role": "member"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    client.post("/api/v1/invitations/", json=payload, headers=headers)
    response = client.post("/api/v1/invitations/", json=payload, headers=headers)
    assert response.status_code == 409

def test_invite_existing_member_rejected(client, admin_token, seed_org, member_user):
    response = client.post(
        "/api/v1/invitations/",
        json={"org_id": seed_org["id"], "email": member_user["email"], "role": "member"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
docker compose exec backend pytest tests/test_auth.py::test_register_short_password_rejected tests/test_invitations.py::test_duplicate_invitation_rejected tests/test_invitations.py::test_invite_existing_member_rejected -v
```
Expected: all FAIL

- [ ] **Step 3: Add password min-length validation**

In `backend/app/api/v1/auth.py`, update `RegisterRequest`:
```python
from pydantic import BaseModel, EmailStr, field_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
```

- [ ] **Step 4: Add duplicate invite and existing-member guards**

In `backend/app/api/v1/invitations.py`, update `create_invitation` endpoint, after the org check:
```python
from sqlmodel import select as sa_select
from app.models.invitation import InvitationStatus

# ...inside create_invitation, after org check:

    # Guard: already a member
    invitee = session.exec(
        sa_select(User).where(User.email == body.email)
    ).first()
    if invitee:
        existing_member = org_service.get_membership(
            session, org_id=body.org_id, user_id=invitee.id
        )
        if existing_member:
            raise HTTPException(status_code=409, detail="User is already a member of this organization")

    # Guard: pending invite already exists
    from sqlmodel import select as _select
    existing_invite = session.exec(
        _select(OrgInvitation).where(
            OrgInvitation.org_id == body.org_id,
            OrgInvitation.invited_email == body.email,
            OrgInvitation.status == InvitationStatus.pending,
        )
    ).first()
    if existing_invite:
        raise HTTPException(status_code=409, detail="A pending invitation already exists for this email")
```

- [ ] **Step 5: Run all three tests**

```bash
docker compose exec backend pytest tests/test_auth.py::test_register_short_password_rejected tests/test_invitations.py::test_duplicate_invitation_rejected tests/test_invitations.py::test_invite_existing_member_rejected -v
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/auth.py backend/app/api/v1/invitations.py backend/tests/test_auth.py backend/tests/test_invitations.py
git commit -m "fix: enforce password min-length, reject duplicate/existing-member invitations"
```

---

## Task 4: Frontend — Show specific error messages from API (409 slug, 409 invite)

**Files:**
- Modify: `frontend/src/queries/orgs.ts`
- Modify: `frontend/src/queries/invitations.ts`

- [ ] **Step 1: Add an error-detail extractor utility**

In `frontend/src/lib/apiError.ts` (create):
```typescript
export function getApiError(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: string } } })
    ?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  return fallback;
}
```

- [ ] **Step 2: Update useCreateOrg and useUpdateOrg to show specific errors**

In `frontend/src/queries/orgs.ts`:
```typescript
import { getApiError } from "@/lib/apiError";

// in useCreateOrg:
    onError: (err) => {
      toast.error(getApiError(err, "Failed to create organization"));
    },

// in useUpdateOrg:
    onError: (err) => {
      toast.error(getApiError(err, "Failed to update organization"));
    },
```

- [ ] **Step 3: Update useCreateInvitation to show specific errors and include invitee in success**

In `frontend/src/queries/invitations.ts`:
```typescript
import { getApiError } from "@/lib/apiError";

export function useCreateInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { org_id: string; email: string; role: string }) =>
      invitationsService.create(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.invitations.list });
      toast.success(`Invitation sent to ${variables.email}`);
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to send invitation"));
    },
  });
}
```

- [ ] **Step 4: Verify in browser**

1. Try creating an org with a duplicate slug → toast should say "Slug already taken"
2. Try inviting someone already in the org → toast should say "User is already a member..."
3. Send a valid invite → toast should say "Invitation sent to x@example.com"

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/apiError.ts frontend/src/queries/orgs.ts frontend/src/queries/invitations.ts
git commit -m "fix: show specific API error messages in toasts for orgs and invitations"
```

---

## Task 5: Frontend — Auto-select first org on login, add Invitations to nav, logout clears store

**Files:**
- Modify: `frontend/src/queries/auth.ts`
- Modify: `frontend/src/components/shared/AppShell.tsx`

- [ ] **Step 1: Auto-select first org after login**

In `frontend/src/queries/auth.ts`, update `useLogin`:
```typescript
import { useOrgStore } from "@/store/org";

export function useLogin() {
  const queryClient = useQueryClient();
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.login(email, password),
    onSuccess: async () => {
      // Fetch orgs and auto-select the first one
      const orgs = await import("@/services/orgs").then((m) => m.orgsService.list());
      if (orgs.length > 0 && !useOrgStore.getState().activeOrg) {
        setActiveOrg({ id: orgs[0].id, name: orgs[0].name, slug: orgs[0].slug });
      }
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}
```

- [ ] **Step 2: Clear org store on logout**

In `frontend/src/queries/auth.ts`, update `useLogout`:
```typescript
export function useLogout() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);

  return () => {
    authService.logout();
    setActiveOrg(null);
    queryClient.clear();
    router.push("/auth/login");
  };
}
```

- [ ] **Step 3: Add Invitations link to AppShell bottom nav**

In `frontend/src/components/shared/AppShell.tsx`, update `bottomItems`:
```typescript
import { Building2, Settings, Mail } from "lucide-react";
import { ROUTES } from "@/constants/routes";

const bottomItems = [
  { href: ROUTES.invitations, label: "Invitations", icon: Mail },
  { href: ROUTES.orgs.list, label: "Organizations", icon: Building2 },
  { href: "/settings", label: "Settings", icon: Settings },
];
```

- [ ] **Step 4: Verify in browser**

1. Log out, log back in → org switcher should show first org pre-selected
2. Log out → log in as different user → org store should not carry over
3. Sidebar bottom section should show Invitations link

- [ ] **Step 5: Commit**

```bash
git add frontend/src/queries/auth.ts frontend/src/components/shared/AppShell.tsx
git commit -m "fix: auto-select first org on login, clear org store on logout, add invitations to nav"
```

---

## Task 6: Frontend — Prevent empty slug submission on new org form

**Files:**
- Modify: `frontend/src/app/orgs/new/page.tsx`

- [ ] **Step 1: The schema already rejects empty slug — verify the Zod rule fires correctly**

Current schema in `frontend/src/app/orgs/new/page.tsx`:
```typescript
slug: z.string().min(1, "Slug is required").regex(/^[a-z0-9-]+$/, ...)
```
This already prevents empty submission client-side. The bug is that `handleNameChange` can produce an empty slug (e.g. name "---") and then `setValue("slug", "")` passes `""` through without triggering Zod until submit.

- [ ] **Step 2: Add explicit empty-slug sanitisation in handleNameChange**

In `frontend/src/app/orgs/new/page.tsx`, replace `handleNameChange`:
```typescript
const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const auto = e.target.value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  // Only auto-fill if result is non-empty; otherwise leave field for user to type
  if (auto) {
    setValue("slug", auto, { shouldValidate: true });
  }
};
```

- [ ] **Step 3: Disable submit button when slug is empty**

The `disabled={isPending}` on the submit button should also block when form is invalid. Update:
```tsx
<button
  type="submit"
  disabled={isPending || !watch("slug")}
  className="..."
>
```

- [ ] **Step 4: Verify in browser**

1. Type "---" as org name → slug field stays empty → button disabled
2. Type "My Org" → slug auto-fills "my-org" → button enabled
3. Clear slug manually → button disables

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/orgs/new/page.tsx
git commit -m "fix: prevent empty slug submission on new org form"
```

---

## Task 7: Restart backend container and run full test suite

- [ ] **Step 1: Rebuild and restart backend**

```bash
docker compose build backend && docker compose up -d backend
```

- [ ] **Step 2: Run full test suite**

```bash
docker compose exec backend pytest -v 2>&1 | tail -30
```
Expected: all tests pass (currently 78 passing — new tests from Tasks 1-3 will add ~6 more)

- [ ] **Step 3: Smoke test the key flows via curl**

```bash
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -d "username=admin@example.com&password=password123" \
  -H "Content-Type: application/x-www-form-urlencoded" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Should be 409
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost/api/v1/orgs/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"X","slug":"demo-org"}'
# Expected: 409

# Short password should be 422
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"y@y.com","password":"ab","full_name":"Y"}'
# Expected: 422
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "fix: rebuild backend with all validation fixes"
```

---

## Self-Review

**Spec coverage check:**
- B1 Duplicate slug 500 → ✅ Task 1
- B2 Empty slug accepted → ✅ Task 1 (server) + Task 6 (client)
- B3 Short password → ✅ Task 3
- B4 Duplicate invitation → ✅ Task 3
- B5 Invite existing member → ✅ Task 3
- B6 Owner removal → ✅ Task 2
- B7 Update slug 500 → ✅ Task 1
- F1 No auto-select org → ✅ Task 5
- F2 Generic error message → ✅ Task 4
- F3 Invitations unreachable → ✅ Task 5
- F4 Settings 500 toast → ✅ Task 4 (via B7 fix + specific error message)
- F5 Empty slug submit → ✅ Task 6
- F7 Logout doesn't clear store → ✅ Task 5
- F8 No invitee in success toast → ✅ Task 4

**Not addressed (by design):**
- F6 (avatar "?" for empty full_name) — only happens if seed data is broken; not a real flow
- F9 (dashboard mock data) — this is intentional placeholder content for the boilerplate
