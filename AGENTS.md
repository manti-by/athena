# AGENTS.md

## Project Overview

Athena is a FastAPI-based chat application with image generation capabilities, powered by OpenRouter (Google Gemini) and Groq for text processing. Supports user authentication via Google OAuth.

## Project Structure

```
athena/
├── api/              # API route handlers (auth, images, sessions)
├── models/           # SQLAlchemy models (User, Session, SessionItem, Image)
├── schemas/          # Pydantic schemas for request/response
├── services/        # Business logic (auth, generator, image, database)
├── prompts/          # LLM prompt templates
├── static/           # CSS, JS assets
├── templates/        # HTML templates
alembic/              # Database migrations
tests/                # Test suite
```

## Git Workflow

- Main branch: `master`
- Feature branches: `<agent>/feature/<issue-id>-<description>`
- Commits: Conventional Commits (`feat:`, `fix:`, etc.)

## Development Commands

```bash
# Install dependencies
uv sync --all-extras --dev

# Run the app
uv run uvicorn main:app --reload

# Run with Docker
docker compose up --build

# Run tests
make test

# Lint and type check
make check

# Generate migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Language & Environment

- Python >=3.13, <3.14
- Ruff for linting (120 char line length)
- ty for type checking
- pytest for tests
- Docker for containerization

## Environment Variables

### Required
- `OPENROUTER_API_KEY`: OpenRouter API key for image generation
- `GROQ_API_KEY`: Groq API key for text processing

### Optional
- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql+asyncpg://postgres:postgres@localhost:5432/athena`)
- `SECRET_KEY`: JWT secret key (default: dev key)
- `LOG_PATH`: Log file path (default: `/var/log/athena/athena.log`)
- `UPLOAD_DIR`: Image upload directory (default: `/var/lib/athena`)

### Google OAuth
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `GOOGLE_REDIRECT_URI`: OAuth callback URL (default: `http://localhost:8000/api/v1/auth/google/callback`)

### Groq Settings
- `GROQ_MODEL`: Groq model name (default: `llama-3.1-8b-instant`)
