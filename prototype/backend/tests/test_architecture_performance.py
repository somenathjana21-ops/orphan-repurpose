"""Protect numerical equivalence, request responsiveness, and grouped persistence."""

from __future__ import annotations

import asyncio
import pickle
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from threading import Event, get_ident
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import torch
from app.api.v1 import candidates, diseases, kg
from app.db import database
from app.db.models import CandidateDetailsModel, CandidateModel
from app.ml.featurizer import ATOM_FEATURE_DIM
from app.ml.indication_model import IndicationModel, SimpleIndicationModel
from app.services import explanation_service, indication_service
from app.services.indication_service import IndicationService
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture(params=["SimpleIndicationModel_MLP", "DualEncoderCrossAttention"])
def checkpoint(request, tmp_path):
    """Small real checkpoints exercise both supported architectures without artifacts."""
    torch.manual_seed(42)
    config = {
        "architecture": request.param,
        "fp_dim": 8,
        "kg_dim": 4,
        "hidden_dim": 16,
        "node_feature_dim": ATOM_FEATURE_DIM,
        "num_layers": 2,
        "num_heads": 4,
    }
    if request.param == "SimpleIndicationModel_MLP":
        model = SimpleIndicationModel(fp_dim=8, kg_dim=4, hidden_dim=16)
    else:
        model = IndicationModel(
            node_feature_dim=ATOM_FEATURE_DIM, kg_dim=4, hidden_dim=16, num_layers=2
        )
    payload = {
        "config": config,
        "model_state_dict": model.state_dict(),
        "temperature": 1.7,
        "conformal_q": 0.13,
        "drug_smiles": dict(enumerate(["CCO", "C", "CCN", "CC", "CCC", "O", "CO"])),
        "drug_fingerprints": {i: torch.randn(8).tolist() for i in range(7)},
        "disease_map": {"UMLS:test": 0},
        "disease_embeddings": [[0.1, 0.2, 0.3, 0.4]],
    }
    path = tmp_path / "model.pt"
    path.write_bytes(pickle.dumps(payload))
    return path


def test_batched_scores_match_independent_single_drug_inference(checkpoint):
    serial = IndicationService(str(checkpoint), batch_size=1)
    batched = IndicationService(str(checkpoint), batch_size=3)
    expected = serial.score_drugs("UMLS:test")
    assert batched.load()
    sizes = []
    hook = batched.model.register_forward_pre_hook(
        lambda model, inputs: sizes.append(inputs[-1].shape[0])
    )
    actual = batched.score_drugs("UMLS:test")
    hook.remove()
    assert sizes == [3, 3, 1]
    assert [r["drug_id"] for r in actual] == [r["drug_id"] for r in expected]
    for result, reference in zip(actual, expected, strict=True):
        for field in ("probability", "ci_lower", "ci_upper"):
            assert result[field] == pytest.approx(reference[field], abs=1e-6)
        assert result["ci_lower"] == pytest.approx(max(0, result["probability"] - 0.13))
        assert result["ci_upper"] == pytest.approx(min(1, result["probability"] + 0.13))


def test_selection_empty_missing_and_lazy_load(checkpoint):
    svc = IndicationService(str(checkpoint), batch_size=3)
    assert len(svc.score_all_for_orpha("UMLS:test", top_k=2)) == 2
    assert svc.score_drugs("UMLS:test", []) == []
    assert svc.score_drugs("missing") == []
    assert svc.score_drugs("UMLS:test", ["missing"]) == []
    selected = svc.score_drugs("UMLS:test", [0, 3, "missing"])
    assert {r["drug_id"] for r in selected} == {0, 3}
    if svc.config["architecture"] == "SimpleIndicationModel_MLP":
        del svc.drug_fingerprints[0]
        assert svc.score_drugs("UMLS:test", [0]) == []
    else:
        cached = svc._graph_cache[0]
        svc.score_drugs("UMLS:test", [0])
        assert svc._graph_cache[0] is cached


def test_concurrent_checkpoint_load_happens_once(checkpoint, monkeypatch):
    svc = IndicationService(str(checkpoint))
    load = Mock(wraps=pickle.load)
    monkeypatch.setattr(indication_service, "pickle", SimpleNamespace(load=load))
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(pool.map(lambda _: svc.load(), range(8)))
    assert load.call_count == 1


@pytest.mark.parametrize("batch_size", [0, -1])
def test_invalid_batch_size(batch_size):
    with pytest.raises(ValueError, match="positive"):
        IndicationService(batch_size=batch_size)


@pytest.mark.parametrize(
    "module_name,class_name",
    [
        ("indication_service", "IndicationService"),
        ("explanation_service", "ExplanationService"),
        ("safety_service", "SafetyService"),
        ("dossier_service", "DossierService"),
    ],
)
def test_worker_threads_share_one_service(module_name, class_name, monkeypatch):
    module = import_module(f"app.services.{module_name}")
    entered, release = Event(), Event()
    instance = Mock()

    def construct():
        entered.set()
        assert release.wait(2)
        return instance

    factory = Mock(side_effect=construct)
    monkeypatch.setattr(module, "_service", None)
    monkeypatch.setattr(module, class_name, factory)
    getter = getattr(module, f"get_{module_name}")
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = [pool.submit(getter) for _ in range(4)]
        try:
            assert entered.wait(1)
        finally:
            release.set()
        assert all(task.result() is instance for task in tasks)
    factory.assert_called_once()


def test_corrupt_checkpoint_is_not_ready(tmp_path):
    path = tmp_path / "broken.pt"
    path.write_bytes(b"invalid checkpoint")
    svc = IndicationService(str(path))
    assert svc.load() is False
    assert svc.score_all_for_orpha("UMLS:test") == []


@pytest.fixture
async def candidate_db(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'candidates.db'}")
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "async_session_factory", async_sessionmaker(engine))
    monkeypatch.setattr(database, "_tables_created", False)
    await database._ensure_tables()
    try:
        yield engine
    finally:
        await engine.dispose()


def make_candidate(index, probability=0.8):
    return candidates._candidate_from_score(
        index + 1,
        {
            "drug_id": f"drugcentral:{1001 + index}",
            "probability": probability,
            "ci_lower": probability - 0.1,
            "ci_upper": probability + 0.1,
        },
    )


async def test_grouped_writes_have_constant_select_count_and_keep_full_evidence(candidate_db):
    statements = []
    event.listen(
        candidate_db.sync_engine,
        "before_cursor_execute",
        lambda conn, cursor, statement, parameters, context, many: statements.append(statement),
    )
    for probability in (0.8, 0.7):
        batch = [make_candidate(i, probability) for i in range(20)]
        statements.clear()
        await candidates._store_candidates(batch)
        assert sum(s.lstrip().upper().startswith("SELECT") for s in statements) == 2
        async with database.async_session_factory() as db:
            rows = (await db.scalars(select(CandidateModel))).all()
            details = (await db.scalars(select(CandidateDetailsModel))).all()
            assert len(rows) == len(details) == 20
            assert all(r.indication_probability == probability for r in rows)
            assert {r.candidate_id: r.payload for r in details} == {
                c.candidate_id: c.model_dump(mode="json") for c in batch
            }
    statements.clear()
    await candidates._store_candidates([])
    assert statements == []


async def test_concurrent_generation_does_not_duplicate_candidates(candidate_db):
    batch = [make_candidate(i) for i in range(5)]
    await asyncio.gather(*(candidates._store_candidates(batch) for _ in range(3)))
    async with database.async_session_factory() as db:
        assert len((await db.scalars(select(CandidateModel))).all()) == 5
        assert len((await db.scalars(select(CandidateDetailsModel))).all()) == 5


async def test_failed_evidence_write_rolls_back_parent_updates(candidate_db, monkeypatch):
    candidate = make_candidate(0)
    await candidates._store_candidates([candidate])
    changed = candidate.model_copy(update={"indication_probability": 0.1})
    monkeypatch.setattr(type(candidate), "model_dump", Mock(side_effect=ValueError("bad payload")))
    with pytest.raises(ValueError, match="bad payload"):
        await candidates._store_candidates([changed])
    async with database.async_session_factory() as db:
        row = await db.get(CandidateModel, candidate.candidate_id)
        assert row.indication_probability == 0.8


@pytest.mark.parametrize("operation", ["inference", "explanation", "dossier", "graph"])
async def test_health_remains_responsive_during_slow_work(operation, monkeypatch, async_client):
    started, release = Event(), Event()
    event_loop_thread = get_ident()
    worker_threads = []

    def slow_work(*args, **kwargs):
        worker_threads.append(get_ident())
        started.set()
        assert release.wait(timeout=5), "Slow work blocked the event loop"
        return {}

    candidate = make_candidate(0)
    monkeypatch.setattr(candidates, "_store_candidates", AsyncMock())
    if operation == "inference":
        svc = Mock()
        svc.is_ready.return_value = True
        svc.score_all_for_orpha.side_effect = lambda *a, **kw: (
            slow_work(),
            [{"drug_id": candidate.drug_id, "probability": 0.8, "ci_lower": 0.7, "ci_upper": 0.9}],
        )[1]
        monkeypatch.setattr(indication_service, "get_indication_service", lambda: svc)
        request = async_client.post("/api/v1/candidates/generate", json={"disease_id": "ORPHA:646"})
    elif operation == "explanation":
        monkeypatch.setattr(candidates, "get_candidate", AsyncMock(return_value=candidate))
        svc = Mock(explain_candidate=slow_work)
        monkeypatch.setattr(explanation_service, "get_explanation_service", lambda: svc)
        request = async_client.get(f"/api/v1/candidates/{candidate.candidate_id}/explanation")
    elif operation == "dossier":
        from app.models.disease import CandidateGenerateResponse
        from app.services import dossier_service

        disease = diseases._to_detail(diseases._FALLBACK_DISEASES[0])
        monkeypatch.setattr(diseases, "get_disease", AsyncMock(return_value=disease))
        monkeypatch.setattr(
            candidates,
            "generate_candidates",
            AsyncMock(
                return_value=CandidateGenerateResponse(candidates=[candidate], session_id="test")
            ),
        )
        svc = Mock(
            generate_dossier=lambda *a, **kw: (
                slow_work(),
                {
                    "pdf_base64": "JVBERi0=",
                    "dossier_json": {"disease": disease, "candidates": [candidate], "sections": {}},
                    "audit_trail_id": "test",
                },
            )[1]
        )
        monkeypatch.setattr(dossier_service, "get_dossier_service", lambda: svc)
        request = async_client.post(
            "/api/v1/dossier/generate",
            json={
                "disease_id": "ORPHA:646",
                "candidate_ids": [],
                "include_sections": [],
            },
        )
    else:
        svc = Mock(execute=lambda *a, **kw: (slow_work(), [])[1])
        monkeypatch.setattr(kg, "_get_kg_service", lambda: svc)
        request = async_client.get("/api/v1/kg/search")

    task = asyncio.create_task(request)
    try:
        assert await asyncio.to_thread(started.wait, 2)
        assert not task.done()
        health = await asyncio.wait_for(async_client.get("/health"), timeout=1)
        assert health.status_code == 200
        assert all(thread != event_loop_thread for thread in worker_threads)
    finally:
        release.set()
        assert (await task).status_code == 200


async def test_lifespan_closes_database_and_graph(monkeypatch):
    from app.main import app, lifespan

    create = AsyncMock()
    dispose = AsyncMock()
    close = Mock()
    monkeypatch.setattr(database, "create_tables", create)
    monkeypatch.setattr(database, "engine", Mock(dispose=dispose))
    monkeypatch.setattr(kg, "close_kg_service", close)
    async with lifespan(app):
        create.assert_awaited_once()
    close.assert_called_once()
    dispose.assert_awaited_once()
