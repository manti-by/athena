import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from athena.models import Session, SessionItem, SessionItemImage
from athena.services.database import async_session_maker


async def main(session_id: int = 29):
    stmt = (
        select(Session)
        .where(Session.id == session_id)
        .options(selectinload(Session.items).selectinload(SessionItem.images).selectinload(SessionItemImage.image))
    )

    async with async_session_maker() as session:
        result = await session.execute(stmt)
        current_session = result.scalar_one_or_none()

        if current_session is None:
            print(f"No session found with #{session_id}")
            return

        print(f"Found session #{current_session.id}")
        print(f"Session item count = {len(current_session.items)}")

        content = [{"type": "text", "text": "text"}]
        for session_item in current_session.items:
            print(f"Session item #{session_item.id}")
            print(f"Session item images count = {len(session_item.images)}")

            content.extend(await session_item.get_image_data_for_context())
        print(f"content length = {len(content)}")


if __name__ == "__main__":
    asyncio.run(main())
