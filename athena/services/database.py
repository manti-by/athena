from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from athena.settings import get_settings


settings = get_settings()

async_session_maker = async_sessionmaker(
    create_async_engine(settings.DATABASE_URL, echo=False),
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def get_current_session(request: Request) -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        yield session
