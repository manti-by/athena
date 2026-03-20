import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from athena.models import Session
from athena.models.session_item import SessionItem
from athena.models.session_item_image import SessionItemImage
from athena.schemas.api import (
    SessionDetailResponse,
    SessionItemDetailResponse,
    SessionItemImageResponse,
    SessionResponse,
)
from athena.services.auth import get_user_from_request
from athena.services.database import async_session_maker


router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(request: Request) -> list[SessionResponse]:
    async with async_session_maker() as session:
        if not (user := await get_user_from_request(request=request, session=session)):
            raise HTTPException(status_code=403, detail="Forbidden")

        stmt = select(Session).where(Session.user_id == user.id).order_by(Session.created_at.desc())
        result = await session.execute(stmt)
        sessions = result.scalars().all()

        return [SessionResponse(id=s.id, user_id=s.user_id, created_at=s.created_at) for s in sessions]


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(request: Request) -> SessionResponse:
    async with async_session_maker() as session:
        if not (user := await get_user_from_request(request=request, session=session)):
            raise HTTPException(status_code=403, detail="Forbidden")

        new_session = Session(user_id=user.id)
        session.add(new_session)
        await session.commit()
        await session.refresh(new_session)

        return SessionResponse(id=new_session.id, user_id=new_session.user_id, created_at=new_session.created_at)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(request: Request, session_id: int) -> SessionDetailResponse:
    async with async_session_maker() as session:
        if not (user := await get_user_from_request(request=request, session=session)):
            raise HTTPException(status_code=403, detail="Forbidden")

        from athena.models.session_item import SessionItem

        stmt = (
            select(Session)
            .where(Session.id == session_id, Session.user_id == user.id)
            .options(selectinload(Session.items).selectinload(SessionItem.images).selectinload(SessionItemImage.image))
        )
        result = await session.execute(stmt)
        db_session = result.scalar_one_or_none()

        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        items = []
        for item in db_session.items:
            item_images = []
            for si_image in item.images:
                item_images.append(
                    SessionItemImageResponse(
                        id=si_image.image.id,
                        file_path=f"/api/v1/image/file/{si_image.image.id}",
                        source=si_image.image.source.value,
                        created_at=si_image.image.created_at,
                    )
                )
            items.append(
                SessionItemDetailResponse(
                    id=item.id,
                    session_id=item.session_id,
                    text=item.text,
                    created_at=item.created_at,
                    images=item_images,
                )
            )

        return SessionDetailResponse(
            id=db_session.id,
            user_id=db_session.user_id,
            created_at=db_session.created_at,
            items=items,
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(request: Request, session_id: int) -> None:
    async with async_session_maker() as session:
        if not (user := await get_user_from_request(request=request, session=session)):
            raise HTTPException(status_code=403, detail="Forbidden")

        stmt = (
            select(Session)
            .where(Session.id == session_id, Session.user_id == user.id)
            .options(selectinload(Session.items).selectinload(SessionItem.images).selectinload(SessionItemImage.image))
        )
        result = await session.execute(stmt)
        db_session = result.scalar_one_or_none()

        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        for item in db_session.items:
            for si_image in item.images:
                image_path = Path(si_image.image.file_path)
                if image_path.exists():
                    try:
                        os.remove(image_path)
                    except OSError:
                        pass
                await session.delete(si_image.image)
            await session.delete(item)
        await session.delete(db_session)
        await session.commit()
