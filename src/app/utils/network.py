"""Network utilities."""

from __future__ import annotations

import ipaddress
from typing import Optional


def is_private_address(host: str) -> bool:
    """Check if a host string is a private/reserved IP address."""
    raise NotImplementedError


def resolve_host(host: str) -> Optional[str]:
    """Resolve a hostname to an IP address."""
    raise NotImplementedError


def validate_port(port: int) -> bool:
    """Check if a port number is valid (1-65535)."""
    raise NotImplementedError
