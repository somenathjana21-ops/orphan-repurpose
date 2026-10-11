"""Runtime optimizations preserve predictions, evidence and failure handling."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock, patch

import networkx as nx
import pytest
import torch

from app.api.v1 import literature
from app.ml.explainer import KGPathExtractor
from app.ml.indication_model import CrossAttentionFusion


@pytest.mark.parametrize("training", [False, True])
def test_attention_preserves_outputs_and_gradients_without_unused_weights(training):
    fusion = CrossAttentionFusion(embed_dim=16, num_heads=4, dropout=0.0)
    fusion.train(training)
    reference = deepcopy(fusion)

    def request_weights(module, args, kwargs):
        kwargs["need_weights"] = True
        return args, kwargs

    for attention in (reference.drug_to_disease, reference.disease_to_drug):
        attention.register_forward_pre_hook(request_weights, with_kwargs=True)

    inputs = [torch.randn(3, 16, requires_grad=True) for _ in range(2)]
    reference_inputs = [value.detach().clone().requires_grad_() for value in inputs]
    expected = reference(*reference_inputs)
    with (
        patch.object(fusion.drug_to_disease, "forward", wraps=fusion.drug_to_disease.forward) as d,
        patch.object(fusion.disease_to_drug, "forward", wraps=fusion.disease_to_drug.forward) as s,
    ):
        actual = fusion(*inputs)
    assert d.call_args.kwargs["need_weights"] is False
    assert s.call_args.kwargs["need_weights"] is False
    torch.testing.assert_close(actual, expected)

    actual.square().mean().backward()
    expected.square().mean().backward()
    for value, baseline in zip(inputs, reference_inputs, strict=True):
        torch.testing.assert_close(value.grad, baseline.grad)
    for value, baseline in zip(fusion.parameters(), reference.parameters(), strict=True):
        torch.testing.assert_close(value.grad, baseline.grad)


@pytest.mark.parametrize("k", [-1, 0, 1, 3, 5, 10])
def test_path_extraction_does_not_compute_an_unused_path(monkeypatch, k):
    extractor = KGPathExtractor()
    graph = nx.DiGraph()
    for i in range(7):
        graph.add_edge("drug", f"target:{i}", type="HAS_TARGET", weight=0.5)
        graph.add_edge(f"target:{i}", "disease", type="IMPLICATED_IN", weight=0.9)
    extractor._graph = graph
    original = nx.shortest_simple_paths
    expected = list(original(graph, "drug", "disease"))[:max(k, 0)]
    computed = []

    def count_paths(*args, **kwargs):
        for path in original(*args, **kwargs):
            computed.append(path)
            yield path

    monkeypatch.setattr(nx, "shortest_simple_paths", count_paths)
    actual = extractor.extract_paths("drug", "disease", k=k)

    assert [[node.id for node in path.nodes] for path in actual] == expected
    assert computed == expected
    for path in actual:
        assert [edge.type for edge in path.edges] == ["HAS_TARGET", "IMPLICATED_IN"]
        assert [edge.weight for edge in path.edges] == [0.5, 0.9]
        assert path.score == 1 / 3


@pytest.fixture
def literature_cache(monkeypatch):
    monkeypatch.setattr(literature, "_cache", {})


async def test_literature_fetches_independent_sources_concurrently(monkeypatch, literature_cache):
    abstracts_started, metadata_started = asyncio.Event(), asyncio.Event()

    async def fetch_abstracts(pmids):
        abstracts_started.set()
        await asyncio.wait_for(metadata_started.wait(), timeout=1)
        return {"1": "First sentence. Second sentence. Third sentence. Fourth sentence."}

    async def fetch_metadata(pmids):
        metadata_started.set()
        await asyncio.wait_for(abstracts_started.wait(), timeout=1)
        return [{"pmid": "1", "title": "Study", "journal": "Journal", "year": "2026"}]

    monkeypatch.setattr(literature, "_efetch_abstracts", fetch_abstracts)
    monkeypatch.setattr(literature, "_esummary", fetch_metadata)

    result = await literature.summarize_literature(["1"])

    assert result["summaries"][0]["title"] == "Study"
    assert result["summaries"][0]["summary"] == (
        "First sentence. Second sentence. Third sentence."
    )


@pytest.mark.parametrize("failure", [None, "abstracts", "metadata", "both"])
async def test_literature_preserves_partial_results_and_cache(
    monkeypatch, literature_cache, failure
):
    abstracts = AsyncMock(return_value={"1": "Full abstract."})
    metadata = AsyncMock(return_value=[{"pmid": "1", "title": "Study", "abstract": "Title."}])
    if failure in ("abstracts", "both"):
        abstracts.side_effect = RuntimeError("Abstract service unavailable")
    if failure in ("metadata", "both"):
        metadata.side_effect = RuntimeError("Metadata service unavailable")
    monkeypatch.setattr(literature, "_efetch_abstracts", abstracts)
    monkeypatch.setattr(literature, "_esummary", metadata)

    result = await literature.summarize_literature(["1", "missing", "1"])
    cached = await literature.summarize_literature(["1", "missing", "1"])

    assert cached == result
    assert [item["pmid"] for item in result["summaries"]] == ["1", "missing", "1"]
    item = result["summaries"][0]
    assert item["title"] == ("Publication 1" if failure in ("metadata", "both") else "Study")
    if failure == "both":
        assert "Abstract could not be retrieved" in item["summary"]
    else:
        assert item["summary"] == ("Title." if failure == "abstracts" else "Full abstract.")
    abstracts.assert_awaited_once()
    metadata.assert_awaited_once()


async def test_cancelled_literature_request_cancels_both_fetches(monkeypatch, literature_cache):
    started = [asyncio.Event(), asyncio.Event()]
    cancelled = []

    async def fetch(index):
        started[index].set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.append(index)

    monkeypatch.setattr(literature, "_efetch_abstracts", lambda pmids: fetch(0))
    monkeypatch.setattr(literature, "_esummary", lambda pmids: fetch(1))
    task = asyncio.create_task(literature.summarize_literature(["1"]))
    try:
        await asyncio.wait_for(asyncio.gather(*(event.wait() for event in started)), timeout=1)
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert sorted(cancelled) == [0, 1]
    assert literature._cache == {}
