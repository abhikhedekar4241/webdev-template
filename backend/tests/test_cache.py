import pickle
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
    mock_redis.get.side_effect = [None, pickle.dumps(4)]  # first call: miss; second call: hit
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
