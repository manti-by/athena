# Athena

FastAPI-based chat application with AI image generation capabilities, powered by OpenRouter (Google Gemini) and Groq for text processing. Supports user authentication via Google OAuth.

## Setup

```bash
uv sync --all-extras --dev
```

### Docker

```bash
docker compose up --build
```

## Run

```bash
uv run uvicorn main:app --reload
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for image generation | Required |
| `GROQ_API_KEY` | Groq API key for text processing | Required |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/athena` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | - |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | - |
| `SECRET_KEY` | JWT secret key | dev key |
| `LOG_PATH` | Log file path | `/var/log/athena/athena.log` |
| `UPLOAD_DIR` | Image upload directory | `/var/lib/athena` |

## API Endpoints

### Authentication
- `GET /api/v1/auth/google/login` - Initiate Google OAuth login
- `GET /api/v1/auth/google/callback` - OAuth callback
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - Logout

### Sessions
- `GET /api/v1/sessions/` - List user sessions
- `POST /api/v1/sessions/` - Create new session
- `GET /api/v1/sessions/{session_id}` - Get session with items
- `DELETE /api/v1/sessions/{session_id}` - Delete session

### Images
- `POST /api/v1/image/` - Generate image (global)
- `POST /api/v1/image/{session_id}` - Generate image in session
