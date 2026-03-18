from fastapi import APIRouter, HTTPException, Request

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
