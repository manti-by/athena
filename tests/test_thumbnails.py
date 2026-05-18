def create_test_image(width: int, height: int, img_format: str = "PNG", color: tuple = (255, 0, 0)):
    from PIL import Image as PILImage

    if len(color) == 4:
        img = PILImage.new("RGBA", (width, height), color)
    else:
        img = PILImage.new("RGB", (width, height), color)
    return img


def img_to_bytes(img, img_format: str = "PNG") -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    img.save(buffer, format=img_format)
    return buffer.getvalue()


class TestThumbnailGeneration:
    def test_generate_thumbnails_returns_correct_names(self):
        import os
        import tempfile

        tmp = tempfile.mkdtemp()
        upload_dir = os.path.join(tmp, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        os.environ["UPLOAD_DIR"] = upload_dir

        from athena.settings import get_settings

        get_settings.cache_clear()

        from athena.services.thumbnail import generate_thumbnails_sync

        img = create_test_image(16, 16)
        img_bytes = img_to_bytes(img)

        thumb_100, thumb_600 = generate_thumbnails_sync("test_image.png", img_bytes)

        assert thumb_100 == "test_image_thumb_100.jpg"
        assert thumb_600 == "test_image_thumb_600.jpg"

    def test_thumbnail_handles_jpeg_input(self):
        import os
        import tempfile

        tmp = tempfile.mkdtemp()
        upload_dir = os.path.join(tmp, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        os.environ["UPLOAD_DIR"] = upload_dir

        from athena.settings import get_settings

        get_settings.cache_clear()

        from athena.services.thumbnail import generate_thumbnails_sync

        img = create_test_image(16, 16, img_format="JPEG")
        img_bytes = img_to_bytes(img)

        thumb_100, thumb_600 = generate_thumbnails_sync("test.jpg", img_bytes)

        assert thumb_100 == "test_thumb_100.jpg"
        assert thumb_600 == "test_thumb_600.jpg"

    def test_thumbnail_naming_preserves_base_name(self):
        import os
        import tempfile

        tmp = tempfile.mkdtemp()
        upload_dir = os.path.join(tmp, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        os.environ["UPLOAD_DIR"] = upload_dir

        from athena.settings import get_settings

        get_settings.cache_clear()

        from athena.services.thumbnail import generate_thumbnails_sync

        img = create_test_image(16, 16)
        img_bytes = img_to_bytes(img)

        thumb_100, thumb_600 = generate_thumbnails_sync("my_custom_image.png", img_bytes)

        assert thumb_100 == "my_custom_image_thumb_100.jpg"
        assert thumb_600 == "my_custom_image_thumb_600.jpg"
