import base64
import binascii


VALID_IMAGE_SIGNATURES = {
    b"\xff\xd8\xff",  # JPEG
    b"\x89PNG\r\n\x1a\n",  # PNG
    b"GIF87a",  # GIF
    b"GIF89a",  # GIF
    b"BM",  # BMP
}


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
