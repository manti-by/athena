# Athena

Simple FastAPI wrapper for OpenRouter's image generation API (Google Gemini 3 Pro).

## Setup

```bash
uv sync --all-extras --dev
```

## Run

```bash
uv run uvicorn main:app --reload
```

## Environment

- `OPENROUTER_API_KEY`: OpenRouter API key
- `LOG_PATH`: Log file path (default: `/var/log/athena/athena.log`)

## API

- `GET /`: Serve HTML frontend
- `POST /api/v1/image/`: Generate image from text prompt
