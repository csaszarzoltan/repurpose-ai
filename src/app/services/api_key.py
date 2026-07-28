"""API key management service."""

from __future__ import annotations

import hmac
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

# ── In-memory API key store ──────────────────────────────────
_api_keys_db: dict[str, dict[str, Any]] = {}
# key_hash -> key_id index for fast lookup
_key_hash_index: dict[str, str] = {}

API_KEY_PREFIX = "rp_"  # RepurposeAI key prefix


def _hash_key(key_value: str) -> str:
    """Hash an API key for secure storage."""
    return hmac.new(
        b"repurposeai-api-key-hmac-secret",  # In production: use a proper secret
        key_value.encode(),
        "sha256",
    ).hexdigest()


def generate_api_key() -> str:
    """Generate a cryptographically secure API key."""
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def create_api_key(user_id: str, name: str, scopes: list[str] | None = None) -> dict[str, Any]:
    """Create a new API key for a user.

    Returns the full key record including the raw key_value (show once).
    """
    key_value = generate_api_key()
    key_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    key_hash = _hash_key(key_value)

    record: dict[str, Any] = {
        "key_id": key_id,
        "user_id": user_id,
        "name": name,
        "key_hash": key_hash,
        "scopes": scopes or ["repurpose:write"],
        "is_active": True,
        "created_at": now,
        "last_used_at": None,
    }

    _api_keys_db[key_id] = record
    _key_hash_index[key_hash] = key_id

    return {
        "key_id": key_id,
        "name": name,
        "scopes": record["scopes"],
        "is_active": True,
        "created_at": now,
        "last_used_at": None,
        "key_prefix": key_value[:8],
        "key_value": key_value,
    }


def list_api_keys(user_id: str) -> list[dict[str, Any]]:
    """List all API keys for a user (without the full key value)."""
    keys = []
    for record in _api_keys_db.values():
        if record["user_id"] == user_id:
            keys.append({
                "key_id": record["key_id"],
                "name": record["name"],
                "scopes": record["scopes"],
                "is_active": record["is_active"],
                "created_at": record["created_at"],
                "last_used_at": record["last_used_at"],
                "key_prefix": "",  # Cannot recover prefix from hash
            })
    return keys


def revoke_api_key(key_id: str, user_id: str) -> bool:
    """Revoke (deactivate) an API key. Returns True if found and revoked."""
    record = _api_keys_db.get(key_id)
    if record is None or record["user_id"] != user_id:
        return False
    record["is_active"] = False
    return True


def validate_api_key(key_value: str) -> dict[str, Any] | None:
    """Validate an API key and return the key record if valid.

    Also updates last_used_at if key is valid.
    """
    key_hash = _hash_key(key_value)
    key_id = _key_hash_index.get(key_hash)
    if key_id is None:
        return None

    record = _api_keys_db.get(key_id)
    if record is None or not record["is_active"]:
        return None

    # Update last used timestamp
    record["last_used_at"] = datetime.now(UTC)
    return record


def has_scope(key_record: dict[str, Any], required_scope: str) -> bool:
    """Check if an API key has the required scope."""
    scopes = key_record.get("scopes", [])
    return required_scope in scopes or "*" in scopes


def clear_keys() -> None:
    """Clear all API keys (used in tests)."""
    _api_keys_db.clear()
    _key_hash_index.clear()
