from tests.conftest import create_auth_token, create_test_user, get_authenticated_client, get_unauthenticated_client


class TestGoogleAuth:
    def test_google_login_returns_redirect(self):
        client = get_unauthenticated_client()
        response = client.get("/api/v1/auth/google/login", follow_redirects=False)
        assert response.status_code == 307
        assert "accounts.google.com" in response.headers["location"]

    def test_get_me_returns_unauthenticated_when_no_cookie(self):
        client = get_unauthenticated_client()

        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["authenticated"] is False

    def test_logout_returns_redirect(self):
        client = get_authenticated_client()

        response = client.post("/api/v1/auth/logout", follow_redirects=False)
        assert response.status_code == 307


class TestAuthUtilities:
    def test_create_access_token(self):
        token = create_auth_token(user_id=1, email="test@example.com")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_test_user(self):
        user = create_test_user(user_id=42, email="custom@example.com", name="Custom Name")
        assert user.id == 42
        assert user.email == "custom@example.com"
        assert user.name == "Custom Name"

    def test_authenticated_client_has_cookie(self):
        client = get_authenticated_client()
        assert "access_token" in client.cookies
