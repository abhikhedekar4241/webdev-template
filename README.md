# Boilerplate SaaS

A production-ready SaaS template built with **FastAPI** (Python) and **Next.js** (TypeScript), designed for rapid development and clean architecture.

## 🚀 Core Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui.
- **Backend:** FastAPI (Python 3.11+), SQLModel (SQLAlchemy 2.0 + Pydantic v2).
- **Database:** PostgreSQL 16.
- **Async Tasks:** Celery + Redis.
- **Object Storage:** MinIO (S3-compatible).
- **Monitoring:** InfluxDB 2 + Grafana.
- **Deployment:** Kamal (Zero-downtime).

## ✨ Key Features

- **Multi-tenancy:** Built-in support for Organizations and Org Memberships.
- **Authentication:** JWT-based auth, email verification, and OAuth support.
- **Admin Tools:** Dashboard, system stats, and user management.
- **File Management:** Robust file upload/download flow using MinIO.
- **Developer Experience:** Fully Dockerized local environment with hot-reloading.
- **Documentation:** MkDocs with Material theme for internal documentation.

## 🛠️ Quick Start

### 1. Prerequisites
Ensure you have **Docker** and **Docker Compose** installed.

### 2. Setup Environment
Copy the example environment variables:
```bash
cp .env.example .env
```
*(Update `.env` with your own secrets as needed)*

### 3. Spin up Services
```bash
make up        # Start all services in the background
make migrate   # Run database migrations
make seed      # Seed the database with initial data
```
The app will be available at **[http://localhost](http://localhost)**.

### 4. Documentation
To view the full project documentation (Architecture, API Reference, Deployment Guide):
```bash
make docs-serve
```
Then visit **[http://localhost:8008](http://localhost:8008)**.

## 📂 Project Structure

- `backend/`: FastAPI application, models, services, and tests.
- `frontend/`: Next.js application, UI components, and API integration.
- `docs/`: Markdown-based documentation.
- `nginx/`: Reverse proxy configuration for local development.

## 🧪 Testing

```bash
make test  # Runs both backend (pytest) and frontend (npm test) tests
```

## 📜 License

This project is licensed under the MIT License.
