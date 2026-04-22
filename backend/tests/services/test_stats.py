from unittest.mock import patch, MagicMock
from app.services.stats import stats

async def test_inc_calls_influx_write():
    mock_api = MagicMock()
    with patch("app.services.stats.get_write_api", return_value=mock_api):
        await stats.inc("acme.req.n", 1)
    mock_api.write.assert_called_once()

async def test_avg_calls_influx_write():
    mock_api = MagicMock()
    with patch("app.services.stats.get_write_api", return_value=mock_api):
        await stats.avg("acme.latency.ms", 250)
    mock_api.write.assert_called_once()


async def test_set_calls_influx_write():
    mock_api = MagicMock()
    with patch("app.services.stats.get_write_api", return_value=mock_api):
        await stats.set("acme.member_count", 5)
    mock_api.write.assert_called_once()


async def test_max_calls_influx_write():
    mock_api = MagicMock()
    with patch("app.services.stats.get_write_api", return_value=mock_api):
        await stats.max("acme.latency.max", 1000)
    mock_api.write.assert_called_once()


async def test_inc_skips_when_no_influx_config():
    with patch("app.services.stats.get_write_api", return_value=None):
        # Should not raise
        await stats.inc("acme.req.n", 1)

async def test_write_failure_logs_warning():
    mock_api = MagicMock()
    mock_api.write.side_effect = Exception("Influx error")
    with patch("app.services.stats.get_write_api", return_value=mock_api):
        # Should catch and log, not raise
        await stats.inc("fail.test")
    mock_api.write.assert_called_once()
