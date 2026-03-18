import uuid
from pathlib import Path

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from athena.models.image import Image, ImageSource
from athena.services.image import validate_base64_image
from athena.settings import get_settings


MAGIC_BYTES_TO_EXT = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"RIFF": "webp",
    b"BM": "bmp",
}


def _detect_extension(image_bytes: bytes) -> str:
    for magic, ext in MAGIC_BYTES_TO_EXT.items():
        if image_bytes.startswith(magic):
            return ext
    return "bin"


settings = get_settings()


def get_upload_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


async def upload_images(session: AsyncSession, images: list[str], prefix: str | None = None) -> list[Image]:
    result: list[Image] = []
    for image in images:
        image_bytes = validate_base64_image(image)
        if image_bytes is None:
            continue

        file_ext = _detect_extension(image_bytes)
        file_name = f"{prefix}_{uuid.uuid4()}.{file_ext}" if prefix else f"{uuid.uuid4()}.{file_ext}"
        file_path = get_upload_dir() / file_name
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(image_bytes)

        new_image = Image(file_path=str(file_path), source=ImageSource.USER)
        session.add(new_image)
        result.append(new_image)
        await session.flush()
    return result
