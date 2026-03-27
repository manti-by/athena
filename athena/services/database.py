import os
from pathlib import Path

from sqlalchemy import Sequence, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from athena.models import Session
from athena.models.session_item import SessionItem
from athena.models.session_item_image import SessionItemImage
from athena.schemas.api import PromptRequest
from athena.services.upload import upload_images
from athena.settings import get_settings


settings = get_settings()

async_session_maker = async_sessionmaker(
    create_async_engine(settings.DATABASE_URL, echo=False),
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_user_session(user_id: int) -> Session:
    async with async_session_maker() as session:
        current_session = Session(user_id=user_id)
        session.add(current_session)
        await session.commit()
        return current_session


async def get_or_create_user_session(user_id: int, session_id: int | None = None) -> Session:
    async with async_session_maker() as session:
        if session_id:
            stmt = (
                select(Session)
                .where(Session.id == session_id, Session.user_id == user_id)
                .options(selectinload(Session.items))
            )
            result = await session.execute(stmt)
            current_session = result.scalar_one_or_none()

            if not current_session:
                raise ValueError(f"Session {session_id} not found")

        else:
            current_session = Session(user_id=user_id)
            session.add(current_session)
            await session.commit()

    return current_session


async def update_user_session(session_id: int, prompt_request: PromptRequest):
    async with async_session_maker() as session:
        session_item = SessionItem(session_id=session_id, text=prompt_request.prompt)
        session.add(session_item)

        if prompt_request.images:
            for image in await upload_images(
                session=session, images=prompt_request.images, prefix=f"session_{session_id}_upload_"
            ):
                session.add(SessionItemImage(session_item_id=session_item.id, image_id=image.id))

        await session.commit()


async def list_user_sessions(user_id: int) -> Sequence[Session]:
    async with async_session_maker() as session:
        stmt = select(Session).where(Session.user_id == user_id).order_by(Session.created_at.desc())
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_user_session(session_id: int, user_id: int) -> Session | None:
    async with async_session_maker() as session:
        stmt = (
            select(Session)
            .where(Session.id == session_id, Session.user_id == user_id)
            .options(selectinload(Session.items).selectinload(SessionItem.images).selectinload(SessionItemImage.image))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def delete_user_session(session_id: int, user_id: int) -> bool:
    async with async_session_maker() as session:
        stmt = (
            select(Session)
            .where(Session.id == session_id, Session.user_id == user_id)
            .options(selectinload(Session.items).selectinload(SessionItem.images).selectinload(SessionItemImage.image))
        )
        result = await session.execute(stmt)

        if not (user_session := result.scalar_one_or_none()):
            return False

        for item in user_session.items:
            for si_image in item.images:
                image_path = Path(settings.UPLOAD_DIR) / si_image.image.file_path
                if image_path.exists():
                    try:
                        os.remove(image_path)
                    except OSError:
                        pass
                await session.delete(si_image.image)
            await session.delete(item)
        await session.delete(user_session)
        await session.commit()

        return True
