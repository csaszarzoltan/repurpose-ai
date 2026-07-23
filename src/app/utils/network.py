"""Network utilities."""

from __future__ import annotations

import ipaddress
import socket


def is_private_address(host: str) -> bool:
    """Check if a host string is a private/reserved IP address."""
    try:
        addr = ipaddress.ip_address(host)
        return addr.is_private or addr.is_loopback
    except ValueError:
        return False


def resolve_host(host: str) -> str | None:
    """Resolve a hostname to an IP address."""
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


def validate_port(port: int) -> bool:
    """Check if a port number is valid (1-65535)."""
    return 1 <= port <= 65535
