# Bug hunt report — 2026-10-11

This pass continues after commit `13c4052`, which fixed candidate persistence, dossier selection, audit integrity, configuration, and packaging. This report covers the additional source changes only.

## Root causes and fixes

| Defect | Root cause | Fix applied |
| --- | --- | --- |
| Benchmark links and candidates referred to unrelated diseases | Curated fixtures reused incorrect Orphanet codes; NPC also used a broader Niemann–Pick UMLS concept. | Corrected identifiers across API fallbacks, frontend navigation and examples, demo data, literature/pathway download fixtures, tests, README, and Makefile. Candidate inference now imports the disease API's shared cross-reference map. |
| CF fixture could overwrite a different disease concept | The demo generator assigned `ORPHA:586` to Wiskott–Aldrich syndrome, colliding with the corrected cystic fibrosis record. | Corrected the Wiskott–Aldrich record and its indication pairs to `ORPHA:906`; regression checks enforce unique disease keys and preserve both concepts. |
| Supplied empty FAERS reports triggered a remote fetch | `if faers_reports` treated `[]` and omitted evidence identically. | Fetch only when reports are `None`; an explicit empty list remains the supplied evidence. |
| Cached FAERS readers always received an empty list | Assessments never populated `_faers_cache`. | Store each completed FAERS analysis, including empty results that replace previous signals. |
| ADMET results remained stale after molecular inputs changed | Cache entries were keyed only by drug ID. | Reuse predictions only when the drug's SMILES also matches; clear the associated SMILES metadata with the cache. |
| Explanations used outdated predictions or descriptions | Cache hits checked only the drug/disease pair. | Match probability, mechanism, and both names too. Failed refreshes invalidate the previous entry and return a fallback for the current inputs. |
| CLI demo failed during safety and validation | Async service methods were called without `await`; the scorer received unsupported `top_k`; missing models caused an early exit. | Run the demo with `asyncio.run`, await safety/audit methods, use the supported scorer, and retain curated fallback when the model is unavailable. Use an exact NPC concept match. |
| Demo exports and validation referred to inconsistent candidates | The script created separate rank-based candidate IDs and relative output paths. | Reuse canonical candidate construction for dossier and validation IDs; anchor output paths to the project. Do not save an empty PDF when rendering is unavailable. |
| Model drug names disappeared from demo dossiers launched at the repository root | Metadata paths depended on the working directory, and canonical candidate construction ignored names already resolved by the demo. | Load drug metadata from `settings.PROCESSED_DATA_DIR` and retain a score's explicitly resolved drug name. |
| Endpoint checks printed misleading 404/405 responses | Verification called nonexistent candidate, KG, audit, and validation paths. | Use candidate generation POST, plural KG disease route, and the two session-list routes. |

## Verified identifiers

| Disease | Correct Orphanet code | UMLS concept | Primary source |
| --- | --- | --- | --- |
| Niemann–Pick disease type C | ORPHA:646 | C0220756 | [Orphanet](https://www.orpha.net/en/disease/detail/646?mode=name) |
| Cystic fibrosis | ORPHA:586 | C0010674 | [Orphanet](https://www.orpha.net/en/disease/detail/586?mode=orpha) |
| Huntington disease | ORPHA:399 | C0020179 | [ORDO](https://www.orpha.net/ORDO/Orphanet_399) |
| Gaucher disease | ORPHA:355 | C0017205 | [Orphanet](https://www.orpha.net/en/disease/detail/355?mode=name) |
| Tuberous sclerosis complex | ORPHA:805 | C0041341 | [ORDO](https://www.orpha.net/ORDO/Orphanet_805) |
| Wiskott–Aldrich syndrome | ORPHA:906 | C0043194 | [Orphanet](https://www.orpha.net/en/disease/detail/906?mode=name&search=) |

Old codes are not aliases: for example, the loaded Orphanet dataset identifies `ORPHA:635` as neuroblastoma and `ORPHA:793` as SAPHO syndrome. With the model disabled, those IDs no longer receive NPC or CF demo candidates.

## Validation

- Added 24 regression cases across five new regression files for disease identifiers, safety caches, explanation caches, the demo pipeline, and candidate metadata.
- First reproduced 14 failing identifier/cache cases and two failing demo cases before implementing their fixes.
- Full backend validation: **276 tests passed at 82.63% coverage**, above the required **80%** floor.
- Frontend production build and ESLint passed.
- Ruff passed for both modified cache services, the CLI demo, and all five new regression files. The backend app retains **73 existing Ruff findings**, with **zero findings on added lines**.
- `git diff --check` passed. Tests used temporary SQLite and coverage files.
- The demo tests mock external services and cover both model availability modes, awaited calls, canonical validation IDs, and PDF renderer unavailability. They do not validate live FAERS requests or real PDF rendering.
- A missing Windows Rollup optional package was repaired locally for the frontend build; dependency manifests and lockfile contents were not changed.
- Independent Codex CLI review identified the demo drug-name regression above; it was fixed and covered by metadata and demo regression tests. No other actionable regressions were reported.

## Risk and remaining limitations

- Existing generated data, KG embeddings, model weights, saved candidates, and historical dossiers are not rewritten. Artifacts built with the old synthetic identifiers need regeneration and review; changing source constants cannot repair trained disease semantics.
- The loaded checkpoint contains legacy benchmark identifiers and lacks the verified benchmark UMLS keys. Benchmark generation therefore uses curated fallback when the model has no matching scores. This pass does not claim newly validated model predictions.
- This pass verifies the six listed disease concepts. Other synthetic fixture identifiers and scientific assertions have not received a complete ontology or clinical audit.
- Existing backend lint/type-check debt and native PDF dependencies remain outside this pass.
- Unrelated existing workspace changes are excluded from the bug-fix commit. No push is performed.
