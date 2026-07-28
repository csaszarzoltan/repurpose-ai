"""Auth service — password hashing, JWT creation/validation, user management."""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.constants import APP_VERSION
from app.models.auth import TokenPayload, UserResponse, UserRole

# ── Password hashing (PBKDF2-SHA256 — stdlib only) ───────────
PBKDF2_ITERATIONS = 600_000
PBKDF2_ALGORITHM = "sha256"

# ── JWT configuration ─────────────────────────────────────────
# In production, these would come from environment variables / secrets manager
JWT_SECRET_KEY = "repurposeai-dev-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30

# ── In-memory user store (replace with database in production) ─
_users_db: dict[str, dict[str, Any]] = {}
# email -> user_id index
_email_index: dict[str, str] = {}

# ── In-memory brand voice config store (per user) ────────────
_brand_voice_db: dict[str, dict[str, Any]] = {}


# ── Password helpers ─────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-SHA256 (stdlib-only).

    Format: <iterations>$<salt_hex>$<hash_hex>
    """
    salt = os.urandom(32)
    dk = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM, password.encode(), salt, PBKDF2_ITERATIONS
    )
    return f"{PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a PBKDF2 hash string."""
    try:
        iterations_str, salt_hex, hash_hex = hashed_password.split("$")
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        stored_hash = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False

    dk = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM, plain_password.encode(), salt, iterations
    )
    return dk == stored_hash


# ── JWT helpers ──────────────────────────────────────────────


def create_access_token(user_id: str, email: str) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "access",
        "version": APP_VERSION,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, email: str) -> str:
    """Create a long-lived JWT refresh token."""
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "refresh",
        "version": APP_VERSION,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token. Raises jwt.PyJWTError on failure."""
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return TokenPayload(
        sub=payload["sub"],
        email=payload["email"],
        exp=payload["exp"],
        type=payload.get("type", "access"),
    )


def refresh_access_token(refresh_token: str) -> tuple[str, str]:
    """Validate refresh token and issue new access + refresh tokens.

    Returns (new_access_token, new_refresh_token).
    """
    payload = decode_token(refresh_token)
    if payload.type != "refresh":
        raise ValueError("Invalid token type: expected refresh token")

    user_id = payload.sub
    email = payload.email

    # Check user still exists and is active
    user = _users_db.get(user_id)
    if user is None or not user.get("is_active", False):
        raise ValueError("User not found or inactive")

    new_access = create_access_token(user_id, email)
    new_refresh = create_refresh_token(user_id, email)
    return new_access, new_refresh


# ── User management ──────────────────────────────────────────


def create_user(email: str, password: str, name: str) -> UserResponse:
    """Register a new user. Raises ValueError if email already exists."""
    if email.strip().lower() in _email_index:
        raise ValueError(f"Email '{email}' is already registered")

    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(password)
    now = datetime.now(UTC)

    user_record: dict[str, Any] = {
        "user_id": user_id,
        "email": email.strip().lower(),
        "name": name.strip(),
        "password": hashed_pw,
        "role": UserRole.USER,
        "is_active": True,
        "created_at": now,
    }

    _users_db[user_id] = user_record
    _email_index[email.strip().lower()] = user_id

    return UserResponse(
        user_id=user_id,
        email=user_record["email"],
        name=user_record["name"],
        role=user_record["role"],
        is_active=user_record["is_active"],
        created_at=user_record["created_at"],
    )


def authenticate_user(email: str, password: str) -> UserResponse:
    """Authenticate a user by email and password. Raises ValueError on failure."""
    normalized_email = email.strip().lower()
    user_id = _email_index.get(normalized_email)
    if user_id is None:
        raise ValueError("Invalid email or password")

    user = _users_db[user_id]
    if not user.get("is_active", False):
        raise ValueError("Account is inactive")

    if not verify_password(password, user["password"]):
        raise ValueError("Invalid email or password")

    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )


def get_user_by_id(user_id: str) -> UserResponse | None:
    """Look up a user by their ID. Returns None if not found."""
    user = _users_db.get(user_id)
    if user is None:
        return None
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )


def get_user_by_email(email: str) -> UserResponse | None:
    """Look up a user by their email. Returns None if not found."""
    user_id = _email_index.get(email.strip().lower())
    if user_id is None:
        return None
    return get_user_by_id(user_id)


def change_password(user_id: str, current_password: str, new_password: str) -> None:
    """Change a user's password. Raises ValueError on failure."""
    user = _users_db.get(user_id)
    if user is None:
        raise ValueError("User not found")

    if not verify_password(current_password, user["password"]):
        raise ValueError("Current password is incorrect")

    user["password"] = hash_password(new_password)


# ── Brand voice per user ─────────────────────────────────────


def get_user_brand_voice(user_id: str) -> dict[str, Any] | None:
    """Get the brand voice config for a user."""
    return _brand_voice_db.get(user_id)


def set_user_brand_voice(
    user_id: str,
    brand_voice: str,
    config_overrides: dict[str, str] | None = None,
    custom_instructions: str | None = None,
) -> dict[str, Any]:
    """Set the brand voice config for a user."""
    record: dict[str, Any] = {
        "user_id": user_id,
        "brand_voice": brand_voice,
        "config_overrides": config_overrides or {},
        "custom_instructions": custom_instructions,
        "updated_at": datetime.now(UTC),
    }
    _brand_voice_db[user_id] = record
    return record


# ── Utility (for testing) ────────────────────────────────────


def clear_users() -> None:
    """Clear all user data (used in tests)."""
    _users_db.clear()
    _email_index.clear()
    _brand_voice_db.clear()
