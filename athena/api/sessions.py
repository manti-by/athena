from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from athena.models import Session
from athena.schemas.api import SessionResponse
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
