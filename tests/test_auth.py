"""Tests for auth system — registration, login, JWT tokens, profile."""

from __future__ import annotations

import uuid

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.auth import (
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    clear_users,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    refresh_access_token,
    verify_password,
)

# ── Fixtures ──────────────────────────────────────────────────


def _valid_user() -> dict:
    """Return a valid user registration payload."""
    return {
        "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
        "password": "SecurePass123!",
        "name": "Test User",
    }


def _login_payload(email: str, password: str) -> dict:
    return {"email": email, "password": password}


# ── Model/Interface Tests ────────────────────────────────────


class TestAuthModelsInterface:
    """Interface: auth models exist with correct structure."""

    def test_user_create_model(self):
        """UserCreate has email, password, name fields."""
        import inspect

        sig = inspect.signature(UserCreate)
        params = list(sig.parameters.keys())
        assert "email" in params
        assert "password" in params
        assert "name" in params

    def test_user_login_model(self):
        """UserLogin has email and password fields."""
        import inspect

        sig = inspect.signature(UserLogin)
        params = list(sig.parameters.keys())
        assert "email" in params
        assert "password" in params

    def test_token_response_model(self):
        """TokenResponse has access_token, refresh_token, token_type."""
        import inspect

        sig = inspect.signature(TokenResponse)
        params = list(sig.parameters.keys())
        assert "access_token" in params
        assert "refresh_token" in params
        assert "token_type" in params

    def test_token_refresh_model(self):
        """TokenRefresh has refresh_token field."""
        import inspect

        sig = inspect.signature(TokenRefresh)
        params = list(sig.parameters.keys())
        assert "refresh_token" in params

    def test_user_response_model(self):
        """UserResponse has expected fields."""
        resp = UserResponse(
            user_id="test-id",
            email="test@example.com",
            name="Test",
        )
        assert resp.user_id == "test-id"
        assert resp.email == "test@example.com"
        assert resp.name == "Test"
        assert resp.role == "user"
        assert resp.is_active is True


class TestAuthServiceInterface:
    """Interface: auth service functions are importable and callable."""

    def test_hash_password_exists(self):
        assert callable(hash_password)

    def test_verify_password_exists(self):
        assert callable(verify_password)

    def test_create_access_token_exists(self):
        assert callable(create_access_token)

    def test_create_refresh_token_exists(self):
        assert callable(create_refresh_token)

    def test_decode_token_exists(self):
        assert callable(decode_token)

    def test_refresh_access_token_exists(self):
        assert callable(refresh_access_token)

    def test_authenticate_user_exists(self):
        assert callable(authenticate_user)

    def test_get_user_by_id_exists(self):
        assert callable(get_user_by_id)

    def test_get_user_by_email_exists(self):
        assert callable(get_user_by_email)


class TestAuthEndpointsInterface:
    """Interface: auth endpoints are registered in the app."""

    def test_register_endpoint_exists(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/auth/register" in paths
        assert "post" in paths["/api/v1/auth/register"]

    def test_login_endpoint_exists(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/auth/login" in paths
        assert "post" in paths["/api/v1/auth/login"]

    def test_refresh_endpoint_exists(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/auth/refresh" in paths
        assert "post" in paths["/api/v1/auth/refresh"]

    def test_me_endpoint_exists(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/auth/me" in paths
        assert "get" in paths["/api/v1/auth/me"]

    def test_password_change_endpoint_exists(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/auth/me/password" in paths
        assert "post" in paths["/api/v1/auth/me/password"]

    def test_brand_voice_get_endpoint_exists(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/auth/me/brand-voice" in paths
        assert "get" in paths["/api/v1/auth/me/brand-voice"]

    def test_brand_voice_put_endpoint_exists(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/auth/me/brand-voice" in paths
        assert "put" in paths["/api/v1/auth/me/brand-voice"]


# ── Service-Level Tests ──────────────────────────────────────


class TestPasswordHashing:
    """Service: password hashing and verification."""

    def test_hash_and_verify(self):
        hashed = hash_password("MyPassword123!")
        assert hashed != "MyPassword123!"
        assert verify_password("MyPassword123!", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("CorrectPass1!")
        assert verify_password("WrongPass1!", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Same password should produce different hashes (salt)."""
        h1 = hash_password("SamePass1!")
        h2 = hash_password("SamePass1!")
        assert h1 != h2


class TestJWTTokenCreation:
    """Service: JWT token creation and decoding."""

    def setup_method(self):
        self.user_id = str(uuid.uuid4())
        self.email = "user@example.com"

    def test_create_access_token(self):
        token = create_access_token(self.user_id, self.email)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_refresh_token(self):
        token = create_refresh_token(self.user_id, self.email)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_access_token(self):
        token = create_access_token(self.user_id, self.email)
        payload = decode_token(token)
        assert payload.sub == self.user_id
        assert payload.email == self.email
        assert payload.type == "access"
        assert payload.exp > 0

    def test_decode_refresh_token(self):
        token = create_refresh_token(self.user_id, self.email)
        payload = decode_token(token)
        assert payload.sub == self.user_id
        assert payload.email == self.email
        assert payload.type == "refresh"

    def test_access_token_type_is_access(self):
        token = create_access_token(self.user_id, self.email)
        payload = decode_token(token)
        assert payload.type == "access"

    def test_refresh_token_type_is_refresh(self):
        token = create_refresh_token(self.user_id, self.email)
        payload = decode_token(token)
        assert payload.type == "refresh"


class TestUserRegistration:
    """Service: user creation and lookup."""

    def setup_method(self):
        clear_users()

    def test_create_user_returns_user_response(self):
        user = create_user(
            email="new@example.com",
            password="StrongPass1!",
            name="New User",
        )
        assert isinstance(user, UserResponse)
        assert user.email == "new@example.com"
        assert user.name == "New User"
        assert user.is_active is True

    def test_create_user_generates_id(self):
        user = create_user(
            email="unique@example.com",
            password="StrongPass1!",
            name="Unique",
        )
        assert user.user_id is not None
        assert len(user.user_id) > 10

    def test_duplicate_email_raises(self):
        create_user(email="dup@example.com", password="Pass1234!", name="Dup")
        import pytest

        with pytest.raises(ValueError, match="already registered"):
            create_user(email="dup@example.com", password="Pass1234!", name="Dup2")

    def test_get_user_by_id(self):
        user = create_user(
            email="lookup@example.com", password="Pass1234!", name="Lookup"
        )
        found = get_user_by_id(user.user_id)
        assert found is not None
        assert found.email == "lookup@example.com"

    def test_get_user_by_id_not_found(self):
        assert get_user_by_id("nonexistent-id") is None

    def test_get_user_by_email(self):
        user = create_user(
            email="byemail@example.com", password="Pass1234!", name="ByEmail"
        )
        found = get_user_by_email("byemail@example.com")
        assert found is not None
        assert found.user_id == user.user_id

    def test_get_user_by_email_not_found(self):
        assert get_user_by_email("unknown@example.com") is None

    def test_email_case_insensitive(self):
        create_user(email="Case@Example.com", password="Pass1234!", name="Case")
        found = get_user_by_email("case@example.com")
        assert found is not None
        found2 = get_user_by_email("CASE@EXAMPLE.COM")
        assert found2 is not None
        assert found2.user_id == found.user_id


class TestUserAuthentication:
    """Service: user authentication."""

    def setup_method(self):
        clear_users()

    def test_authenticate_valid_credentials(self):
        create_user(email="auth@example.com", password="MyPass123!", name="Auth")
        user = authenticate_user(email="auth@example.com", password="MyPass123!")
        assert user.email == "auth@example.com"
        assert user.name == "Auth"

    def test_authenticate_wrong_password(self):
        create_user(email="wrongpw@example.com", password="Correct1!", name="WrongPW")
        import pytest

        with pytest.raises(ValueError, match="Invalid email or password"):
            authenticate_user(email="wrongpw@example.com", password="Wrong1!")

    def test_authenticate_nonexistent_email(self):
        import pytest

        with pytest.raises(ValueError, match="Invalid email or password"):
            authenticate_user(email="noone@example.com", password="Pass1234!")


class TestTokenRefresh:
    """Service: token refresh flow."""

    def setup_method(self):
        clear_users()
        self.user = create_user(
            email="refresh@example.com",
            password="Refresh123!",
            name="Refresh",
        )

    def test_refresh_with_valid_token(self):
        refresh_token = create_refresh_token(self.user.user_id, self.user.email)
        new_access, new_refresh = refresh_access_token(refresh_token)
        assert isinstance(new_access, str)
        assert isinstance(new_refresh, str)
        assert new_access != refresh_token

        # Verify the new access token
        payload = decode_token(new_access)
        assert payload.sub == self.user.user_id
        assert payload.type == "access"

    def test_refresh_with_access_token_raises(self):
        access_token = create_access_token(self.user.user_id, self.user.email)
        import pytest

        with pytest.raises(ValueError, match="Invalid token type"):
            refresh_access_token(access_token)

    def test_refresh_with_invalid_token_raises(self):
        import pytest

        with pytest.raises(Exception):
            refresh_access_token("invalid-token-string")


# ── API Endpoint Tests ──────────────────────────────────────


class TestRegisterEndpoint:
    """API: POST /api/v1/auth/register."""

    async def test_register_returns_201(self):
        payload = _valid_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201

    async def test_register_returns_user_data(self):
        payload = _valid_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/auth/register", json=payload)
        data = response.json()
        assert "user_id" in data
        assert data["email"] == payload["email"]
        assert data["name"] == payload["name"]
        assert data["is_active"] is True
        assert "password" not in data

    async def test_register_duplicate_email(self):
        payload = _valid_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json=payload)
            response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    async def test_register_short_password(self):
        payload = _valid_user()
        payload["password"] = "1234567"  # 7 chars, min is 8
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_missing_email(self):
        payload = _valid_user()
        del payload["email"]
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422


class TestLoginEndpoint:
    """API: POST /api/v1/auth/login."""

    async def _register_and_login(self) -> tuple[AsyncClient, dict]:
        """Helper: register a user and return client + login payload."""
        payload = _valid_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json=payload)
            login_resp = await client.post(
                "/api/v1/auth/login",
                json=_login_payload(payload["email"], payload["password"]),
            )
        return login_resp.json()

    async def test_login_returns_tokens(self):
        payload = _valid_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json=payload)
            response = await client.post(
                "/api/v1/auth/login",
                json=_login_payload(payload["email"], payload["password"]),
            )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self):
        payload = _valid_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json=payload)
            response = await client.post(
                "/api/v1/auth/login",
                json=_login_payload(payload["email"], "WrongPass123!"),
            )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json=_login_payload("noone@example.com", "Pass1234!"),
            )
        assert response.status_code == 401


class TestMeEndpoint:
    """API: GET /api/v1/auth/me."""

    async def _register_and_get_token(self) -> tuple[AsyncClient, str]:
        """Helper: register a user and return access token."""
        payload = _valid_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json=payload)
            login_resp = await client.post(
                "/api/v1/auth/login",
                json=_login_payload(payload["email"], payload["password"]),
            )
        token = login_resp.json()["access_token"]
        return token

    async def test_me_returns_user_data(self):
        token = await self._register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert "name" in data

    async def test_me_without_token(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_me_with_invalid_token(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid-token"},
            )
        assert response.status_code == 401


class TestTokenRefreshEndpoint:
    """API: POST /api/v1/auth/refresh."""

    async def test_refresh_returns_new_tokens(self):
        payload = _valid_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json=payload)
            login_resp = await client.post(
                "/api/v1/auth/login",
                json=_login_payload(payload["email"], payload["password"]),
            )
            refresh_token = login_resp.json()["refresh_token"]

            refresh_resp = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )
        assert refresh_resp.status_code == 200
        data = refresh_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != refresh_token

    async def test_refresh_with_invalid_token(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid-token"},
            )
        assert response.status_code == 401


class TestPasswordChangeEndpoint:
    """API: POST /api/v1/auth/me/password."""

    async def _setup_user(self) -> tuple[AsyncClient, str]:
        payload = _valid_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json=payload)
            login_resp = await client.post(
                "/api/v1/auth/login",
                json=_login_payload(payload["email"], payload["password"]),
            )
        return payload, login_resp.json()["access_token"]

    async def test_password_change_success(self):
        user_payload, token = await self._setup_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/me/password",
                json={
                    "current_password": user_payload["password"],
                    "new_password": "NewSecurePass789!",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 204

    async def test_password_change_wrong_current(self):
        _, token = await self._setup_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/me/password",
                json={
                    "current_password": "WrongPass123!",
                    "new_password": "NewSecurePass789!",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 400

    async def test_password_change_needs_auth(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/me/password",
                json={
                    "current_password": "any",
                    "new_password": "NewSecurePass789!",
                },
            )
        assert response.status_code == 401


class TestBrandVoiceEndpoint:
    """API: GET/PUT /api/v1/auth/me/brand-voice."""

    async def _setup_user(self) -> tuple[str, str]:
        payload = _valid_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json=payload)
            login_resp = await client.post(
                "/api/v1/auth/login",
                json=_login_payload(payload["email"], payload["password"]),
            )
        return login_resp.json()["access_token"]

    async def test_get_default_brand_voice(self):
        token = await self._setup_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/auth/me/brand-voice",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["brand_voice"] == "professional"

    async def test_update_brand_voice(self):
        token = await self._setup_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                "/api/v1/auth/me/brand-voice",
                json={
                    "brand_voice": "casual",
                    "custom_instructions": "Keep it light",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["brand_voice"] == "casual"
        assert data["custom_instructions"] == "Keep it light"

    async def test_get_updated_brand_voice(self):
        token = await self._setup_user()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.put(
                "/api/v1/auth/me/brand-voice",
                json={"brand_voice": "humorous"},
                headers={"Authorization": f"Bearer {token}"},
            )
            response = await client.get(
                "/api/v1/auth/me/brand-voice",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        assert response.json()["brand_voice"] == "humorous"
