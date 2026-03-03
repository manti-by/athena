# AGENTS.md

## Project Overview

Athena is a simple FastAPI wrapper for OpenRouter's image generation API (Google Gemini 3 Pro).

## Project Structure

- `main.py`: FastAPI application with image generation endpoint
- `settings.py`: Configuration and logging settings
- `templates/`: Static HTML templates
- `configs/`: Configuration files
- `tests/`: Test suite

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

# Run tests
make test

# Lint and type check
make check
```

## Language & Environment

- Python >=3.13, <3.14
- Ruff for linting (120 char line length)
- ty for type checking
- pytest for tests

## Environment Variables

- `OPENROUTER_API_KEY`: OpenRouter API key
- `LOG_PATH`: Log file path (default: `/var/log/athena/athena.log`)
