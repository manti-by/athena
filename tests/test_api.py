from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app


class TestApi:
    @patch("main.OpenRouter")
    def test_post_prompt(self, client_mock):
        response_mock = MagicMock()
        response_mock.choices[0].message.content = "<image>"

        mock_client = MagicMock()
        mock_client.chat.send.return_value = response_mock
        client_mock.return_value.__enter__ = MagicMock(return_value=mock_client)
        client_mock.return_value.__exit__ = MagicMock(return_value=False)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/image/", json={"prompt": "Create an image"})

        assert response.status_code == 200
        assert mock_client.chat.send.called
