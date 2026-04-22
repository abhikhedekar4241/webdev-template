# ADR 001: SQLModel over SQLAlchemy

- **Status:** Accepted
- **Deciders:** [Team Name]
- **Date:** 2024-04-22

## Context and Problem Statement
We need an Object-Relational Mapper (ORM) for interacting with our PostgreSQL database in FastAPI. The main candidates are SQLAlchemy and SQLModel.

## Decision Drivers
- **Developer Productivity:** Reducing boilerplate and duplication between Pydantic schemas and database models.
- **Type Safety:** Ensuring strong typing across the backend.
- **Modern Standards:** Leveraging the latest Python features (Type Hints, Pydantic v2).

## Considered Options
1.  **SQLAlchemy:** The industry-standard Python ORM. Highly mature and powerful.
2.  **SQLModel:** A library built on top of SQLAlchemy 2.0 and Pydantic v2.

## Decision Outcome
**SQLModel** was chosen because it allows us to define a single model that serves as both a database entity and a Pydantic schema. This significantly reduces code duplication and ensures consistency between the database structure and the API data.

### Positive Consequences
- Faster development: Write once, use everywhere.
- Automatic integration with FastAPI's documentation (OpenAPI).
- Built-in type safety that works seamlessly with editors like VS Code and PyCharm.

### Negative Consequences
- Slightly less mature than raw SQLAlchemy.
- Occasional edge cases in complex relationships where raw SQLAlchemy might be needed.
