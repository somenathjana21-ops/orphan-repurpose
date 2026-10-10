"""Regression coverage for database configuration loaded from .env."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_database_uses_dotenv_url(tmp_path: Path) -> None:
    """The engine and table creation must honor the configured SQLite database."""
    database_path = tmp_path / "configured" / "audit.db"
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    (tmp_path / ".env").write_text(f"DATABASE_URL={database_url}\n", encoding="utf-8")
    environment = os.environ.copy()
    environment.pop("DATABASE_URL", None)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import asyncio; "
            "from app.core.config import settings; "
            "from app.db.database import DATABASE_URL, create_tables, engine; "
            "assert DATABASE_URL == settings.DATABASE_URL; "
            "asyncio.run(create_tables()); "
            "asyncio.run(engine.dispose())",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert database_path.is_file()
