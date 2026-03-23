import asyncio
import tempfile
import uuid
from pathlib import Path

import httpx
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
    b"BM": "bmp",
}


class ImageValidationError(Exception):
    def __init__(self, errors: list[dict[str, str | int]]) -> None:
        self.errors = errors
        error_messages = [e["error"] for e in errors]
        super().__init__(f"Image validation failed: {error_messages}")


def _detect_extension(image_bytes: bytes) -> str:
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "webp"
    for magic, ext in _MAGIC_BYTES_TO_EXT.items():
        if image_bytes.startswith(magic):
            return ext
    return "bin"


settings = get_settings()


async def upload_images(
    session: AsyncSession, images: list[str], prefix: str | None = None, source: ImageSource = ImageSource.USER
) -> list[Image]:
    result: list[Image] = []
    pending: list[tuple[Path, Path]] = []
    validation_errors: list[dict[str, str | int]] = []

    for idx, image in enumerate(images):
        image_bytes = validate_base64_image(image)
        if image_bytes is None:
            if image.startswith("http://") or image.startswith("https://"):
                try:
                    response = httpx.get(image, timeout=10)
                    response.raise_for_status()
                    image_bytes = response.content
                except (httpx.HTTPError, httpx.TimeoutException):
                    validation_errors.append({"index": idx, "error": "Failed to download image from URL"})
                    continue
                if not (
                    any(image_bytes.startswith(sig) for sig in _MAGIC_BYTES_TO_EXT)
                    or (image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP")
                ):
                    validation_errors.append({"index": idx, "error": "Downloaded image has unsupported format"})
                    continue
            elif image.startswith("data:"):
                if ";base64," in image:
                    image = image.split(";base64,", 1)[1]
                    image_bytes = validate_base64_image(image)
                    if image_bytes is None:
                        validation_errors.append(
                            {"index": idx, "error": "Invalid base64 image data or unsupported image format"}
                        )
                        continue
                else:
                    validation_errors.append({"index": idx, "error": "Unsupported data URL format"})
                    continue
            else:
                validation_errors.append(
                    {"index": idx, "error": "Invalid base64 image data or unsupported image format"}
                )
                continue

        file_ext = _detect_extension(image_bytes)
        file_name = f"{prefix}_{uuid.uuid4()}.{file_ext}" if prefix else f"{uuid.uuid4()}.{file_ext}"
        file_name = f"uploads/{file_name}"

        tmp = tempfile.NamedTemporaryFile(dir=settings.UPLOAD_DIR, delete=False, suffix=".tmp")
        try:
            tmp.write(image_bytes)
            tmp.close()
            tmp_path = Path(tmp.name)
        except Exception:
            tmp.close()
            raise

        pending.append((tmp_path, Path(settings.UPLOAD_DIR) / file_name))
        new_image = Image(file_path=file_name, source=source)
        session.add(new_image)
        result.append(new_image)

    if validation_errors:
        for tmp_path, _ in pending:
            tmp_path.unlink(missing_ok=True)
        raise ImageValidationError(validation_errors)

    if pending:
        await session.flush()

        def on_commit(_session: AsyncSession) -> None:
            for tmp_path, file_path in pending:
                tmp_path.rename(file_path)
            loop = asyncio.get_event_loop()
            loop.call_soon(lambda: event.remove(session.sync_session, "after_commit", on_commit))

        def on_rollback(_session: AsyncSession) -> None:
            for tmp_path, _ in pending:
                tmp_path.unlink(missing_ok=True)
            loop = asyncio.get_event_loop()
            loop.call_soon(lambda: event.remove(session.sync_session, "after_rollback", on_rollback))

        event.listen(session.sync_session, "after_commit", on_commit)
        event.listen(session.sync_session, "after_rollback", on_rollback)

    return result
