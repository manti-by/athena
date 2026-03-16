import base64
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from openrouter import OpenRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from athena.models import Image, Session, SessionItem, SessionItemImage, User
from athena.schemas.api import PromptRequest, SessionResponse
from athena.services.auth import get_current_user
from athena.services.database import async_session_maker
from athena.services.summarizer import SummarizerService
from athena.settings import get_settings


router = APIRouter(prefix="/api/v1", tags=["api"])
settings = get_settings()
summarizer = SummarizerService()


def get_upload_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


VALID_IMAGE_SIGNATURES = {
    b"\xff\xd8\xff",  # JPEG
    b"\x89PNG\r\n\x1a\n",  # PNG
    b"GIF87a",  # GIF
    b"GIF89a",  # GIF
    b"RIFF",  # WEBP
    b"BM",  # BMP
}


def validate_base64_image(data: str) -> bytes | None:
    try:
        img_data = base64.b64decode(data)
        if len(img_data) < 4:
            return None
        if not any(img_data.startswith(sig) for sig in VALID_IMAGE_SIGNATURES):
            return None
        return img_data
    except (base64.binascii.Error, ValueError):
        return None


async def get_user_from_request(request: Request, session: AsyncSession) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    return await get_current_user(session, token)


@router.get("/sessions/", response_model=list[SessionResponse])
async def list_sessions(request: Request) -> list[SessionResponse]:
    async with async_session_maker() as session:
        user = await get_user_from_request(request, session)
        if not user:
            return []

        stmt = select(Session).where(Session.user_id == user.id).order_by(Session.created_at.desc())
        result = await session.execute(stmt)
        sessions = result.scalars().all()

        return [SessionResponse(id=s.id, user_id=s.user_id, created_at=s.created_at) for s in sessions]


@router.post("/sessions/", response_model=SessionResponse | None)
async def create_session(request: Request) -> SessionResponse | None:
    async with async_session_maker() as session:
        user = await get_user_from_request(request, session)
        if not user:
            return None

        new_session = Session(user_id=user.id)
        session.add(new_session)
        await session.commit()
        await session.refresh(new_session)

        return SessionResponse(id=new_session.id, user_id=new_session.user_id, created_at=new_session.created_at)


async def generate_with_session(
    request: PromptRequest, session: AsyncSession, user: User, session_id: int | None = None
) -> dict[str, Any]:
    if session_id:
        stmt = select(Session).where(Session.id == session_id, Session.user_id == user.id)
        result = await session.execute(stmt)
        current_session = result.scalar_one_or_none()
        if not current_session:
            return {"error": "Session not found"}
    else:
        current_session = Session(user_id=user.id)
        session.add(current_session)
        await session.commit()
        await session.refresh(current_session)

    stmt = select(SessionItem).where(SessionItem.session_id == current_session.id).order_by(SessionItem.created_at)
    result = await session.execute(stmt)
    existing_items = result.scalars().all()

    uploaded_image_paths: list[str] = []
    if request.images:
        for idx, img_data in enumerate(request.images):
            image_bytes = validate_base64_image(img_data)
            if image_bytes is None:
                continue
            upload_dir = get_upload_dir()
            file_path = upload_dir / f"session_{current_session.id}_{len(existing_items)}_{idx}.jpg"
            file_path.write_bytes(image_bytes)

            new_image = Image(file_path=str(file_path))
            session.add(new_image)
            await session.flush()
            uploaded_image_paths.append(str(file_path))

    new_session_item = SessionItem(session_id=current_session.id, text=request.prompt)
    session.add(new_session_item)
    await session.flush()

    for img_path in uploaded_image_paths:
        stmt = select(Image).where(Image.file_path == img_path)
        result = await session.execute(stmt)
        image = result.scalar_one_or_none()
        if image:
            session_item_image = SessionItemImage(session_item_id=new_session_item.id, image_id=image.id)
            session.add(session_item_image)

    await session.commit()

    all_items_stmt = (
        select(SessionItem).where(SessionItem.session_id == current_session.id).order_by(SessionItem.created_at)
    )
    result = await session.execute(all_items_stmt)
    all_items = result.scalars().all()
    all_items_data = [{"id": item.id, "text": item.text} for item in all_items]

    summary = await summarizer.summarize_session(all_items_data, uploaded_image_paths)

    content: list[dict[str, Any]] = []
    if summary:
        content.append({"type": "text", "text": f"Context: {summary}\n\nCurrent request: {request.prompt}"})
    else:
        content.append({"type": "text", "text": request.prompt})

    if request.images:
        for img in request.images:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})

    async with OpenRouter(api_key=settings.OPENROUTER_API_KEY) as client:
        response = await client.chat.send_async(
            model="google/gemini-3-pro-image-preview",
            messages=[{"role": "user", "content": content}],
            modalities=["image"],
        )

    images = response.choices[0].message.images or []
    return {"images": [x.image_url.url for x in images], "session_id": current_session.id}


async def generate_without_session(request: PromptRequest) -> dict[str, Any]:
    content = [{"type": "text", "text": request.prompt}]
    if request.images:
        for img in request.images:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})

    async with OpenRouter(api_key=settings.OPENROUTER_API_KEY) as client:
        response = await client.chat.send_async(
            model="google/gemini-3-pro-image-preview",
            messages=[{"role": "user", "content": content}],
            modalities=["image"],
        )

    images = response.choices[0].message.images or []
    return {"images": [x.image_url.url for x in images]}


@router.post("/image/{session_id}")
@router.post("/image/")
async def generate_image(
    request: PromptRequest, http_request: Request, session_id: int | None = None
) -> dict[str, Any]:
    token = http_request.cookies.get("access_token")

    if token:
        async with async_session_maker() as session:
            user = await get_current_user(session, token)
            if user:
                return await generate_with_session(request, session, user, session_id)

    return await generate_without_session(request)
