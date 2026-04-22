import functools
import hashlib
import json
import pickle
from collections.abc import Callable
from typing import Any

import redis as redis_lib
import structlog

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
