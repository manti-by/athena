from typing import Any

from fastapi import APIRouter, HTTPException, Request

from athena.exceptions import AthenaException
from athena.schemas.api import PromptRequest
from athena.services.auth import get_user_from_request
from athena.services.database import get_or_create_user_session, update_user_session
from athena.services.generator import generate_images


router = APIRouter(prefix="/api/v1/image", tags=["images"])


@router.post("/")
@router.post("/{session_id}")
async def generate_image(
    prompt_request: PromptRequest, request: Request, session_id: int | None = None
) -> dict[str, Any]:
    if not (user := await get_user_from_request(request=request)):
        raise HTTPException(status_code=403, detail="Forbidden")

    current_session = await get_or_create_user_session(user_id=user.id, session_id=session_id)
    await update_user_session(prompt_request=prompt_request, session_id=current_session.id)

    try:
        return await generate_images(session_id=current_session.id)
    except AthenaException:
        return {"error": "Provider returned an error please check logs for more details"}
