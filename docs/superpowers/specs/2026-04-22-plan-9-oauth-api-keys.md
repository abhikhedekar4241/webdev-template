# Plan 9: Google OAuth + Org API Keys

## Goal

Add Google OAuth login (auto-linking existing accounts by email) and org-scoped API keys (opaque token, SHA-256 hash, revocable) so users can sign in without a password and integrate programmatically.

## Architecture

OAuth is backend-driven: FastAPI handles the Google redirect and callback, issues a JWT, and redirects to the frontend `/auth/callback` page which stores the token and navigates to the dashboard. API keys are opaque `sk_live_` tokens whose SHA-256 hash is stored in the DB; the existing `get_current_user` dep handles them transparently alongside JWTs, so all existing endpoints work with API keys without modification.

## Tech Stack

- **authlib** — OAuth client library for FastAPI
- **httpx** — async HTTP client (already in stack, used by authlib)
- **hashlib** (stdlib) — SHA-256 hashing for API keys
- **secrets** (stdlib) — cryptographically secure token generation

---

## Data Model

### New table: `user_oauth_accounts`

Separate table (not a column on `users`) so additional providers can be added without schema changes.

```
id            UUID PK
user_id       UUID FK → users.id, index
provider      str  ("google")
provider_user_id  str  (Google's stable user ID, index)
provider_email    str
created_at    datetime
```

Unique constraint on `(provider, provider_user_id)`.

### New table: `org_api_keys`

```
id            UUID PK
org_id        UUID FK → organizations.id, index
name          str  (human label, e.g. "CI/CD key")
key_hash      str  (sha256 hex of full key, unique)
key_prefix    str  (first 10 chars of key, for display only)
created_by    UUID FK → users.id
last_used_at  datetime | None
expires_at    datetime | None
revoked_at    datetime | None
created_at    datetime
```

### Change: `users.hashed_password` → `str | None`

Google-only users have no password. Migration sets existing rows' `hashed_password` to non-null (they already have values); new column is nullable going forward.

---

## Backend

### Config additions (`core/config.py`)

```
GOOGLE_CLIENT_ID: str | None = None
GOOGLE_CLIENT_SECRET: str | None = None
```

Optional — OAuth endpoints return 501 if not configured.

### New model files

- `app/models/oauth_account.py` — `UserOAuthAccount`
- `app/models/api_key.py` — `OrgApiKey`

### New migration

`003_add_oauth_and_api_keys.py` chained after current head:
- Alter `users.hashed_password` to nullable
- Create `user_oauth_accounts` with unique constraint
- Create `org_api_keys`

### OAuth endpoints (added to `app/api/v1/auth.py`)

**`GET /api/v1/auth/google`**
- Builds Google authorization URL (scopes: `openid email profile`)
- Sets a short-lived `oauth_state` cookie for CSRF protection
- Returns HTTP 302 redirect to Google

**`GET /api/v1/auth/google/callback`**
- Validates `state` against cookie
- Exchanges `code` for tokens via Google
- Fetches user info (`sub`, `email`, `name`)
- Lookup order:
  1. Find `UserOAuthAccount` by `(provider="google", provider_user_id=sub)` → get user
  2. Else find `User` by email → auto-link (create `UserOAuthAccount`, mark user verified)
  3. Else create new `User` (no password, `is_verified=True`) + `UserOAuthAccount`
- Issues JWT via `create_access_token`
- Redirects to `{FRONTEND_URL}/auth/callback?token={jwt}`

### API key service (`app/services/api_keys.py`)

```python
class ApiKeyService:
    def create(session, *, org_id, name, created_by) -> tuple[OrgApiKey, str]:
        # generates sk_live_{secrets.token_hex(32)}
        # stores sha256 hash + first 10 chars as prefix
        # returns (record, full_key) — caller must surface key to user immediately

    def list(session, *, org_id) -> list[OrgApiKey]:
        # returns non-revoked keys ordered by created_at desc

    def revoke(session, *, key_id, org_id) -> bool:
        # sets revoked_at, returns False if not found or wrong org

    def authenticate(session, *, raw_key) -> OrgApiKey | None:
        # hashes raw_key, looks up, checks not revoked/expired
        # updates last_used_at on hit
```

### API key endpoints (`app/api/v1/api_keys.py`)

All require org owner or admin role.

- `POST /api/v1/orgs/{org_id}/api-keys` — create, returns full key + metadata (201)
- `GET /api/v1/orgs/{org_id}/api-keys` — list metadata only, never secret
- `DELETE /api/v1/orgs/{org_id}/api-keys/{key_id}` — revoke (204)

### Auth dep update (`app/api/deps.py`)

`get_current_user` detects API key by checking if the Bearer token starts with `sk_live_`:

```python
if token.startswith("sk_live_"):
    key_record = api_key_service.authenticate(session, raw_key=token)
    if not key_record:
        raise 401
    return user_service.get(session, key_record.created_by)
# else: existing JWT path
```

This means all existing endpoints accept API keys with zero changes.

---

## Frontend

### New page: `/auth/callback`

Public route (added to middleware `PUBLIC_PATHS`). Reads `?token=` query param, stores as `access_token` cookie (same approach as login), auto-selects first org via `orgsService.list()`, redirects to `/dashboard`. Shows a brief loading state while processing.

### Login + Signup pages

Add "Continue with Google" button below the existing form. It is an `<a>` tag linking to `/api/v1/auth/google` (full page navigation, not fetch). Styled consistently with existing buttons, with Google's `G` logo icon.

### Org Settings page — API Keys tab

New "API Keys" tab on `/orgs/[orgId]/settings` (alongside existing settings).

**List view** — table with columns: Name, Key, Created, Last Used, Actions.
- Key column shows prefix only: `sk_live_abc123...`
- Actions: "Revoke" button (confirms before revoking)

**Create flow:**
1. "Create API Key" button opens a modal
2. User enters a name (required)
3. On submit: POST to backend, response includes full key
4. Modal transitions to "Copy your key" view:
   - Full key in a read-only input with a copy button
   - Warning: "This key won't be shown again. Store it somewhere safe."
   - "Done" button closes modal, key is cleared from state

### New service/query files

- `src/services/apiKeys.ts` — `create`, `list`, `revoke` methods
- `src/queries/apiKeys.ts` — `useApiKeys`, `useCreateApiKey`, `useRevokeApiKey` hooks

---

## Error Handling

| Scenario | Response |
|----------|----------|
| Google OAuth not configured | 501 Not Implemented |
| OAuth state mismatch (CSRF) | 400 Bad Request |
| Google returns error | redirect to `/auth/login?error=oauth_failed` |
| API key not found / revoked | 401 Unauthorized |
| API key expired | 401 Unauthorized |
| Create key — not org owner/admin | 403 Forbidden |

---

## Testing

**Backend (pytest):**
- `test_oauth.py` — mock Google HTTP calls; test new user, existing user (JWT link), existing email (auto-link), state mismatch
- `test_api_keys.py` — create, list, revoke, authenticate with valid/revoked/expired key, wrong org, non-owner

**Frontend:**
- Manual: Google sign-in flow end-to-end, API key create+copy+revoke in org settings

---

## Out of Scope

- Additional OAuth providers (GitHub, etc.) — table supports it, no implementation
- API key permission scopes — all keys have full org access
- API key usage logs — `last_used_at` is sufficient for now
- Password reset for Google-only accounts
