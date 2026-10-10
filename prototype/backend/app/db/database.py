"""Database setup and session management."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Database URL - SQLite for prototype
# Use absolute path relative to the backend directory (prototype/backend/)
_backend_dir = Path(__file__).resolve().parent.parent.parent
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite+aiosqlite:///{_backend_dir}/data/orphan_repurpose.db"
)

# Ensure data directory exists
_data_dir = _backend_dir / "data"
_data_dir.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


_tables_created = False


async def _ensure_tables():
    """Ensure tables exist (idempotent)."""
    global _tables_created
    if not _tables_created:
        await create_tables()
        _tables_created = True


async def get_session() -> AsyncSession:
    """Get an async database session."""
    await _ensure_tables()
    async with async_session_factory() as session:
        yield session


async def create_tables() -> None:
    """Create all database tables."""
    # Import models to register them with Base
    import app.db.models  # noqa: F401

    # Ensure directory exists for SQLite
    if "sqlite" in DATABASE_URL:
        # Handle both relative and absolute paths
        db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "").replace(
            "sqlite+aiosqlite://", ""
        )
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
