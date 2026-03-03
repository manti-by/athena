from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app


class TestApi:
    @patch("main.openai.OpenAI")
    def test_post_prompt(self, client_mock):
        response_mock = MagicMock()
        response_mock.choices[0].message.content = "<image>"

        client_mock.chat.completions.create.return_value = response_mock

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/image/", json={"prompt": "Create an image"})

        assert response.status_code == 200
        assert client_mock.called
