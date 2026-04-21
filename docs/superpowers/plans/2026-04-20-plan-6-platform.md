# Platform Services Implementation Plan (Plan 6 of 6)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up the cross-cutting platform services — Audit Logs, Stats (InfluxDB), Redis Cache decorator, Feature Flags (per-org overrides), Background Jobs (Celery), and Grafana provisioning — all connected but none blocking development without their infrastructure.

**Architecture:** Each service is a standalone module with no hard runtime dependency on its backing store (InfluxDB, Redis, MinIO). Services degrade gracefully: missing config → warning log, not a crash. Feature flags check DB overrides first, then fall back to `flags.yml`. Audit logs are fire-and-forget (no HTTP API). Cache decorator is opt-in per route.

**Tech Stack:** InfluxDB Python client, Redis (`redis-py`), Celery 5, PyYAML, structlog

**Prerequisite:** Plans 2–5 must be complete (services reference `User` and `Organization` models).

---

## File Map

**Backend (new):**
- Create: `backend/app/models/audit_log.py`
- Create: `backend/app/models/feature_flag.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/alembic/env.py`
- Create: `backend/alembic/versions/<hash>_add_audit_logs_feature_flags.py`
- Create: `backend/app/core/influx.py` — InfluxDB client wrapper
- Create: `backend/app/services/audit.py` — `log_event()`
- Create: `backend/app/services/stats.py` — `inc / avg / set / max → InfluxDB`
- Create: `backend/app/services/cache.py` — `@cache(ttl)` Redis decorator
- Create: `backend/app/services/flags.py` — `is_enabled(org_id, flag_name)`
- Create: `backend/flags.yml` — flag definitions + defaults
- Modify: `backend/app/worker.py` — Celery app fully configured
- Create: `backend/app/jobs/examples.py` — example Celery tasks
- Create: `backend/app/api/v1/flags.py` — `PATCH /api/v1/orgs/{org_id}/flags/{flag_name}`
- Modify: `backend/app/api/v1/orgs.py` — include flags endpoint
- Modify: `backend/app/main.py` — ensure flags router wired
- Create: `backend/grafana/provisioning/datasources/influxdb.yml`
- Create: `backend/grafana/provisioning/dashboards/dashboard.yml`
- Create: `backend/grafana/provisioning/dashboards/starter.json`
- Create: `backend/tests/test_audit.py`
- Create: `backend/tests/test_stats.py`
- Create: `backend/tests/test_cache.py`
- Create: `backend/tests/test_flags.py`

---

## Task 1: Audit Log + Feature Flag Models + Migration

**Files:**
- Create: `backend/app/models/audit_log.py`
- Create: `backend/app/models/feature_flag.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/alembic/env.py`

- [ ] **Step 1: Create `backend/app/models/audit_log.py`**

```python
import uuid
from datetime import datetime
from typing import Any

from sqlmodel import JSON, Column, Field, SQLModel


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    event: str = Field(index=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", nullable=True)
    org_id: uuid.UUID | None = Field(default=None, foreign_key="organizations.id", nullable=True)
    metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
```

- [ ] **Step 2: Create `backend/app/models/feature_flag.py`**

```python
import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class FeatureFlagOverride(SQLModel, table=True):
    __tablename__ = "feature_flag_overrides"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    flag_name: str
    enabled: bool
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 3: Update `backend/app/models/__init__.py`**

```python
from app.models.user import User  # noqa: F401
from app.models.password_reset import PasswordResetToken  # noqa: F401
from app.models.org import Organization, OrgMembership, OrgRole  # noqa: F401
from app.models.invitation import InvitationStatus, OrgInvitation  # noqa: F401
from app.models.file import File  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.feature_flag import FeatureFlagOverride  # noqa: F401
```

- [ ] **Step 4: Update `backend/alembic/env.py`**

Add after the File model import:

```python
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.feature_flag import FeatureFlagOverride  # noqa: F401
```

- [ ] **Step 5: Generate migration**

```bash
cd backend && alembic revision --autogenerate -m "add audit logs and feature flag overrides"
```

Expected: New file with `op.create_table("audit_logs", ...)` and `op.create_table("feature_flag_overrides", ...)`.

- [ ] **Step 6: Apply migration**

```bash
cd backend && alembic upgrade head
```

Expected: `Running upgrade  -> <hash>, add audit logs and feature flag overrides`

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/audit_log.py backend/app/models/feature_flag.py backend/app/models/__init__.py backend/alembic/
git commit -m "feat: add AuditLog and FeatureFlagOverride models with migration"
```

---

## Task 2: Audit Log Service

**Files:**
- Create: `backend/app/services/audit.py`
- Create: `backend/tests/test_audit.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_audit.py`:

```python
import uuid

import pytest

from app.models.audit_log import AuditLog
from app.models.org import OrgMembership, Organization
from app.models.user import User
from app.services.audit import log_event


@pytest.fixture(autouse=True)
def create_tables(session):
    User.__table__.create(session.get_bind(), checkfirst=True)
    Organization.__table__.create(session.get_bind(), checkfirst=True)
    OrgMembership.__table__.create(session.get_bind(), checkfirst=True)
    AuditLog.__table__.create(session.get_bind(), checkfirst=True)
    yield
    AuditLog.__table__.drop(session.get_bind())
    OrgMembership.__table__.drop(session.get_bind())
    Organization.__table__.drop(session.get_bind())
    User.__table__.drop(session.get_bind())


def test_log_event_creates_record(session):
    user_id = uuid.uuid4()
    log_event(session, event="user.login", user_id=user_id)
    from sqlmodel import select
    logs = session.exec(select(AuditLog)).all()
    assert len(logs) == 1
    assert logs[0].event == "user.login"
    assert logs[0].user_id == user_id


def test_log_event_with_org_and_metadata(session):
    org_id = uuid.uuid4()
    log_event(
        session,
        event="org.created",
        org_id=org_id,
        metadata={"org_name": "Acme"},
    )
    from sqlmodel import select
    log = session.exec(select(AuditLog)).first()
    assert log.org_id == org_id
    assert log.metadata == {"org_name": "Acme"}


def test_log_event_all_optional(session):
    log_event(session, event="system.startup")
    from sqlmodel import select
    log = session.exec(select(AuditLog)).first()
    assert log.event == "system.startup"
    assert log.user_id is None
    assert log.org_id is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && pytest tests/test_audit.py -v
```

Expected: `ImportError` — `app.services.audit` does not exist yet.

- [ ] **Step 3: Create `backend/app/services/audit.py`**

```python
import uuid
from typing import Any

import structlog
from sqlmodel import Session

from app.models.audit_log import AuditLog

logger = structlog.get_logger()


def log_event(
    session: Session,
    *,
    event: str,
    user_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    try:
        entry = AuditLog(
            event=event,
            user_id=user_id,
            org_id=org_id,
            metadata=metadata or {},
        )
        session.add(entry)
        session.commit()
        logger.info("audit_event", event=event, user_id=str(user_id), org_id=str(org_id))
    except Exception as exc:
        logger.error("audit_log_failed", event=event, error=str(exc))
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend && pytest tests/test_audit.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/audit.py backend/tests/test_audit.py
git commit -m "feat: add audit log service"
```

---

## Task 3: Stats Service (InfluxDB)

**Files:**
- Create: `backend/app/core/influx.py`
- Create: `backend/app/services/stats.py`
- Create: `backend/tests/test_stats.py`

- [ ] **Step 1: Create `backend/app/core/influx.py`**

```python
import structlog
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from app.core.config import settings

logger = structlog.get_logger()

_client: InfluxDBClient | None = None
_write_api = None


def get_write_api():
    global _client, _write_api
    if not settings.INFLUXDB_TOKEN:
        return None
    if _client is None:
        _client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG,
        )
        _write_api = _client.write_api(write_options=SYNCHRONOUS)
    return _write_api
```

- [ ] **Step 2: Write the failing tests**

Create `backend/tests/test_stats.py`:

```python
from unittest.mock import MagicMock, patch

from app.services.stats import stats


def test_inc_calls_influx_write():
    mock_api = MagicMock()
    with patch("app.services.stats.get_write_api", return_value=mock_api):
        stats.inc("acme.req.n", 1)
    mock_api.write.assert_called_once()


def test_avg_calls_influx_write():
    mock_api = MagicMock()
    with patch("app.services.stats.get_write_api", return_value=mock_api):
        stats.avg("acme.latency.ms", 250)
    mock_api.write.assert_called_once()


def test_set_calls_influx_write():
    mock_api = MagicMock()
    with patch("app.services.stats.get_write_api", return_value=mock_api):
        stats.set("acme.member_count", 5)
    mock_api.write.assert_called_once()


def test_max_calls_influx_write():
    mock_api = MagicMock()
    with patch("app.services.stats.get_write_api", return_value=mock_api):
        stats.max("acme.latency.max", 1000)
    mock_api.write.assert_called_once()


def test_inc_skips_when_no_influx_config():
    with patch("app.services.stats.get_write_api", return_value=None):
        # Should not raise
        stats.inc("acme.req.n", 1)
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
cd backend && pytest tests/test_stats.py -v
```

Expected: `ImportError` — `app.services.stats` does not exist yet.

- [ ] **Step 4: Create `backend/app/services/stats.py`**

```python
import structlog
from influxdb_client import Point

from app.core.config import settings
from app.core.influx import get_write_api

logger = structlog.get_logger()


class StatsService:
    def _write(self, measurement: str, field: str, value: float) -> None:
        write_api = get_write_api()
        if write_api is None:
            return
        try:
            point = (
                Point(measurement)
                .field(field, value)
            )
            write_api.write(
                bucket=settings.INFLUXDB_BUCKET,
                org=settings.INFLUXDB_ORG,
                record=point,
            )
        except Exception as exc:
            logger.warning("stats_write_failed", measurement=measurement, error=str(exc))

    def inc(self, measurement: str, value: float = 1) -> None:
        self._write(measurement, "count", value)

    def avg(self, measurement: str, value: float) -> None:
        self._write(measurement, "avg", value)

    def set(self, measurement: str, value: float) -> None:  # noqa: A003
        self._write(measurement, "value", value)

    def max(self, measurement: str, value: float) -> None:  # noqa: A003
        self._write(measurement, "max", value)


stats = StatsService()
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd backend && pytest tests/test_stats.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/influx.py backend/app/services/stats.py backend/tests/test_stats.py
git commit -m "feat: add InfluxDB client and stats service (inc/avg/set/max)"
```

---

## Task 4: Redis Cache Decorator

**Files:**
- Create: `backend/app/services/cache.py`
- Create: `backend/tests/test_cache.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_cache.py`:

```python
import time
from unittest.mock import MagicMock, patch

from app.services.cache import cache


def test_cache_returns_cached_value_on_second_call():
    call_count = 0

    @cache(ttl=60)
    def expensive(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x * 2

    mock_redis = MagicMock()
    mock_redis.get.side_effect = [None, b"4"]  # first call: miss; second call: hit
    mock_redis.setex.return_value = True

    with patch("app.services.cache._get_redis", return_value=mock_redis):
        result1 = expensive(2)
        result2 = expensive(2)

    assert result1 == 4
    assert result2 == 4
    assert call_count == 1  # Only called once; second was cached


def test_cache_skips_when_redis_unavailable():
    @cache(ttl=60)
    def my_func(x: int) -> int:
        return x + 1

    with patch("app.services.cache._get_redis", return_value=None):
        result = my_func(5)

    assert result == 6  # Should still work without Redis
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && pytest tests/test_cache.py -v
```

Expected: `ImportError` — `app.services.cache` does not exist yet.

- [ ] **Step 3: Create `backend/app/services/cache.py`**

```python
import functools
import hashlib
import json
import pickle
from typing import Any, Callable

import structlog
import redis as redis_lib

from app.core.config import settings

logger = structlog.get_logger()

_redis_client: redis_lib.Redis | None = None


def _get_redis() -> redis_lib.Redis | None:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        client = redis_lib.from_url(settings.REDIS_URL, decode_responses=False)
        client.ping()
        _redis_client = client
        return _redis_client
    except Exception as exc:
        logger.warning("redis_unavailable", error=str(exc))
        return None


def cache(ttl: int = 60) -> Callable:
    """Decorator to cache function results in Redis for `ttl` seconds."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            r = _get_redis()
            if r is None:
                return func(*args, **kwargs)

            key_data = json.dumps(
                {"fn": func.__qualname__, "args": args, "kwargs": kwargs},
                sort_keys=True,
                default=str,
            )
            cache_key = "cache:" + hashlib.md5(key_data.encode()).hexdigest()

            try:
                cached = r.get(cache_key)
                if cached is not None:
                    return pickle.loads(cached)  # noqa: S301

                result = func(*args, **kwargs)
                r.setex(cache_key, ttl, pickle.dumps(result))
                return result
            except Exception as exc:
                logger.warning("cache_error", fn=func.__qualname__, error=str(exc))
                return func(*args, **kwargs)

        return wrapper

    return decorator
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend && pytest tests/test_cache.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/cache.py backend/tests/test_cache.py
git commit -m "feat: add Redis cache decorator"
```

---

## Task 5: Feature Flags Service + API

**Files:**
- Create: `backend/flags.yml`
- Create: `backend/app/services/flags.py`
- Create: `backend/app/api/v1/flags.py`
- Modify: `backend/app/api/v1/orgs.py` — add flags endpoint import
- Create: `backend/tests/test_flags.py`

- [ ] **Step 1: Create `backend/flags.yml`**

```yaml
flags:
  new_dashboard: false
  beta_exports: false
```

- [ ] **Step 2: Write the failing tests**

Create `backend/tests/test_flags.py`:

```python
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from app.models.feature_flag import FeatureFlagOverride
from app.models.org import OrgMembership, Organization
from app.models.user import User
from app.services.flags import flags_service


@pytest.fixture(autouse=True)
def create_tables(session):
    User.__table__.create(session.get_bind(), checkfirst=True)
    Organization.__table__.create(session.get_bind(), checkfirst=True)
    OrgMembership.__table__.create(session.get_bind(), checkfirst=True)
    FeatureFlagOverride.__table__.create(session.get_bind(), checkfirst=True)
    yield
    FeatureFlagOverride.__table__.drop(session.get_bind())
    OrgMembership.__table__.drop(session.get_bind())
    Organization.__table__.drop(session.get_bind())
    User.__table__.drop(session.get_bind())


MOCK_FLAGS = {"flags": {"new_dashboard": False, "beta_exports": False}}


def test_flag_returns_yml_default_when_no_override(session):
    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        result = flags_service.is_enabled(session, org_id=uuid.uuid4(), flag_name="new_dashboard")
    assert result is False


def test_flag_returns_org_override(session):
    org_id = uuid.uuid4()
    override = FeatureFlagOverride(org_id=org_id, flag_name="new_dashboard", enabled=True)
    session.add(override)
    session.commit()

    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        result = flags_service.is_enabled(session, org_id=org_id, flag_name="new_dashboard")
    assert result is True


def test_unknown_flag_returns_false(session):
    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        result = flags_service.is_enabled(
            session, org_id=uuid.uuid4(), flag_name="nonexistent_flag"
        )
    assert result is False


def test_set_override_creates_new(session):
    org_id = uuid.uuid4()
    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        flags_service.set_override(session, org_id=org_id, flag_name="new_dashboard", enabled=True)
        result = flags_service.is_enabled(session, org_id=org_id, flag_name="new_dashboard")
    assert result is True


def test_set_override_updates_existing(session):
    org_id = uuid.uuid4()
    override = FeatureFlagOverride(org_id=org_id, flag_name="new_dashboard", enabled=True)
    session.add(override)
    session.commit()

    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        flags_service.set_override(session, org_id=org_id, flag_name="new_dashboard", enabled=False)
        result = flags_service.is_enabled(session, org_id=org_id, flag_name="new_dashboard")
    assert result is False
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
cd backend && pytest tests/test_flags.py -v
```

Expected: `ImportError` — `app.services.flags` does not exist yet.

- [ ] **Step 4: Create `backend/app/services/flags.py`**

```python
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
import yaml
from sqlmodel import Session, select

from app.models.feature_flag import FeatureFlagOverride

logger = structlog.get_logger()

_FLAGS_PATH = Path(__file__).parent.parent.parent / "flags.yml"


class FlagsService:
    def _load_yaml(self) -> dict[str, Any]:
        try:
            with open(_FLAGS_PATH) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("flags_yml_not_found", path=str(_FLAGS_PATH))
            return {"flags": {}}

    def is_enabled(
        self, session: Session, *, org_id: uuid.UUID, flag_name: str
    ) -> bool:
        # 1. Check DB override for this org
        override = session.exec(
            select(FeatureFlagOverride)
            .where(FeatureFlagOverride.org_id == org_id)
            .where(FeatureFlagOverride.flag_name == flag_name)
        ).first()

        if override is not None:
            return override.enabled

        # 2. Fall back to flags.yml default
        data = self._load_yaml()
        flags = data.get("flags", {})
        return bool(flags.get(flag_name, False))

    def set_override(
        self,
        session: Session,
        *,
        org_id: uuid.UUID,
        flag_name: str,
        enabled: bool,
    ) -> FeatureFlagOverride:
        existing = session.exec(
            select(FeatureFlagOverride)
            .where(FeatureFlagOverride.org_id == org_id)
            .where(FeatureFlagOverride.flag_name == flag_name)
        ).first()

        if existing:
            existing.enabled = enabled
            existing.updated_at = datetime.utcnow()
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

        override = FeatureFlagOverride(
            org_id=org_id, flag_name=flag_name, enabled=enabled
        )
        session.add(override)
        session.commit()
        session.refresh(override)
        return override

    def list_defaults(self) -> dict[str, bool]:
        data = self._load_yaml()
        return data.get("flags", {})


flags_service = FlagsService()
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd backend && pytest tests/test_flags.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Create `backend/app/api/v1/flags.py`**

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.org import OrgRole
from app.models.user import User
from app.services.flags import flags_service
from app.services.orgs import org_service

router = APIRouter(prefix="/api/v1/orgs", tags=["flags"])


class FlagOverrideRequest(BaseModel):
    enabled: bool


class FlagStatusResponse(BaseModel):
    flag_name: str
    enabled: bool


@router.patch("/{org_id}/flags/{flag_name}", response_model=FlagStatusResponse)
def set_flag_override(
    org_id: uuid.UUID,
    flag_name: str,
    body: FlagOverrideRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Only owner or admin can change flags
    membership = org_service.get_membership(
        session, org_id=org_id, user_id=current_user.id
    )
    if not membership or membership.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Validate flag exists in flags.yml
    defaults = flags_service.list_defaults()
    if flag_name not in defaults:
        raise HTTPException(status_code=404, detail=f"Unknown flag: {flag_name}")

    override = flags_service.set_override(
        session, org_id=org_id, flag_name=flag_name, enabled=body.enabled
    )
    return {"flag_name": flag_name, "enabled": override.enabled}


@router.get("/{org_id}/flags/{flag_name}", response_model=FlagStatusResponse)
def get_flag_status(
    org_id: uuid.UUID,
    flag_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    membership = org_service.get_membership(
        session, org_id=org_id, user_id=current_user.id
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    enabled = flags_service.is_enabled(session, org_id=org_id, flag_name=flag_name)
    return {"flag_name": flag_name, "enabled": enabled}
```

- [ ] **Step 7: Update `backend/app/main.py` — include flags router**

Add import:
```python
from app.api.v1 import auth, files, flags, health, invitations, orgs
```

Add after files router inclusion:
```python
app.include_router(flags.router)
```

Full router section:
```python
app.include_router(health.router, tags=["health"])
app.include_router(auth.router)
app.include_router(orgs.router)
app.include_router(invitations.router)
app.include_router(files.router)
app.include_router(flags.router)
```

- [ ] **Step 8: Verify app starts**

```bash
cd backend && python -c "from app.main import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 9: Commit**

```bash
git add backend/flags.yml backend/app/services/flags.py backend/app/api/v1/flags.py backend/app/main.py backend/tests/test_flags.py
git commit -m "feat: add feature flags service (YAML defaults + per-org DB overrides) and API"
```

---

## Task 6: Background Jobs (Celery)

**Files:**
- Modify: `backend/app/worker.py` — fully configure Celery app
- Modify: `backend/app/jobs/examples.py` — add concrete example tasks

- [ ] **Step 1: Read `backend/app/worker.py` to see its current state**

Read the file before editing.

- [ ] **Step 2: Update `backend/app/worker.py`**

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
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)
```

- [ ] **Step 3: Read `backend/app/jobs/examples.py` to see its current state**

Read the file before editing.

- [ ] **Step 4: Update `backend/app/jobs/examples.py`**

```python
"""
Example Celery tasks.

Run the worker with:
  celery -A app.worker.celery_app worker --loglevel=info

Dispatch from application code:
  from app.jobs.examples import send_welcome_email_task
  send_welcome_email_task.delay(user_email="alice@example.com", full_name="Alice")
"""
import structlog

from app.worker import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3)
def send_welcome_email_task(self, *, user_email: str, full_name: str) -> dict:
    """
    Example: Send a welcome email asynchronously.
    In production, call email_service.send() here instead of logging.
    """
    try:
        logger.info("task_send_welcome_email", user_email=user_email, full_name=full_name)
        # email_service.send(to=user_email, subject="Welcome!", template="welcome", context={"full_name": full_name, "login_url": "..."})
        return {"status": "sent", "to": user_email}
    except Exception as exc:
        logger.error("task_failed", task="send_welcome_email", error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def cleanup_expired_invitations_task(self) -> dict:
    """
    Example: Periodic task to clean up expired invitations.
    Wire into Celery beat for scheduling.
    """
    from datetime import datetime

    from sqlmodel import Session, select

    from app.core.db import engine
    from app.models.invitation import InvitationStatus, OrgInvitation

    try:
        with Session(engine) as session:
            expired = session.exec(
                select(OrgInvitation)
                .where(OrgInvitation.status == InvitationStatus.pending)
                .where(OrgInvitation.expires_at < datetime.utcnow())
            ).all()

            count = len(expired)
            for inv in expired:
                inv.status = InvitationStatus.declined
                session.add(inv)
            session.commit()

        logger.info("cleanup_expired_invitations", count=count)
        return {"expired_count": count}
    except Exception as exc:
        logger.error("task_failed", task="cleanup_expired_invitations", error=str(exc))
        raise self.retry(exc=exc, countdown=120)
```

- [ ] **Step 5: Verify Celery app can be imported**

```bash
cd backend && python -c "from app.worker import celery_app; print('Celery OK:', celery_app)"
```

Expected: `Celery OK: <Celery worker at 0x...>`

- [ ] **Step 6: Commit**

```bash
git add backend/app/worker.py backend/app/jobs/examples.py
git commit -m "feat: configure Celery worker with example tasks (welcome email, cleanup invitations)"
```

---

## Task 7: Grafana Provisioning

**Files:**
- Create: `backend/grafana/provisioning/datasources/influxdb.yml`
- Create: `backend/grafana/provisioning/dashboards/dashboard.yml`
- Create: `backend/grafana/provisioning/dashboards/starter.json`

The `grafana` service in `docker-compose.yml` should already mount `./grafana/provisioning:/etc/grafana/provisioning`. Verify this before proceeding — read `docker-compose.yml`.

- [ ] **Step 1: Verify Grafana provisioning mount in `docker-compose.yml`**

Read `docker-compose.yml` and confirm the Grafana service has:
```yaml
volumes:
  - ./grafana/provisioning:/etc/grafana/provisioning
```

If the volume is missing, add it to the grafana service in `docker-compose.yml`.

- [ ] **Step 2: Create `backend/grafana/provisioning/datasources/influxdb.yml`**

Create the directory first (`backend/grafana/provisioning/datasources/`), then create the file:

```yaml
apiVersion: 1

datasources:
  - name: InfluxDB
    type: influxdb
    access: proxy
    url: http://influxdb:8086
    jsonData:
      version: Flux
      organization: ${INFLUXDB_ORG}
      defaultBucket: ${INFLUXDB_BUCKET}
      tlsSkipVerify: true
    secureJsonData:
      token: ${INFLUXDB_TOKEN}
    isDefault: true
    editable: true
```

- [ ] **Step 3: Create `backend/grafana/provisioning/dashboards/dashboard.yml`**

```yaml
apiVersion: 1

providers:
  - name: Default
    folder: ""
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /etc/grafana/provisioning/dashboards
```

- [ ] **Step 4: Create `backend/grafana/provisioning/dashboards/starter.json`**

```json
{
  "__inputs": [],
  "__requires": [],
  "annotations": { "list": [] },
  "description": "Boilerplate starter dashboard",
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "datasource": { "type": "influxdb", "uid": "influxdb" },
      "fieldConfig": {
        "defaults": { "color": { "mode": "palette-classic" }, "custom": {} },
        "overrides": []
      },
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
      "id": 1,
      "options": { "legend": { "calcs": [], "displayMode": "list", "placement": "bottom" } },
      "title": "Request Count",
      "type": "timeseries",
      "targets": [
        {
          "datasource": { "type": "influxdb" },
          "query": "from(bucket: v.defaultBucket)\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement =~ /req\\.n$/)\n  |> sum()",
          "refId": "A"
        }
      ]
    }
  ],
  "schemaVersion": 38,
  "tags": ["boilerplate"],
  "time": { "from": "now-1h", "to": "now" },
  "timepicker": {},
  "timezone": "browser",
  "title": "Boilerplate Starter",
  "uid": "boilerplate-starter",
  "version": 1
}
```

- [ ] **Step 5: Commit**

```bash
git add backend/grafana/
git commit -m "feat: add Grafana provisioning files (InfluxDB datasource + starter dashboard)"
```

---

## Task 8: Full Test Suite + Linter

- [ ] **Step 1: Run full backend test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: All tests passing.

- [ ] **Step 2: Run linter**

```bash
cd backend && ruff check app/ tests/ && ruff format --check app/ tests/
```

Expected: No errors.

- [ ] **Step 3: Run frontend type check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No type errors.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final platform services — all tests pass, linter clean"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Audit Log model: id, event, user_id (nullable), org_id (nullable), metadata (JSON), created_at
- [x] `log_event()` — fire-and-forget, graceful failure
- [x] FeatureFlagOverride model: id, org_id, flag_name, enabled, updated_at
- [x] `flags.yml` with `new_dashboard` and `beta_exports` defaults
- [x] `is_enabled(org_id, flag_name)` — DB override first, then YAML default
- [x] `PATCH /api/v1/orgs/{org_id}/flags/{flag_name}` — owner/admin only
- [x] `GET /api/v1/orgs/{org_id}/flags/{flag_name}` — any member
- [x] Stats: `stats.inc / avg / set / max` → InfluxDB; skips silently if not configured
- [x] Cache: `@cache(ttl=N)` decorator backed by Redis; skips silently if unavailable
- [x] Celery: configured with Redis broker/backend, serializers, UTC timezone
- [x] Example tasks: `send_welcome_email_task`, `cleanup_expired_invitations_task`
- [x] Grafana: InfluxDB datasource + starter dashboard auto-provisioned on boot
- [x] InfluxDB client lazy-initialized, handles missing config gracefully
