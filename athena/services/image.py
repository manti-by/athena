import base64
import binascii
import logging
import mimetypes

import aiofiles


VALID_IMAGE_SIGNATURES = {
    b"\xff\xd8\xff",  # JPEG
    b"\x89PNG\r\n\x1a\n",  # PNG
    b"GIF87a",  # GIF
    b"GIF89a",  # GIF
    b"BM",  # BMP
}

logger = logging.getLogger(__name__)


def _is_webp(data: bytes) -> bool:
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"


def validate_base64_image(data: str) -> bytes | None:
    try:
        img_data = base64.b64decode(data)
        if len(img_data) < 4:
            return None
        if not (any(img_data.startswith(sig) for sig in VALID_IMAGE_SIGNATURES) or _is_webp(img_data)):
            return None
        return img_data
    except (binascii.Error, ValueError):
        return None


async def read_image_mimetype_and_data(image_path: str) -> tuple[str, str] | None:
    try:
        async with aiofiles.open(image_path, "rb") as image_file:
            image_bytes = await image_file.read()
    except (FileNotFoundError, PermissionError) as e:
        logger.warning(f"Could not read image file {image_path}: {e}")
        return

    encoded_bytes = base64.b64encode(image_bytes)
    encoded_string = encoded_bytes.decode("utf-8")

    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "image/jpeg"

    return mime_type, encoded_string
