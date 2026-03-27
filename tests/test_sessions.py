import pytest

from tests.conftest import get_authenticated_client, get_unauthenticated_client


class TestSessions:
    @pytest.mark.skip(reason="Async event loop isolation issue with TestClient")
    def test_list_sessions(self):
        client = get_authenticated_client()
        response = client.get("/api/v1/sessions/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_sessions_not_authenticated(self):
        client = get_unauthenticated_client()
        response = client.get("/api/v1/sessions/")
        assert response.status_code == 403

    @pytest.mark.skip(reason="Async event loop isolation issue with TestClient")
    def test_create_session(self):
        client = get_authenticated_client()
        response = client.post("/api/v1/sessions/")
        assert response.status_code == 201
        assert "id" in response.json()

    def test_create_session_not_authenticated(self):
        client = get_unauthenticated_client()
        response = client.post("/api/v1/sessions/")
        assert response.status_code == 403
