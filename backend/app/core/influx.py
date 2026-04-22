import structlog
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from app.core.config import settings

logger = structlog.get_logger()

_client: InfluxDBClient | None = None
_write_api = None


async def get_write_api():
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
