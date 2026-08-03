"""Frontend quality gate — the modern analytics dashboard must exist.

Mirrors the checks in ``~/.hermes/scripts/ui-gate.sh`` as a pytest suite so the
deliverable is verifiable in CI without a browser or a node toolchain:

* ``frontend/package.json`` pins a modern framework (Next.js/React/Vite…)
* the app is component-based (TSX sources), not a vanilla ``app.js``
* Tailwind CSS is configured
* the dashboard wires every required product section to a real analytics endpoint
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

REQUIRED_SECTIONS = [
    "SummaryCards",
    "TrendChart",
    "TopContentTable",
    "OptimizationScorePanel",
    "ValidationGapsPanel",
    "EmptyState",
]

REQUIRED_ENDPOINTS = [
    "/posts",
    "/summary",
    "/trends/",
    "/trends/top-content",
    "/optimization-score/calculate",
    "/validate",
    "/export/csv",
]


def test_frontend_package_json_pins_a_modern_stack() -> None:
    pkg = json.loads((FRONTEND / "package.json").read_text())
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    assert any(key in deps for key in ("next", "react", "svelte", "vue", "vite")), (
        "frontend/package.json pins no modern framework"
    )
    assert "next" in deps and "react" in deps, "expected a Next.js + React stack"


def test_frontend_is_component_based() -> None:
    tsx_sources = list((FRONTEND / "components").rglob("*.tsx"))
    assert len(tsx_sources) >= 5, f"only {len(tsx_sources)} components — expected a component-based UI"
    assert (FRONTEND / "app" / "page.tsx").exists(), "dashboard page missing"


def test_tailwind_is_configured() -> None:
    assert (FRONTEND / "tailwind.config.ts").exists()
    globals_css = (FRONTEND / "app" / "globals.css").read_text()
    assert "@tailwind base" in globals_css and "@tailwind utilities" in globals_css


def test_dashboard_wires_required_sections_to_real_endpoints() -> None:
    page = (FRONTEND / "app" / "page.tsx").read_text()
    api = (FRONTEND / "lib" / "api.ts").read_text()
    for section in REQUIRED_SECTIONS:
        assert section in page, f"dashboard page does not render {section}"
    for endpoint in REQUIRED_ENDPOINTS:
        assert endpoint in api, f"API client does not call {endpoint}"
