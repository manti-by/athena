from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status

from athena.schemas.api import (
    SessionDetailResponse,
    SessionItemDetailResponse,
    SessionItemImageResponse,
    SessionResponse,
)
from athena.services.auth import get_user_from_request
from athena.services.database import create_user_session, delete_user_session, get_user_session, list_user_sessions


router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(request: Request) -> list[SessionResponse]:
    if not (user := await get_user_from_request(request=request)):
        raise HTTPException(status_code=403, detail="Forbidden")

    sessions = await list_user_sessions(user_id=user.id)
    return [SessionResponse(id=s.id, user_id=s.user_id, created_at=s.created_at) for s in sessions]


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(request: Request) -> SessionResponse:
    if not (user := await get_user_from_request(request=request)):
        raise HTTPException(status_code=403, detail="Forbidden")

    new_session = await create_user_session(user_id=user.id)
    return SessionResponse(id=new_session.id, user_id=new_session.user_id, created_at=new_session.created_at)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(request: Request, session_id: int) -> SessionDetailResponse:
    if not (user := await get_user_from_request(request=request)):
        raise HTTPException(status_code=403, detail="Forbidden")

    user_session = await get_user_session(session_id=session_id, user_id=user.id)
    if not user_session:
        raise HTTPException(status_code=404, detail="Session not found")

    items = []
    for item in user_session.items:
        item_images = []
        for si_image in item.images:
            file_name = Path(si_image.image.file_path).name
            item_images.append(
                SessionItemImageResponse(
                    id=si_image.image.id,
                    file_path=f"/media/{file_name}",
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
        id=user_session.id,
        user_id=user_session.user_id,
        created_at=user_session.created_at,
        items=items,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(request: Request, session_id: int) -> None:
    if not (user := await get_user_from_request(request=request)):
        raise HTTPException(status_code=403, detail="Forbidden")

    await delete_user_session(session_id=session_id, user_id=user.id)
