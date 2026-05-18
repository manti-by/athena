#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from athena.models.image import Image
from athena.services.thumbnail import generate_thumbnails_sync
from athena.settings import get_settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-6s %(name)-12s %(message)s",
)
logger = logging.getLogger(__name__)


async def fix_thumbnails() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_maker() as session:
        result = await session.execute(select(Image))
        images = result.unique().scalars().all()
    if not images:
        logger.info("There are no images in database.")
        return

    logger.info(f"Found {len(images)} images.")
    upload_dir = Path(settings.UPLOAD_DIR)
    failed = updated = 0
    for image in images:
        file_path = upload_dir / image.file_path
        if not file_path.exists():
            logger.warning(f"Image file not found: {file_path}")
            failed += 1
            continue

        try:
            image_bytes = file_path.read_bytes()
            generate_thumbnails_sync(image.file_path, image_bytes)
            logger.info(f"Thumbnails are generated for image #{image.id}: {image.file_path}")
            updated += 1

        except Exception as e:  # noqa
            logger.error(f"Failed to generate thumbnails for {image.file_path}: {e}")
            failed += 1

    logger.info(f"Done. Updated: {updated}, Failed: {failed}")


if __name__ == "__main__":
    asyncio.run(fix_thumbnails())
