import tempfile
import uuid
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from athena.models.image import Image, ImageSource
from athena.services.image import validate_base64_image
from athena.settings import get_settings


_MAGIC_BYTES_TO_EXT = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"RIFF": "webp",
    b"BM": "bmp",
}


def _detect_extension(image_bytes: bytes) -> str:
    for magic, ext in _MAGIC_BYTES_TO_EXT.items():
        if image_bytes.startswith(magic):
            return ext
    return "bin"


settings = get_settings()


def get_upload_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


async def upload_images(
    session: AsyncSession, images: list[str], prefix: str | None = None, source: ImageSource = ImageSource.USER
) -> list[Image]:
    result: list[Image] = []
    pending: list[tuple[Path, Path]] = []

    for image in images:
        image_bytes = validate_base64_image(image)
        if image_bytes is None:
            continue

        file_ext = _detect_extension(image_bytes)
        file_name = f"{prefix}_{uuid.uuid4()}.{file_ext}" if prefix else f"{uuid.uuid4()}.{file_ext}"
        file_path = get_upload_dir() / file_name

        tmp = tempfile.NamedTemporaryFile(dir=get_upload_dir(), delete=False, suffix=".tmp")
        try:
            tmp.write(image_bytes)
            tmp.close()
            tmp_path = Path(tmp.name)
        except Exception:
            tmp.close()
            raise

        pending.append((tmp_path, file_path))
        new_image = Image(file_path=str(file_path), source=source)
        session.add(new_image)
        result.append(new_image)

    if pending:
        await session.flush()

        @event.listens_for(session.sync_session, "after_commit")
        def on_commit(_session: AsyncSession) -> None:
            for tmp_path, file_path in pending:
                tmp_path.rename(file_path)

        @event.listens_for(session.sync_session, "after_rollback")
        def on_rollback(_session: AsyncSession) -> None:
            for tmp_path, _ in pending:
                tmp_path.unlink(missing_ok=True)

    return result
