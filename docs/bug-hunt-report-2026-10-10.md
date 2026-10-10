# Bug hunt and fix report — 10 October 2026

Fixed 10 groups of functional defects across candidate identity, dossiers, audit persistence, configuration, packaging, and frontend connectivity. Final verification on Linux (repo `.venv`, Python 3.13): **252 backend tests passed, 82.18% coverage**, exceeding the 80% requirement. Frontend build and lint passed. Changes were committed on `pre-production`; pre-existing frontend/configuration edits were included.

## Codebase understanding

The React/Vite UI calls FastAPI through an Axios client. Disease data comes from processed Orphanet data with a curated fallback. Candidate generation maps disease identifiers to model keys, scores drugs through the indication service, and persists candidate records in SQLite. Kuzu supports knowledge-graph exploration; separate services provide explanations and safety assessments. Validation writes audit entries to SQLite, and dossiers combine disease and candidate data with a PDF/JSON export service.

I inspected those boundaries, used graphify's local structural extraction to map 94 code files (1,382 nodes and 2,487 edges), and ran the explicitly requested fix skill through Codex CLI for an independent audit review. The CLI supplied regression cases but stopped at the broken repository interpreter. I ran those cases in an isolated working environment, reproduced the failures, applied the fixes, and verified the combined changes. The structural map used no semantic LLM extraction (0 semantic extraction tokens); this is not a count of the coding session's tokens.

## Root causes and fixes applied

| # | Root cause and observed failure | Fix applied | Main location |
|---|---|---|---|
| 1 | Candidate IDs were based only on rank (`cand_001`, etc.). Generating another disease or changing rankings reused the same database keys and could change which drug an existing link or review referred to. | Generate deterministic IDs from both disease and drug. Rank no longer determines identity. | [candidates.py](prototype/backend/app/api/v1/candidates.py) |
| 2 | Dossiers used a separate disease-to-model lookup and filtered only candidate IDs, while the UI supplied drug IDs. Missing model output or mismatched IDs could silently produce an empty candidate list. | Reuse the candidate API's mapping, stable IDs, and curated fallback. Accept candidate IDs or drug IDs and reject unknown selections with HTTP 400. Renderer errors propagate as server errors rather than triggering a different mock dossier. | [dossier.py](prototype/backend/app/api/v1/dossier.py) |
| 3 | PDF rendering exceptions returned HTML bytes in `pdf_base64`, producing an invalid `.pdf` download. | Return an empty PDF payload on renderer failure. Keep JSON available and show a clear message in the UI. | [dossier_service.py](prototype/backend/app/services/dossier_service.py), [DossierBuilder.tsx](prototype/frontend/src/components/DossierBuilder.tsx) |
| 4 | `/sessions` was registered after `/{session_id}` in both audit and validation routers, so requests were interpreted as an audit trail named `sessions`. | Register the static session-list routes before the dynamic routes. | [audit.py](prototype/backend/app/api/v1/audit.py), [validation.py](prototype/backend/app/api/v1/validation.py) |
| 5 | Audit logging and audit session listing called async service functions without awaiting them. Logging returned a coroutine and did not persist the entry. | Await both service calls before building the response. | [audit.py](prototype/backend/app/api/v1/audit.py) |
| 6 | Audit reads did not initialize tables, although writes did. A fresh database could return HTTP 500 before the first write. | Apply lazy table initialization to trail reads and session enumeration. | [audit_service.py](prototype/backend/app/services/audit_service.py) |
| 7 | The audit cache was treated as authoritative. Appending after restart cached only the new entry; other service instances' writes and changes to persisted data could remain invisible, including during verification. | Read trails from SQLite and invalidate cached snapshots after writes. Verification now examines persisted content. | [audit_service.py](prototype/backend/app/services/audit_service.py) |
| 8 | The settings loader read `DATABASE_URL` from `.env`, but the database module separately used `os.getenv`, ignoring that loaded value. | Build the database engine from the shared settings object. | [database.py](prototype/backend/app/db/database.py) |
| 9 | The explicit setuptools package list omitted `app.db` and `app.ml`. Built wheels lacked modules required at runtime. | Discover the `app` package and its subpackages. Confirmed that the rebuilt wheel contains and imports the missing modules outside the checkout. | [pyproject.toml](prototype/backend/pyproject.toml) |
| 10 | The API client defaulted to the browser user's `localhost:8000`, bypassing Vite's proxy. The health indicator independently used a relative URL and could probe a different server or accept an unrelated HTTP 200 page as healthy. | Default to same-origin API requests, retain `VITE_API_URL` overrides, and probe health through the same Axios client while checking the response status field. | [api.ts](prototype/frontend/src/services/api.ts), [Layout.tsx](prototype/frontend/src/components/Layout.tsx) |

## Validation

Added **22 regression cases** across four files:

- [test_audit_regressions.py](prototype/backend/tests/test_audit_regressions.py): 12 cases covering route dispatch, awaited persistence, empty databases, restart history, other writers, and persisted tampering.
- [test_candidate_identity.py](prototype/backend/tests/test_candidate_identity.py): 8 cases covering disease separation, stable drug identity across ranking changes, dossier selection with and without model availability, and invalid selections.
- [test_database_config.py](prototype/backend/tests/test_database_config.py): a subprocess loads a temporary `.env` and creates the database at its configured location.
- [test_dossier_export.py](prototype/backend/tests/test_dossier_export.py): renderer failure must not return HTML as a PDF.

Also tightened the existing dossier error test to require 404 for an unknown disease and 400 for an unknown candidate instead of accepting successful or arbitrary error responses.

| Check | Result |
|---|---|
| Full backend suite, `pytest --cov=app --cov-report=term-missing --cov-fail-under=80 -q` | 252 passed; 82.18% coverage (re-verified on Linux in the repo `.venv`, Python 3.13) |
| Frontend `npm run build` | Passed: TypeScript compilation and Vite production build |
| Frontend `npm run lint` | Passed |
| Backend wheel build and import smoke check outside checkout | Passed: FastAPI application, database module, and ML module imported from the wheel |
| API URL contract smoke check | Passed for same-origin defaults and an explicit backend override, including `/health` |
| Ruff on new regression files and the otherwise lint-clean changed backend files | Passed |
| Ruff on all backend application code | 73 pre-existing findings; none on added lines |
| Full mypy check | Blocked by syntax errors in installed RDKit stubs (`rdmolfiles.pyi`: duplicate parameter and invalid argument ordering) |

The fixes were originally produced and verified on a Windows host (Python 3.11 in a temporary environment), because the repository `.venv` had been copied from Linux and could not run there. They were re-verified on Linux in the repository `.venv` (Python 3.13) as part of committing: 252 tests passed at 82.18% coverage, and the frontend build and lint passed after locally installing the missing `@rollup/rollup-linux-x64-gnu` optional dependency (no manifest or lockfile changes). During that re-verification two test expectations were corrected to match verified data rather than a stale demo fixture: `test_candidate_identity.py` now asserts the real Orphanet name for `ORPHA:793` (SAPHO syndrome; the curated demo generator still labels it "Cystic fibrosis"), and one over-long test signature was wrapped to satisfy the 100-character ruff limit. Full-suite audit and candidate writes are directed to temporary SQLite databases. `ruff` reports 73 pre-existing findings across backend application code (all `E501` line-length or similar), none on lines added by this work.

## Risk and remaining limitations

- **Candidate ID compatibility:** newly generated IDs differ from the old rank IDs. Existing persisted rows and historical validation records are retained, but already-overwritten historical identities cannot be reconstructed. Regenerate candidate lists and use the IDs returned by the API; unknown or stale dossier selections now produce HTTP 400.
- **Backend routing:** deployments without a same-origin API proxy must set `VITE_API_URL`. The development proxy already handles `/api` and `/health`.
- **PDF availability:** the failure path and JSON fallback were tested. Successful native WeasyPrint rendering and visual PDF quality were not validated in this environment.
- **Audit scope:** sequential writes from multiple service instances and persisted tampering are covered. Concurrent append serialization across processes was not tested or redesigned.
- **Quality checks:** backend-wide lint and mypy are not clean for the reasons above. The frontend dependency install also reported 11 dependency vulnerabilities (5 moderate, 6 high); dependency upgrades were not included in this functional bug-fix pass.
- **Scope:** this was a targeted functional review, not proof that every defect is fixed. Browser end-to-end interaction, model retraining, predictive accuracy, and scientific validity of the prototype's curated or placeholder outputs were not evaluated.
