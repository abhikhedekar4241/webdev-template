import pytest
from unittest.mock import patch, MagicMock
from app.services.cache import cache, _get_redis
import app.services.cache
import fakeredis

@pytest.fixture(autouse=True)
def reset_redis_client():
    # Reset the global client before each test
    app.services.cache._redis_client = None
    yield
    app.services.cache._redis_client = None

def test_cache_hit_miss():
    fake_r = fakeredis.FakeRedis()
    
    with patch("app.services.cache._get_redis", return_value=fake_r):
        call_count = 0
        
        @cache(ttl=10)
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Miss
        assert my_func(5) == 10
        assert call_count == 1
        
        # Hit
        assert my_func(5) == 10
        assert call_count == 1
        
        # Different args (Miss)
        assert my_func(6) == 12
        assert call_count == 2

def test_cache_redis_unavailable():
    with patch("app.services.cache._get_redis", return_value=None):
        call_count = 0
        
        @cache(ttl=10)
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x
        
        assert my_func(10) == 10
        assert my_func(10) == 10
        assert call_count == 2

def test_get_redis_success():
    mock_client = MagicMock()
    with patch("redis.from_url", return_value=mock_client):
        client = _get_redis()
        assert client == mock_client
        mock_client.ping.assert_called_once()

def test_get_redis_failure():
    with patch("redis.from_url", side_effect=Exception("Connection failed")):
        client = _get_redis()
        assert client is None

def test_get_redis_existing():
    mock_client = MagicMock()
    app.services.cache._redis_client = mock_client
    assert _get_redis() == mock_client

def test_cache_redis_error_during_get():
    fake_r = MagicMock()
    fake_r.get.side_effect = Exception("Redis error")
    
    with patch("app.services.cache._get_redis", return_value=fake_r):
        @cache()
        def my_func():
            return "ok"
        
        assert my_func() == "ok"

def test_cache_redis_error_during_set():
    fake_r = MagicMock()
    fake_r.get.return_value = None
    fake_r.setex.side_effect = Exception("Redis error")
    
    with patch("app.services.cache._get_redis", return_value=fake_r):
        @cache()
        def my_func():
            return "ok"
        
        assert my_func() == "ok"
