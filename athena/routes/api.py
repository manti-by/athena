from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from athena.models import Session
from athena.schemas.api import PromptRequest, SessionResponse
from athena.services.auth import get_user_from_request
from athena.services.database import async_session_maker
from athena.services.generator import generate_images
from athena.settings import get_settings


router = APIRouter(prefix="/api/v1", tags=["api"])
settings = get_settings()


@router.get("/sessions/", response_model=list[SessionResponse])
async def list_sessions(request: Request) -> list[SessionResponse]:
    async with async_session_maker() as session:
        if not (user := await get_user_from_request(request=request, session=session)):
            raise HTTPException(status_code=403, detail="Forbidden")

        stmt = select(Session).where(Session.user_id == user.id).order_by(Session.created_at.desc())
        result = await session.execute(stmt)
        sessions = result.scalars().all()

        return [SessionResponse(id=s.id, user_id=s.user_id, created_at=s.created_at) for s in sessions]


@router.post("/sessions/", response_model=SessionResponse | None)
async def create_session(request: Request) -> SessionResponse | None:
    async with async_session_maker() as session:
        if not (user := await get_user_from_request(request=request, session=session)):
            raise HTTPException(status_code=403, detail="Forbidden")

        new_session = Session(user_id=user.id)
        session.add(new_session)
        await session.commit()
        await session.refresh(new_session)

        return SessionResponse(id=new_session.id, user_id=new_session.user_id, created_at=new_session.created_at)


@router.post("/image/{session_id}")
@router.post("/image")
async def generate_image(
    prompt_request: PromptRequest, request: Request, session_id: int | None = None
) -> dict[str, list[str]]:
    async with async_session_maker() as session:
        if not (user := await get_user_from_request(request=request, session=session)):
            raise HTTPException(status_code=403, detail="Forbidden")

        return await generate_images(
            prompt_request=prompt_request,
            session=session,
            user=user,
            session_id=session_id,
        )
