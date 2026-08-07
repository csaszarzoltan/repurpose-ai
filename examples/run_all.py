"""Run all analytics dashboard examples sequentially using subprocess.

Usage: .venv/bin/python examples/run_all.py
"""

import os
import subprocess
import sys

EXAMPLES = [
    "publish_wordpress",
    "publish_ghost",
    "analytics_data_store",
    "analytics_performance",
    "analytics_scoring",
    "analytics_validation",
    "analytics_export",
    "analytics_trends",
]


def main() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_python = os.path.join(repo_root, ".venv", "bin", "python")

    if not os.path.exists(venv_python):
        print(f"ERROR: virtualenv python not found at {venv_python}")
        sys.exit(1)

    passed = 0
    failed = []
    for name in EXAMPLES:
        script = os.path.join(repo_root, "examples", f"{name}.py")
        print(f"\n{'=' * 60}")
        print(f"  Running: {name}")
        print(f"{'=' * 60}")
        result = subprocess.run(
            [venv_python, script],
            cwd=repo_root,
            capture_output=False,
            text=True,
        )
        if result.returncode == 0:
            passed += 1
            print(f"  ✓ {name} passed")
        else:
            failed.append(name)
            print(f"  ✗ {name} FAILED (exit code {result.returncode})")

    print(f"\n{'=' * 60}")
    summary = f"Result: {passed}/{len(EXAMPLES)} passed"
    if failed:
        summary += f", {len(failed)} failed: {', '.join(failed)}"
    else:
        summary += " — all OK"
    print(f"  {summary}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
