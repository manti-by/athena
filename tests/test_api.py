from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from main import app


class TestRoot:
    def test_root_returns_html(self):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_default_message_when_no_template(self):
        with patch("main.templates_dir") as mock_dir:
            mock_dir.__truediv__ = MagicMock(return_value=MagicMock(exists=MagicMock(return_value=False)))
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/")
            assert response.text == "<h1>No template found</h1>"


class TestImageGeneration:
    @patch("athena.routes.api.OpenRouter")
    def test_generate_image_returns_images(self, client_mock):
        image_mock = MagicMock()
        image_mock.image_url.url = "https://example.com/image.png"

        response_mock = MagicMock()
        response_mock.choices[0].message.images = [image_mock]

        mock_client = AsyncMock()
        mock_client.chat.send_async = AsyncMock(return_value=response_mock)
        client_mock.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        client_mock.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/image/", json={"prompt": "Create an image"})

        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert len(data["images"]) == 1
        assert data["images"][0] == "https://example.com/image.png"

    @patch("athena.routes.api.OpenRouter")
    def test_generate_image_uses_correct_model(self, client_mock):
        response_mock = MagicMock()
        response_mock.choices[0].message.images = []

        mock_client = AsyncMock()
        mock_client.chat.send_async = AsyncMock(return_value=response_mock)
        client_mock.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        client_mock.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        client.post("/api/v1/image/", json={"prompt": "Test prompt"})

        call_args = mock_client.chat.send_async.call_args
        assert call_args.kwargs["model"] == "google/gemini-3-pro-image-preview"

    @patch("athena.routes.api.OpenRouter")
    def test_generate_image_sends_correct_messages(self, client_mock):
        response_mock = MagicMock()
        response_mock.choices[0].message.images = []

        mock_client = AsyncMock()
        mock_client.chat.send_async = AsyncMock(return_value=response_mock)
        client_mock.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        client_mock.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        client.post("/api/v1/image/", json={"prompt": "My custom prompt"})

        call_args = mock_client.chat.send_async.call_args
        assert call_args.kwargs["messages"] == [
            {"role": "user", "content": [{"type": "text", "text": "My custom prompt"}]}
        ]

    @patch("athena.routes.api.OpenRouter")
    def test_generate_image_requests_image_modality(self, client_mock):
        response_mock = MagicMock()
        response_mock.choices[0].message.images = []

        mock_client = AsyncMock()
        mock_client.chat.send_async = AsyncMock(return_value=response_mock)
        client_mock.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        client_mock.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        client.post("/api/v1/image/", json={"prompt": "Test"})

        call_args = mock_client.chat.send_async.call_args
        assert call_args.kwargs["modalities"] == ["image"]

    @patch("athena.routes.api.OpenRouter")
    def test_generate_image_with_images(self, client_mock):
        response_mock = MagicMock()
        response_mock.choices[0].message.images = []

        mock_client = AsyncMock()
        mock_client.chat.send_async = AsyncMock(return_value=response_mock)
        client_mock.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        client_mock.return_value.__aexit__ = AsyncMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        client.post("/api/v1/image/", json={"prompt": "Describe this image", "images": ["base64encodedimage"]})

        call_args = mock_client.chat.send_async.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "user"
        content = messages[0]["content"]
        assert content[0] == {"type": "text", "text": "Describe this image"}
        assert content[1] == {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,base64encodedimage"}}
