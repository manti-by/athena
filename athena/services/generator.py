import logging
from pathlib import Path
from typing import Any

from openrouter import OpenRouter
from openrouter.components import ChatResponse
from openrouter.errors import BadRequestResponseError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from athena.exceptions import AthenaException
from athena.models import ImageSource, Session, SessionItem, SessionItemImage
from athena.services.database import async_session_maker
from athena.services.upload import upload_images
from athena.settings import get_settings


logger = logging.getLogger(__name__)


settings = get_settings()


def extract_images(response: Any) -> list[str]:
    if not hasattr(response, "choices") or not response.choices:
        logger.warning("OpenRouter response missing or has empty choices")
        return []
    if not hasattr(response.choices[0], "message") or not response.choices[0].message:
        logger.warning("OpenRouter response missing message in first choice")
        return []
    message = response.choices[0].message
    if not hasattr(message, "images") or not message.images:
        logger.warning("OpenRouter response message missing images")
        return []
    return [
        x.image_url.url
        for x in message.images
        if hasattr(x, "image_url") and x.image_url and hasattr(x.image_url, "url")
    ]


async def generate_images(session_id: int) -> dict[str, list[str]]:
    async with async_session_maker() as session:
        stmt = (
            select(Session)
            .where(Session.id == session_id)
            .options(selectinload(Session.items).selectinload(SessionItem.images).joinedload(SessionItemImage.image))
        )
        result = await session.execute(stmt)
        current_session = result.scalar_one_or_none()

        if not current_session:
            raise ValueError(f"Session {session_id} not found")

        content = []
        for session_item in current_session.items:
            content.extend([{"type": "text", "text": session_item.text}])
            content.extend(await session_item.get_image_data_for_context())

        async with OpenRouter(api_key=settings.OPENROUTER_API_KEY) as client:
            try:
                response: ChatResponse = await client.chat.send_async(
                    model="google/gemini-3.1-flash-image-preview",
                    messages=[{"role": "user", "content": content}],
                    modalities=["image"],
                    session_id=f"metis-sesion-{current_session.id}",
                )
            except BadRequestResponseError as e:
                logger.error(f"OpenRouter error: {e}")
                raise AthenaException from e

        result_images = []
        if images := extract_images(response):
            for image in await upload_images(
                session=session,
                images=images,
                prefix=f"session_{current_session.id}_generated_",
                source=ImageSource.OPENROUTER,
            ):
                item_image = SessionItemImage(session_item_id=session_item.id, image_id=image.id)
                session.add(item_image)
                result_images.append(f"/media/{Path(image.file_path).name}")

            await session.commit()

    return {"images": result_images}
