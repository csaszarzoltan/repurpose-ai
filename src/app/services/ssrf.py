"""SSRF protection service."""

from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse


class SSRFChecker:
    """Validates URLs to prevent SSRF attacks."""

    BLOCKED_HOSTS: list[str] = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "metadata.google.internal",
        "169.254.169.254",
    ]

    BLOCKED_SCHEMES: list[str] = ["file", "ftp", "gopher"]

    def __init__(self, custom_blocked: Optional[list[str]] = None) -> None:
        raise NotImplementedError

    def validate_url(self, url: str) -> bool:
        """Check if a URL is safe to fetch."""
        raise NotImplementedError

    def is_private_ip(self, host: str) -> bool:
        """Check if a host resolves to a private/reserved IP."""
        raise NotImplementedError

    def sanitize_url(self, url: str) -> str:
        """Sanitize a URL before fetching."""
        raise NotImplementedError

    def check_redirect_chain(self, urls: list[str]) -> bool:
        """Verify a redirect chain stays safe."""
        raise NotImplementedError
