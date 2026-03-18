import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from athena.models.user import User
from athena.services.auth import create_access_token


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://athena:athena@localhost:5432/test_athena"
    os.environ["SECRET_KEY"] = "Lly1+DnfJus2zsl$?e1VJeV\\&r1eRs9hP"
    os.environ["UPLOAD_DIR"] = str(tmp_path / "uploads")

    from athena.settings import get_settings

    get_settings.cache_clear()

    yield


@pytest.fixture(autouse=True, scope="function")
def setup_db_user(setup_test_env):
    import asyncio

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    async def setup_db():
        engine = create_async_engine(os.environ["DATABASE_URL"])
        async with engine.begin() as conn:
            await conn.execute(
                text("TRUNCATE TABLE session_item_images, session_items, sessions, users, images CASCADE")
            )
            await conn.execute(
                text(
                    "INSERT INTO users (id, email, name, google_id, avatar) VALUES (1, 'test@example.com', 'Test User', 'google123', 'https://example.com/avatar.png')"
                )
            )
        await engine.dispose()

    asyncio.run(setup_db())

    import athena.api.auth as auth_module
    import athena.api.sessions as sessions_module
    import athena.services.database as db_module
    from athena.settings import get_settings

    settings = get_settings()
    original_db_maker = db_module.async_session_maker
    original_sessions_maker = sessions_module.async_session_maker
    original_auth_maker = auth_module.async_session_maker
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    new_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    db_module.async_session_maker = new_maker
    sessions_module.async_session_maker = new_maker
    auth_module.async_session_maker = new_maker

    yield

    db_module.async_session_maker = original_db_maker
    sessions_module.async_session_maker = original_sessions_maker
    auth_module.async_session_maker = original_auth_maker
    asyncio.run(engine.dispose())


def create_auth_token(user_id: int, email: str) -> str:
    return create_access_token({"user_id": user_id, "email": email})


def create_test_user(user_id: int = 1, email: str = "test@example.com", name: str = "Test User") -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = email
    user.name = name
    user.avatar = "https://example.com/avatar.png"
    return user


def get_authenticated_client(token: str | None = None) -> TestClient:
    from main import app

    client = TestClient(app, raise_server_exceptions=False)

    if token is None:
        test_user = create_test_user()
        token = create_auth_token(test_user.id, test_user.email)

    client.cookies.set("access_token", token)
    return client


def get_unauthenticated_client() -> TestClient:
    from main import app

    return TestClient(app, raise_server_exceptions=False)


def mock_auth_user() -> User:
    return create_test_user(user_id=1, email="test@example.com")


def get_client_with_auth_mock(token: str | None = None) -> tuple[TestClient, MagicMock]:
    from main import app

    client = TestClient(app, raise_server_exceptions=False)

    if token is None:
        test_user = create_test_user()
        token = create_auth_token(test_user.id, test_user.email)

    client.cookies.set("access_token", token)

    mock_user = create_test_user(user_id=1, email="test@example.com")
    mock_get_user = MagicMock(return_value=AsyncMock(return_value=mock_user))

    return client, mock_get_user
