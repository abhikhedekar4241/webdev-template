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
            point = Point(measurement).field(field, value)
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
