from unittest.mock import MagicMock, patch

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
