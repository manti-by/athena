import os
from functools import lru_cache
from pathlib import Path


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    BASE_PATH = Path(__file__).resolve().parent.parent

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/athena")

    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-3.1-flash-image-preview")

    UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/var/lib/athena")

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)-6s: %(filename)-8s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
            "file": {
                "level": "WARNING",
                "class": "logging.FileHandler",
                "filename": os.environ.get("LOG_PATH", "/var/log/app/athena.log"),
                "formatter": "standard",
            },
        },
        "loggers": {
            "": {"handlers": ["console", "file"], "level": "INFO", "propagate": True},
        },
    }
