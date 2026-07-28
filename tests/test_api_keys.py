"""Tests for API key management — create, list, revoke, validate."""

from __future__ import annotations

import uuid

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.auth import ApiKeyCreate, ApiKeyFullResponse, ApiKeyResponse
from app.services.api_key import (
    clear_keys,
    create_api_key,
    generate_api_key,
    has_scope,
    list_api_keys,
    revoke_api_key,
    validate_api_key,
)

# ── Helpers ──────────────────────────────────────────────────


def _valid_user() -> dict:
    return {
        "email": f"ak-test-{uuid.uuid4().hex[:8]}@example.com",
        "password": "SecurePass123!",
        "name": "API Key Test User",
    }


async def _register_and_get_token() -> str:
    """Register a user and return access token."""
    payload = _valid_user()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/api/v1/auth/register", json=payload)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        )
    return login_resp.json()["access_token"]


# ── Model/Interface Tests ────────────────────────────────────


class TestApiKeyModelsInterface:
    """Interface: API key models exist with correct structure."""

    def test_api_key_create_model(self):
        import inspect

        sig = inspect.signature(ApiKeyCreate)
        params = list(sig.parameters.keys())
        assert "name" in params
        assert "scopes" in params

    def test_api_key_response_model(self):
        resp = ApiKeyResponse(
            key_id="key-1",
            name="My Key",
            scopes=["repurpose:write"],
            created_at="2026-01-01T00:00:00",
            key_prefix="rp_abc123",
        )
        assert resp.key_id == "key-1"
        assert resp.name == "My Key"
        assert resp.is_active is True

    def test_api_key_full_response_model(self):
        resp = ApiKeyFullResponse(
            key_id="key-1",
            name="My Key",
            scopes=["repurpose:write"],
            created_at="2026-01-01T00:00:00",
            key_prefix="rp_abc123",
            key_value="rp_abc123...",
        )
        assert resp.key_value == "rp_abc123..."

    def test_generate_api_key_has_prefix(self):
        key = generate_api_key()
        assert key.startswith("rp_")
        assert len(key) > 10

    def test_generate_api_key_unique(self):
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100  # All unique


class TestApiKeyServiceInterface:
    """Interface: API key service functions exist."""

    def test_create_api_key_exists(self):
        assert callable(create_api_key)

    def test_list_api_keys_exists(self):
        assert callable(list_api_keys)

    def test_revoke_api_key_exists(self):
        assert callable(revoke_api_key)

    def test_validate_api_key_exists(self):
        assert callable(validate_api_key)

    def test_has_scope_exists(self):
        assert callable(has_scope)


class TestApiKeyEndpointsInterface:
    """Interface: API key endpoints are registered."""

    def test_create_key_endpoint_exists(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/api-keys" in paths
        assert "post" in paths["/api/v1/api-keys"]

    def test_list_keys_endpoint_exists(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/api-keys" in paths
        assert "get" in paths["/api/v1/api-keys"]

    def test_revoke_key_endpoint_exists(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/api-keys/{key_id}" in paths
        assert "delete" in paths["/api/v1/api-keys/{key_id}"]


# ── Service-Level Tests ──────────────────────────────────────


class TestApiKeyService:
    """Service: API key CRUD operations."""

    def setup_method(self):
        clear_keys()
        self.user_id = str(uuid.uuid4())

    def test_create_and_validate_key(self):
        result = create_api_key(
            user_id=self.user_id,
            name="Test Key",
            scopes=["repurpose:write"],
        )
        assert result["key_id"] is not None
        assert result["key_value"].startswith("rp_")
        assert result["name"] == "Test Key"

        # Validate the key
        validated = validate_api_key(result["key_value"])
        assert validated is not None
        assert validated["user_id"] == self.user_id
        assert validated["is_active"] is True

    def test_invalid_key_returns_none(self):
        assert validate_api_key("rp_invalid-key") is None

    def test_revoked_key_invalid(self):
        result = create_api_key(
            user_id=self.user_id,
            name="Revokable",
        )
        assert revoke_api_key(result["key_id"], self.user_id) is True
        assert validate_api_key(result["key_value"]) is None

    def test_revoke_wrong_user_fails(self):
        result = create_api_key(
            user_id=self.user_id,
            name="Others Key",
        )
        assert revoke_api_key(result["key_id"], "other-user-id") is False

    def test_list_keys_for_user(self):
        create_api_key(user_id=self.user_id, name="Key A")
        create_api_key(user_id=self.user_id, name="Key B")
        keys = list_api_keys(self.user_id)
        assert len(keys) == 2

    def test_list_keys_excludes_other_users(self):
        create_api_key(user_id=self.user_id, name="My Key")
        create_api_key(user_id="other-user", name="Other Key")
        keys = list_api_keys(self.user_id)
        assert len(keys) == 1

    def test_has_scope_check(self):
        result = create_api_key(
            user_id=self.user_id,
            name="Scoped Key",
            scopes=["repurpose:write"],
        )
        validated = validate_api_key(result["key_value"])
        assert validated is not None
        assert has_scope(validated, "repurpose:write") is True
        assert has_scope(validated, "admin") is False

    def test_wildcard_scope(self):
        result = create_api_key(
            user_id=self.user_id,
            name="Wildcard Key",
            scopes=["*"],
        )
        validated = validate_api_key(result["key_value"])
        assert validated is not None
        assert has_scope(validated, "anything") is True


# ── API Endpoint Tests ──────────────────────────────────────


class TestApiKeyEndpoints:
    """API: API key CRUD endpoints."""

    async def test_create_key_returns_201(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/api-keys",
                json={"name": "My API Key", "scopes": ["repurpose:write"]},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 201

    async def test_create_key_returns_full_key(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/api-keys",
                json={"name": "Test Key"},
                headers={"Authorization": f"Bearer {token}"},
            )
        data = response.json()
        assert "key_id" in data
        assert "key_value" in data
        assert data["key_value"].startswith("rp_")
        assert data["name"] == "Test Key"

    async def test_create_key_needs_auth(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/api-keys",
                json={"name": "Unauthorized Key"},
            )
        assert response.status_code == 401

    async def test_list_keys(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Create two keys
            await client.post(
                "/api/v1/api-keys",
                json={"name": "Key 1"},
                headers={"Authorization": f"Bearer {token}"},
            )
            await client.post(
                "/api/v1/api-keys",
                json={"name": "Key 2"},
                headers={"Authorization": f"Bearer {token}"},
            )
            # List them
            response = await client.get(
                "/api/v1/api-keys",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_list_keys_not_include_key_value(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post(
                "/api/v1/api-keys",
                json={"name": "My Key"},
                headers={"Authorization": f"Bearer {token}"},
            )
            response = await client.get(
                "/api/v1/api-keys",
                headers={"Authorization": f"Bearer {token}"},
            )
        data = response.json()
        assert "key_value" not in data[0]

    async def test_revoke_key(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            create_resp = await client.post(
                "/api/v1/api-keys",
                json={"name": "Revokable"},
                headers={"Authorization": f"Bearer {token}"},
            )
            key_id = create_resp.json()["key_id"]

            delete_resp = await client.delete(
                f"/api/v1/api-keys/{key_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert delete_resp.status_code == 204

    async def test_revoke_nonexistent_key(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(
                "/api/v1/api-keys/nonexistent-key-id",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 404
