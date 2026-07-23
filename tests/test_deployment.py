"""Tests for deployment configuration — Railway, health, infrastructure."""

import tomllib
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent


# ── Railway Config Tests ──────────────────────────────────────


class TestRailwayConfig:
    """Interface: Railway deployment config files exist and are valid."""

    def test_railway_toml_exists(self):
        """railway.toml must exist at repo root."""
        assert (REPO_ROOT / "railway.toml").exists()

    def test_railway_toml_is_valid_toml(self):
        """railway.toml must parse as valid TOML."""
        path = REPO_ROOT / "railway.toml"
        with open(path, "rb") as f:
            config = tomllib.load(f)
        assert isinstance(config, dict)

    def test_railway_toml_has_deploy_section(self):
        """railway.toml must have a [deploy] section."""
        path = REPO_ROOT / "railway.toml"
        with open(path, "rb") as f:
            config = tomllib.load(f)
        assert "deploy" in config

    def test_railway_toml_has_healthcheck_path(self):
        """railway.toml must configure /health as healthcheck path."""
        path = REPO_ROOT / "railway.toml"
        with open(path, "rb") as f:
            config = tomllib.load(f)
        assert config["deploy"]["healthcheckPath"] == "/health"

    def test_dockerfile_exists(self):
        """Dockerfile must exist at repo root."""
        assert (REPO_ROOT / "Dockerfile").exists()

    def test_dockerfile_starts_from_python(self):
        """Dockerfile must use a Python base image."""
        dockerfile = (REPO_ROOT / "Dockerfile").read_text()
        assert any(line.startswith("FROM python") for line in dockerfile.splitlines())


# ── Health Endpoint Tests ─────────────────────────────────────


class TestDeploymentHealthEndpoint:
    """Behavioral: /health returns version info for deployment validation."""

    async def test_health_returns_200(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_returns_version(self):
        """Health endpoint must include version string '0.1.0'."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    async def test_health_returns_status_ok(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
