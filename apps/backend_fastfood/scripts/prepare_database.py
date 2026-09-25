"""Idempotently migrate the database and ensure its initial platform owner exists."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run() -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "bootstrap_platform.py")],
        cwd=PROJECT_ROOT,
        check=True,
    )


if __name__ == "__main__":
    run()
