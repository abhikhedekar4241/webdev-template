FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a separate volume
ENV UV_LINK_MODE=copy

# Install dependencies into a specific path
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev --project .

# After sync, the venv is in /app/.venv. 
# We want it to stay functional when moved or mounted over.
# uv venvs are generally portable if we don't rely on absolute paths in shebangs,
# but 'python -m uvicorn' is safer.

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtualenv from the builder to a path that WON'T be mounted over
COPY --from=builder /app/.venv /venv

# Set environment variables
ENV PATH="/venv/bin:$PATH"
ENV VIRTUAL_ENV="/venv"
ENV PYTHONUNBUFFERED=1

# Copy application files
COPY . .

# Use 'python -m' to avoid shebang issues with moved venv
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
