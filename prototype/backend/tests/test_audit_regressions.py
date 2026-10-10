"""Audit API and persistence regressions, isolated from application data."""

from __future__ import annotations

import asyncio
import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import database
from app.db.models import AuditEntryModel
from app.main import app
from app.services import audit_service


@pytest.fixture
async def audit_db(tmp_path, monkeypatch):
    """Use an empty temporary SQLite database and a fresh audit singleton."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'audit.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "async_session_factory", factory)
    monkeypatch.setattr(database, "_tables_created", False)
    monkeypatch.setattr(audit_service, "async_session_factory", factory)
    monkeypatch.setattr(audit_service, "_service", audit_service.AuditService())
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.mark.parametrize("prefix", ["audit", "validation"])
async def test_sessions_route_lists_persisted_sessions(audit_db, async_client, prefix):
    service = audit_service.get_audit_service()
    await service.add_entry("session-one", "note", "reviewer", {"note": "first"})
    await service.add_entry("session-one", "note", "reviewer", {"note": "second"})
    await service.add_entry("session-two", "note", "reviewer", {})

    response = await async_client.get(f"/api/v1/{prefix}/sessions")

    assert response.status_code == 200, response.text
    assert sorted(response.json()["sessions"]) == ["session-one", "session-two"]


async def test_log_endpoint_persists_entry_before_responding(audit_db):
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/audit/log",
            params={"session_id": "logged", "entry_type": "note", "user": "reviewer"},
            json={"note": "persist this"},
        )

    assert response.status_code == 200, response.text
    entry = response.json()["entry"]
    assert entry["data"] == {"note": "persist this"}
    assert len(entry["hash"]) == 64
    async with audit_db() as db:
        stored = (await db.execute(select(AuditEntryModel))).scalar_one()
        assert stored.session_id == "logged"
        assert stored.hash == entry["hash"]
        assert stored.data == entry["data"]


@pytest.mark.parametrize("prefix", ["audit", "validation"])
@pytest.mark.parametrize(
    ("path", "status"), [("sessions", 200), ("missing", 404), ("missing/verify", 404)]
)
async def test_audit_reads_work_before_first_write(audit_db, async_client, prefix, path, status):
    response = await async_client.get(f"/api/v1/{prefix}/{path}")
    assert response.status_code == status, response.text
    if path == "sessions":
        assert response.json() == {"sessions": []}


async def test_append_after_service_restart_keeps_full_trail(audit_db):
    await audit_service.AuditService().add_entry("resumed", "note", "first", {"n": 1})
    restarted = audit_service.AuditService()
    await restarted.add_entry("resumed", "note", "second", {"n": 2})

    trail = await restarted.get_trail("resumed")
    assert trail is not None
    assert [entry.data["n"] for entry in trail.entries] == [1, 2]
    result = await restarted.verify("resumed")
    assert result["valid"] is True
    assert result["entry_count"] == 2


async def test_trail_includes_entries_written_by_another_service(audit_db):
    reader = audit_service.AuditService()
    await reader.add_entry("shared", "note", "first", {"n": 1})
    await reader.get_trail("shared")
    await audit_service.AuditService().add_entry("shared", "note", "second", {"n": 2})

    trail = await reader.get_trail("shared")
    assert trail is not None
    assert [entry.data["n"] for entry in trail.entries] == [1, 2]


async def test_verify_detects_persisted_tampering_with_warm_cache(audit_db):
    service = audit_service.AuditService()
    await service.add_entry("tampered", "validation", "reviewer", {"assessment": "unlikely"})
    await service.get_trail("tampered")
    async with audit_db() as db:
        await db.execute(
            update(AuditEntryModel)
            .where(AuditEntryModel.session_id == "tampered")
            .values(data={"assessment": "plausible"})
        )
        await db.commit()

    result = await service.verify("tampered")
    assert result["valid"] is False
    assert result["failed_at_index"] == 0


@pytest.mark.parametrize("seed_count", [0, 1])
async def test_concurrent_services_append_one_hash_chain(audit_db, seed_count):
    """Independent writers must serialize even when the session has no entries."""
    await database._ensure_tables()
    for number in range(seed_count):
        await audit_service.AuditService().add_entry("concurrent", "note", "seed", {"n": number})

    entries = await asyncio.gather(
        *(
            audit_service.AuditService().add_entry("concurrent", "note", f"writer-{n}", {"n": n})
            for n in range(seed_count, seed_count + 16)
        )
    )

    async with audit_db() as db:
        rows = (
            await db.execute(select(AuditEntryModel).order_by(AuditEntryModel.id))
        ).scalars().all()
    assert len(rows) == seed_count + len(entries)
    assert {row.data["n"] for row in rows} == set(range(seed_count + 16))
    assert {entry.hash for entry in entries} <= {row.hash for row in rows}
    previous_hash = ""
    for row in rows:
        assert row.previous_hash == previous_hash
        previous_hash = row.hash
    assert await audit_service.AuditService().verify("concurrent") == {
        "session_id": "concurrent",
        "valid": True,
        "entry_count": seed_count + 16,
        "message": "Audit trail integrity verified",
    }


@pytest.mark.parametrize("prefix", ["audit", "validation"])
@pytest.mark.parametrize("tampered_index", [0, 1])
async def test_verify_detects_previous_hash_tampering(
    audit_db, async_client, prefix, tampered_index
):
    """Changing only the stored link must fail verification with the existing API shape."""
    service = audit_service.get_audit_service()
    for number in range(2):
        await service.add_entry("tampered-link", "note", "reviewer", {"n": number})
    await service.get_trail("tampered-link")
    async with audit_db() as db:
        rows = (
            await db.execute(select(AuditEntryModel).order_by(AuditEntryModel.id))
        ).scalars().all()
        await db.execute(
            update(AuditEntryModel)
            .where(AuditEntryModel.id == rows[tampered_index].id)
            .values(previous_hash="f" * 64)
        )
        await db.commit()

    response = await async_client.get(f"/api/v1/{prefix}/tampered-link/verify")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "session_id": "tampered-link",
        "valid": False,
        "failed_at_index": tampered_index,
        "message": f"Hash mismatch at entry {tampered_index}",
    }


async def test_failed_append_rolls_back_and_releases_write_lock(audit_db, monkeypatch):
    async def fail_commit(db: AsyncSession) -> None:
        await db.flush()
        raise RuntimeError("simulated commit failure")

    await audit_service.AuditService().add_entry("rollback", "note", "seed", {})
    with monkeypatch.context() as patch:
        patch.setattr(AsyncSession, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="simulated commit failure"):
            await audit_service.AuditService().add_entry("rollback", "note", "failed", {})

    service = audit_service.AuditService()
    await asyncio.wait_for(service.add_entry("rollback", "note", "recovered", {}), timeout=10)
    trail = await service.get_trail("rollback")
    assert trail is not None
    assert [entry.user for entry in trail.entries] == ["seed", "recovered"]
    assert (await service.verify("rollback"))["valid"] is True


async def test_concurrent_processes_append_one_hash_chain(audit_db):
    """Each worker has its own interpreter, engine, connections, and services."""
    await database._ensure_tables()
    worker = """
import asyncio
import sys
from app.db import database
from app.services.audit_service import AuditService

async def main():
    # The parent initialized the schema before launching the workers.
    database._tables_created = True
    print("ready", flush=True)
    await asyncio.to_thread(sys.stdin.readline)
    try:
        await asyncio.gather(*(
            AuditService().add_entry("processes", "note", sys.argv[1], {"n": n})
            for n in range(6)
        ))
    finally:
        await database.engine.dispose()

asyncio.run(main())
"""
    env = dict(os.environ, DATABASE_URL=audit_db.kw["bind"].url.render_as_string())
    processes = []
    try:
        for number in range(3):
            processes.append(
                await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-c",
                    worker,
                    f"process-{number}",
                    env=env,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            )
        ready = await asyncio.wait_for(
            asyncio.gather(*(process.stdout.readline() for process in processes)), timeout=30
        )
        assert [line.strip() for line in ready] == [b"ready"] * len(processes)
        results = await asyncio.wait_for(
            asyncio.gather(*(process.communicate(b"go\n") for process in processes)), timeout=30
        )
        for process, (stdout, stderr) in zip(processes, results, strict=True):
            assert process.returncode == 0, (stdout.decode(), stderr.decode())
    finally:
        for process in processes:
            if process.returncode is None:
                process.kill()
            await process.wait()

    service = audit_service.AuditService()
    trail = await service.get_trail("processes")
    assert trail is not None
    assert {(entry.user, entry.data["n"]) for entry in trail.entries} == {
        (f"process-{number}", n) for number in range(3) for n in range(6)
    }
    assert await service.verify("processes") == {
        "session_id": "processes",
        "valid": True,
        "entry_count": 18,
        "message": "Audit trail integrity verified",
    }
