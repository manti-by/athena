from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from athena.schemas.api import PromptRequest
from athena.services.auth import get_user_from_request
from athena.services.database import async_session_maker
from athena.services.generator import generate_images


router = APIRouter(prefix="/api/v1/image", tags=["images"])


@router.post("/")
@router.post("/{session_id}")
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


@router.get("/file/{image_id}")
async def get_image_file(image_id: int, request: Request) -> FileResponse:
    async with async_session_maker() as session:
        if not (user := await get_user_from_request(request=request, session=session)):
            raise HTTPException(status_code=403, detail="Forbidden")

        from sqlalchemy import select

        from athena.models import Image, Session, SessionItem, SessionItemImage

        stmt = (
            select(Image)
            .join(SessionItemImage, SessionItemImage.image_id == Image.id)
            .join(SessionItem, SessionItem.id == SessionItemImage.session_item_id)
            .join(Session, Session.id == SessionItem.session_id)
            .where(Image.id == image_id, Session.user_id == user.id)
        )
        result = await session.execute(stmt)
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        file_path = Path(image.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image file not found")

        return FileResponse(file_path)
