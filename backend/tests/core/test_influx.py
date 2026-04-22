from unittest.mock import MagicMock, patch

import pytest

import app.core.influx
from app.core.influx import get_write_api


@pytest.fixture(autouse=True)
def reset_influx():
    app.core.influx._client = None
    app.core.influx._write_api = None
    yield
    app.core.influx._client = None
    app.core.influx._write_api = None


async def test_get_write_api_no_token():
    with patch("app.core.influx.settings") as mock_settings:
        mock_settings.INFLUXDB_TOKEN = None
        assert await get_write_api() is None


async def test_get_write_api_success():
    with patch("app.core.influx.settings") as mock_settings:
        mock_settings.INFLUXDB_TOKEN = "token"
        mock_settings.INFLUXDB_URL = "http://localhost:8086"
        mock_settings.INFLUXDB_ORG = "org"

        with patch("app.core.influx.InfluxDBClient") as mock_client_class:
            mock_client = MagicMock()
            mock_write_api = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.write_api.return_value = mock_write_api

            # First call
            assert await get_write_api() == mock_write_api
            mock_client_class.assert_called_once()

            # Second call (memoized)
            assert await get_write_api() == mock_write_api
            assert mock_client_class.call_count == 1
