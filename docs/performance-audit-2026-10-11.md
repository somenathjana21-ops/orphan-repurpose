# Performance audit — 11 October 2026

Implemented three focused optimizations without adding dependencies. Existing uncommitted
work was preserved. Benchmarks compare the affected functions at commit `7601893` with
the working-tree implementations.

## Implemented changes

| Area | Change | Preserved behavior |
| --- | --- | --- |
| `prototype/backend/app/api/v1/kg.py` | Use a set to deduplicate graph edges, index disease genes by symbol, remove an unused connection list, and reuse endpoint lookups instead of querying both nodes twice. | Response order, first duplicate's evidence, multiple genes sharing a symbol, node properties, and missing-node 404s. |
| `prototype/scripts/etl/train_indication_model_fast.py` | Actually batch disconnected molecular graphs during embedding precomputation; pass the training batch size through. Reuse the feature-dimension constant and remove unused imports. | Drug order, embedding shapes, NumPy checkpoint values, and equivalent embeddings within floating-point tolerance. Invalid batch sizes now fail explicitly. |
| `prototype/scripts/etl/compute_molecular_features.py` | Parse each SMILES once, reuse the molecule for both fingerprints and descriptors, convert fingerprints through RDKit's native NumPy conversion, and iterate columns without constructing a pandas Series per row. | Fingerprint bits and dtype, descriptors, IDs and row indices, custom columns and fingerprint parameters, empty inputs, and invalid-structure fallbacks. String-based helper calls still work. |

Graph construction replaces repeated edge scans with expected constant-time membership
checks. Target-to-gene matching now costs O(targets + genes + matches), rather than
O(targets × genes). Successful subgraph requests use five queries instead of seven
at depths below three, and six instead of eight at greater depths.

## Local measurements

Windows, Intel Core i5-12450H, Python 3.11.9, PyTorch 2.11.0 CPU; one PyTorch thread.
Each version was warmed up before measuring. Values are medians of five runs,
except molecular features, which used three runs.

| Component workload | Before | After | Improvement |
| --- | ---: | ---: | ---: |
| Subgraph assembly: 300 targets, 900 genes, 2,601 unique edges | 232.48 ms | 4.96 ms | 46.9× |
| Drug embeddings: 256 small molecules, hidden dimension 64, batches of 64 | 125.89 ms | 52.62 ms | 2.39× |
| Molecular features: 64 small molecules, all descriptors | 280.41 ms | 272.63 ms | 1.03× |

The graph benchmark uses a mocked database to isolate assembly time. It does not
measure Kuzu query latency. Both versions returned identical graph dictionaries.
Fingerprint arrays and descriptor frames matched exactly; embeddings were compared
with absolute and relative tolerances of 1e-6 using the same random seed.

These are component benchmarks on synthetic inputs, not whole-platform latency or
large-dataset throughput claims. Descriptor computation still dominates molecular
feature time; parsing less often produces a modest total improvement in this workload.

## Validation

- Initial suite: 324 tests passed, 86.77% application coverage.
- Final suite: **339 tests passed, 87.98% application coverage**, exceeding the 80% floor.
- Added 15 regression cases in `prototype/backend/tests/test_performance_audit.py`.
- All four changed Python files pass Ruff using the backend configuration.
- Frontend production build and ESLint passed. No frontend changes were needed for these fixes.
- Full backend Ruff still reports 74 existing violations elsewhere, down from 76.
- Full mypy stops at malformed installed RDKit stubs: a duplicate `structstd` parameter
  and a required parameter following a default parameter in `rdmolfiles.pyi:1598`.

Backend validation used `.venv-perf/Scripts/python.exe` from `prototype/backend/`:

```text
python -m pytest tests/ -q --cov=app --cov-fail-under=80
python -m ruff check app/api/v1/kg.py tests/test_performance_audit.py ../scripts/etl/compute_molecular_features.py ../scripts/etl/train_indication_model_fast.py
```

## Other findings and limits

The audit also inspected inference batching and locking, async request handling,
candidate persistence, explanation and safety caches, literature requests, graph
loading, and frontend routes and queries. Several useful optimizations already
exist: bounded inference batches, shared services, grouped candidate writes,
worker-thread execution for slow synchronous work, concurrent literature fetches,
lazy routes, and five-minute frontend query freshness.

Further opportunities require separate validation:

- **Fast-training checkpoint compatibility:** the fast trainer already saves
  `DualEncoderCrossAttention_Fast` with nested component state dictionaries.
  `IndicationService` supports the simple MLP explicitly and otherwise constructs
  the standard end-to-end model. These checkpoint formats do not match. This audit
  verifies embedding precomputation, not serving a newly trained fast checkpoint.
- **Bulk graph ingestion:** `build_kg.py` constructs pandas row objects and issues
  individual MERGE statements. Bulk import needs duplicate-ID, null-field, and
  relationship integrity checks against representative datasets.
- **Cache growth and freshness:** literature and explanation caches have no size
  bound. A long-lived deployment needs measured limits and explicit expiry rules;
  eviction or expiry can change how often external sources and models are invoked.
- **Search request volume:** Dashboard and KGBrowser query keys follow input changes
  directly. Debouncing and cancellation could reduce requests, but should be tested
  together with pagination, filters, and loading behavior in the browser.

GPU behavior, full retraining, production-scale graph ingestion, browser interaction,
and concurrent load were not benchmarked. Batching can slightly change floating-point
rounding and uses memory proportional to the configured batch's total atom count.
