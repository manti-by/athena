from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage

from athena.settings import get_settings


def generate_thumbnails_sync(file_path: str, image_bytes: bytes) -> tuple[str, str]:
    settings = get_settings()

    img = PILImage.open(BytesIO(image_bytes))

    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = PILImage.new("RGBA", img.size, (255, 255, 255))
        alpha_composite = PILImage.alpha_composite(background, img)
        img = alpha_composite.convert("RGB")
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    base_name = Path(file_path).stem
    ext = "jpg"

    thumb_100 = create_thumbnail(img, 100, 100)
    thumb_100_path = f"{base_name}_thumb_100.{ext}"
    thumb_100_full = Path(settings.UPLOAD_DIR) / thumb_100_path
    save_jpeg(thumb_100, thumb_100_full, quality=60)

    thumb_600 = create_thumbnail(img, 600, 600)
    thumb_600_path = f"{base_name}_thumb_600.{ext}"
    thumb_600_full = Path(settings.UPLOAD_DIR) / thumb_600_path
    save_jpeg(thumb_600, thumb_600_full, quality=75)

    return thumb_100_path, thumb_600_path


def create_thumbnail(img: PILImage.Image, width: int, height: int) -> PILImage.Image:
    target_ratio = width / height
    img_width, img_height = img.size
    img_ratio = img_width / img_height

    if img_ratio > target_ratio:
        new_height = img_height
        new_width = int(new_height * target_ratio)
        left = (img_width - new_width) // 2
        top = 0
        right = left + new_width
        bottom = new_height
    else:
        new_width = img_width
        new_height = int(new_width / target_ratio)
        top = (img_height - new_height) // 2
        left = 0
        right = new_width
        bottom = top + new_height

    cropped = img.crop((left, top, right, bottom))
    return cropped.resize((width, height), PILImage.Resampling.LANCZOS)


def save_jpeg(img: PILImage.Image, path: Path, quality: int) -> None:
    img.save(path, format="JPEG", quality=quality, optimize=True)
