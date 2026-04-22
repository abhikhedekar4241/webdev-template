# API Reference

The API is built with FastAPI and follows RESTful principles.

## Interactive Docs

When running locally, you can access the interactive Swagger UI at:
`http://localhost:8000/docs`

## Authentication

Most endpoints require a Bearer token in the `Authorization` header:
`Authorization: Bearer <your_token>`

API Keys can also be used with the same header:
`Authorization: Bearer sk_live_...`
