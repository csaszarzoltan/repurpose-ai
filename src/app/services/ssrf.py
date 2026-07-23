"""SSRF protection service."""

from __future__ import annotations

from urllib.parse import urlparse

from app.utils.network import is_private_address, resolve_host


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

    def __init__(self, custom_blocked: list[str] | None = None) -> None:
        self._custom_blocked = custom_blocked or []

    def validate_url(self, url: str) -> bool:
        """Check if a URL is safe to fetch."""
        parsed = urlparse(url)
        scheme = parsed.scheme.lower() if parsed.scheme else ""

        if not scheme:
            return False

        if scheme in self.BLOCKED_SCHEMES:
            return False

        host = parsed.hostname or ""
        if host.lower() in self.BLOCKED_HOSTS:
            return False

        if host.lower() in [h.lower() for h in self._custom_blocked]:
            return False

        return not self.is_private_ip(host)

    def is_private_ip(self, host: str) -> bool:
        """Check if a host resolves to a private/reserved IP."""
        if is_private_address(host):
            return True

        resolved = resolve_host(host)
        return bool(resolved and is_private_address(resolved))

    def sanitize_url(self, url: str) -> str:
        """Sanitize a URL before fetching."""
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/")

        cleaned = f"{scheme}://{netloc}{path}"
        if parsed.query:
            cleaned += f"?{parsed.query}"

        return cleaned

    def check_redirect_chain(self, urls: list[str]) -> bool:
        """Verify a redirect chain stays safe."""
        return all(self.validate_url(url) for url in urls)
