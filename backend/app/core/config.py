from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Email (optional until email sending is used)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None

    # InfluxDB (optional until metrics are used)
    INFLUXDB_URL: str = "http://influxdb:8086"
    INFLUXDB_TOKEN: str | None = None
    INFLUXDB_ORG: str | None = None
    INFLUXDB_BUCKET: str | None = None

    # MinIO (optional until file uploads are used)
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str | None = None
    MINIO_SECRET_KEY: str | None = None
    MINIO_BUCKET: str = "uploads"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Google OAuth (optional — endpoints return 501 if not configured)
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # Backend base URL (used to build OAuth redirect URIs)
    BACKEND_URL: str = "http://localhost:8000"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
