"""Monkey-patch httpx.Request to support .json() (needed by pre-tester tests)."""
from __future__ import annotations

import json as _json

import httpx

if not hasattr(httpx.Request, "json"):

    def _request_json(self) -> object:
        return _json.loads(self.content)

    httpx.Request.json = _request_json  # type: ignore[attr-defined]
