from openrouter import OpenRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from athena.models import Session, SessionItem, SessionItemImage, User
from athena.schemas.api import PromptRequest
from athena.services.summarizer import summarize_session
from athena.services.upload import upload_images
from athena.settings import get_settings


settings = get_settings()


async def generate_images(
    prompt_request: PromptRequest, session: AsyncSession, user: User, session_id: int | None = None
) -> dict[str, list[str]]:
    current_session = None

    if session_id:
        stmt = (
            select(Session)
            .where(Session.id == session_id, Session.user_id == user.id)
            .options(selectinload(Session.items))
        )
        result = await session.execute(stmt)
        current_session = result.scalar_one_or_none()

    if not current_session:
        current_session = Session(user_id=user.id)
        session.add(current_session)
        await session.commit()

    session_item = SessionItem(session_id=current_session.id, text=prompt_request.prompt)
    session.add(session_item)
    await session.flush()

    stmt = select(Session).where(Session.id == current_session.id).options(selectinload(Session.items))
    result = await session.execute(stmt)
    current_session = result.scalar_one()
    input_text = "\n".join([item.text for item in current_session.items])

    text = prompt_request.prompt
    if summary := await summarize_session(input_text=input_text):
        text = summary

    content = [{"type": "text", "text": text}]
    if prompt_request.images:
        for image in await upload_images(
            session=session, images=prompt_request.images, prefix=f"session_{current_session.id}_upload_"
        ):
            session.add(SessionItemImage(session_item_id=session_item.id, image_id=image.id))
        await session.commit()

    from athena.models import SessionItem as SessionItemModel

    stmt = (
        select(SessionItemModel)
        .where(SessionItemModel.id == session_item.id)
        .options(selectinload(SessionItemModel.images).selectinload(SessionItemImage.image))
    )
    result = await session.execute(stmt)
    session_item = result.scalar_one()
    if session_item.images:
        content.extend(await session_item.get_image_data_for_context())

    async with OpenRouter(api_key=settings.OPENROUTER_API_KEY) as client:
        response = await client.chat.send_async(
            model="google/gemini-3-pro-image-preview",
            messages=[{"role": "user", "content": content}],
            modalities=["image"],
        )

    images = [x.image_url.url for x in response.choices[0].message.images]
    for image in await upload_images(session=session, images=images, prefix=f"session_{current_session.id}_generated_"):
        session.add(SessionItemImage(session_item_id=session_item.id, image_id=image.id))
    await session.commit()

    stmt = (
        select(SessionItemModel)
        .where(SessionItemModel.id == session_item.id)
        .options(selectinload(SessionItemModel.images).selectinload(SessionItemImage.image))
    )
    result = await session.execute(stmt)
    session_item = result.scalar_one()

    return {"images": await session_item.get_image_data_list()}
