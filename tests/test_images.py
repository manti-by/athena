from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import get_authenticated_client, get_unauthenticated_client


class TestImageGeneration:
    @patch("athena.services.generator.upload_images")
    @patch("athena.services.generator.OpenRouter")
    def test_generate_image(self, router_mock, upload_images_mock):
        image_mock = MagicMock()
        image_mock.image_url.url = "https://example.com/image.jpg"

        response_mock = MagicMock()
        response_mock.choices[0].message.images = [image_mock]

        client_mock = MagicMock()
        client_mock.chat.send_async = AsyncMock(return_value=response_mock)

        router_mock.return_value.__aenter__ = AsyncMock(return_value=client_mock)
        router_mock.return_value.__aexit__ = AsyncMock(return_value=None)

        client = get_authenticated_client()

        response = client.post("/api/v1/image", json={"prompt": "A beautiful sunset"})
        assert response.status_code == 200

    def test_generate_image_not_authenticated(self):
        client = get_unauthenticated_client()

        response = client.post("/api/v1/image", json={"prompt": "A beautiful sunset"})
        assert response.status_code == 403

    def test_generate_image_with_session_id_not_authenticated(self):
        client = get_unauthenticated_client()

        response = client.post("/api/v1/image/1", json={"prompt": "A beautiful sunset"})
        assert response.status_code == 403
