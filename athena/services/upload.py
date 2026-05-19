import logging
import os
import tempfile
import uuid
from pathlib import Path

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from athena.models.image import Image, ImageSource
from athena.services.image import validate_base64_image
from athena.services.thumbnail import generate_thumbnails_sync
from athena.settings import get_settings


logger = logging.getLogger(__name__)


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
    image_bytes_map: dict[str, bytes] = {}

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
        tmp = tempfile.NamedTemporaryFile(dir=settings.UPLOAD_DIR, delete=False, suffix=".tmp")
        try:
            tmp.write(image_bytes)
            tmp.close()
            os.chmod(tmp.name, 0o644)
            tmp_path = Path(tmp.name)
        except Exception:
            tmp.close()
            raise

        pending.append((tmp_path, Path(settings.UPLOAD_DIR) / file_name))
        new_image = Image(file_path=file_name, source=source)
        session.add(new_image)
        result.append(new_image)
        image_bytes_map[file_name] = image_bytes

    if validation_errors:
        for tmp_path, _ in pending:
            tmp_path.unlink(missing_ok=True)
        raise ImageValidationError(validation_errors)

    if pending:
        for tmp_path, file_path in pending:
            tmp_path.rename(file_path)

        for img in result:
            if img.file_path in image_bytes_map:
                try:
                    generate_thumbnails_sync(img.file_path, image_bytes_map[img.file_path])
                    logger.info(f"Thumbnails generated for image #{img.file_path}")
                except OSError as e:
                    logger.warning("Failed to generate thumbnails for %s: %s", img.file_path, e)

        await session.commit()

    return result
