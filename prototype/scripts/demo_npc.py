#!/usr/bin/env python3
"""
End-to-end Niemann-Pick Type C (NPC) demo pipeline.

Demonstrates the full OrphanRepurpose workflow:
1. Disease selection (NPC)
2. Candidate generation from model
3. Explanation (KG paths, SHAP, counterfactuals, LLM rationale)
4. Safety assessment (FAERS + ADMET)
5. Dossier generation
6. Validation

Usage:
    python scripts/demo_npc.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add backend to path when running directly from any working directory.
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir))


def print_header(title: str) -> None:
    """Print a prominent stage heading."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_section(title: str) -> None:
    """Print a compact subsection heading."""
    print(f"\n--- {title} ---")


async def main() -> None:
    """Run the NPC research demo, falling back when the model lacks its concept."""
    print_header("OrphanRepurpose — NPC Demo Pipeline")
    print(f"Started: {datetime.now(UTC).isoformat()}")

    # 1. Disease Selection
    print_header("Step 1: Disease Selection")
    disease_id = "ORPHA:646"
    disease_name = "Niemann-Pick disease type C"
    print(f"Disease: {disease_name} ({disease_id})")
    print("Prevalence: 0.5 per 100,000 (ultra-rare)")
    print("Genes: NPC1, NPC2")
    print("Existing treatments: Miglustat (symptomatic only)")
    print("Unmet need: HIGH — no disease-modifying therapy")

    # 2. Candidate Generation
    print_header("Step 2: Candidate Generation")
    try:
        from app.services.indication_service import get_indication_service

        svc = get_indication_service()
        ready = svc.is_ready()
        if ready:
            print(f"Model: {svc.config.get('architecture', 'unknown')}")
            print(f"Drugs: {len(svc.drug_smiles)}")
            print(f"Diseases: {len(svc.disease_map)}")
            print(f"Temperature: {svc.temperature}")
            print(f"Conformal q: {svc.conformal_q}")

        # Match the exact NPC concept; a broader Niemann-Pick key is not equivalent.
        from app.api.v1.diseases import ORPHA_TO_UMLS

        npc_key = None
        if ready and ORPHA_TO_UMLS[disease_id] in svc.disease_map:
            npc_key = ORPHA_TO_UMLS[disease_id]

        if npc_key is None:
            print("WARNING: NPC disease not found in model, using fallback")
            # Use fallback demo candidates
            candidates = [
                {"drug_id": "drugcentral:1001", "drug_name": "Miglustat", "probability": 0.85},
                {"drug_id": "drugcentral:1002", "drug_name": "Sirolimus", "probability": 0.72},
            ]
        else:
            print(f"Disease key: {npc_key}")
            scores = svc.score_all_for_orpha(npc_key, top_k=5)
            candidates = []
            for s in scores:
                drug_id = s["drug_id"]
                name = drug_id.split(":")[-1]
                # Try to get drug name from DrugCentral data
                try:
                    import pandas as pd

                    from app.core.config import settings

                    dc_path = (
                        Path(settings.PROCESSED_DATA_DIR)
                        / "drugcentral/drugcentral_fda_approved.parquet"
                    )
                    if dc_path.exists():
                        df = pd.read_parquet(dc_path)
                        row = df[df["struct_id"].astype(str) == drug_id.split(":")[-1]]
                        if len(row) > 0:
                            name = row.iloc[0].get("name", name)
                except Exception:
                    pass
                candidates.append(
                    {
                        "drug_id": drug_id,
                        "drug_name": name,
                        "probability": s["probability"],
                        "ci_lower": s["ci_lower"],
                        "ci_upper": s["ci_upper"],
                    }
                )

        from app.api.v1.candidates import _candidate_from_score

        cand_objs = [
            _candidate_from_score(
                i + 1,
                {**c, "ci_lower": c.get("ci_lower", 0.0), "ci_upper": c.get("ci_upper", 1.0)},
                disease_id,
            )
            for i, c in enumerate(candidates[:5])
        ]

        print(f"\nTop {len(candidates)} candidates:")
        for i, c in enumerate(candidates, 1):
            print(f"  {i}. {c['drug_name']} ({c['drug_id']}) — p={c['probability']:.3f}")

    except Exception as e:
        print(f"ERROR in candidate generation: {e}")
        import traceback

        traceback.print_exc()
        return

    # 3. Explanation
    print_header("Step 3: Explanation")
    try:
        from app.services.explanation_service import get_explanation_service

        exp_svc = get_explanation_service()

        if candidates:
            top = candidates[0]
            print(f"Explaining: {top['drug_name']} for {disease_name}")

            explanation = exp_svc.explain_candidate(
                drug_id=top["drug_id"],
                disease_id=npc_key or disease_id,
                drug_name=top["drug_name"],
                disease_name=disease_name,
                probability=top["probability"],
                moa_summary=cand_objs[0].moa_summary,
            )

            print(f"\n  KG Paths: {len(explanation.get('kg_paths', []))}")
            for i, path in enumerate(explanation.get("kg_paths", [])[:3]):
                nodes = " → ".join([n["name"] for n in path.get("nodes", [])])
                print(f"    Path {i + 1} (score={path.get('score', 0):.3f}): {nodes}")

            print("\n  SHAP Values (top 5):")
            shap = explanation.get("shap_values", {})
            for feat, val in list(shap.items())[:5]:
                print(f"    {feat}: {val:+.4f}")

            print(f"\n  Counterfactuals: {len(explanation.get('counterfactuals', []))}")
            for cf in explanation.get("counterfactuals", [])[:2]:
                print(f"    {cf.get('description', '')[:100]}...")

            print("\n  LLM Rationale:")
            print(f"    {explanation.get('llm_rationale', 'N/A')[:200]}...")

    except Exception as e:
        print(f"ERROR in explanation: {e}")
        import traceback

        traceback.print_exc()

    # 4. Safety Assessment
    print_header("Step 4: Safety Assessment")
    try:
        from app.services.safety_service import get_safety_service

        safety_svc = get_safety_service()

        if candidates:
            top = candidates[0]
            print(f"Assessing safety: {top['drug_name']}")

            # Get SMILES
            smiles = ""
            try:
                from app.services.indication_service import get_indication_service

                ind_svc = get_indication_service()
                if ind_svc.is_ready():
                    smiles = ind_svc.drug_smiles.get(top["drug_id"], "")
            except Exception:
                pass

            safety = await safety_svc.assess_drug(
                drug_id=top["drug_id"],
                drug_name=top["drug_name"],
                smiles=smiles,
            )

            print(f"\n  FAERS Signals: {len(safety.get('faers_signals', []))}")
            for sig in safety.get("faers_signals", [])[:3]:
                print(
                    f"    {sig.get('meddra_pt')}: ROR={sig.get('ror')}, "
                    f"PRR={sig.get('prr')}, BCPNN={sig.get('bcpnn')}"
                )

            print(f"\n  ADMET Predictions: {len(safety.get('admet_predictions', {}))} endpoints")
            admet = safety.get("admet_predictions", {})
            for endpoint in ["Caco2", "hERG", "DILI", "BBB"]:
                if endpoint in admet:
                    print(f"    {endpoint}: {admet[endpoint]:.3f}")

            print(f"\n  Contraindications: {len(safety.get('contraindications', []))}")
            for c in safety.get("contraindications", [])[:3]:
                print(f"    - {c}")

            print(f"\n  Overall Safety: {safety.get('overall', 'unknown').upper()}")

    except Exception as e:
        print(f"ERROR in safety assessment: {e}")
        import traceback

        traceback.print_exc()

    # 5. Dossier Generation
    print_header("Step 5: Dossier Generation")
    try:
        from app.api.v1.diseases import _DISEASE_BY_ID, _to_detail
        from app.services.dossier_service import get_dossier_service

        dossier_svc = get_dossier_service()
        disease = _to_detail(_DISEASE_BY_ID[disease_id])

        if disease and candidates:
            result = dossier_svc.generate_dossier(
                disease=disease,
                candidates=cand_objs,
                sections=[
                    "background",
                    "drug_profile",
                    "mechanistic_rationale",
                    "preclinical_plan",
                    "regulatory_strategy",
                ],
                audit_trail_id="demo-npc-001",
            )

            print(f"  PDF generated: {len(result['pdf_base64'])} bytes (base64)")
            print(f"  Audit trail ID: {result['audit_trail_id']}")
            print(f"  Dossier JSON keys: {list(result['dossier_json'].sections.keys())}")

            # Save PDF
            import base64

            if result["pdf_base64"]:
                pdf_path = backend_dir.parent / "data" / "npc_dossier.pdf"
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                pdf_path.write_bytes(base64.b64decode(result["pdf_base64"]))
                print(f"  PDF saved to: {pdf_path}")
            else:
                print("  PDF renderer unavailable; JSON dossier remains available.")

    except Exception as e:
        print(f"ERROR in dossier generation: {e}")
        import traceback

        traceback.print_exc()

    # 6. Validation
    print_header("Step 6: Validation")
    try:
        from app.services.audit_service import get_audit_service

        audit_svc = get_audit_service()
        session_id = "demo-npc-session-001"

        # Record validation
        entry1 = await audit_svc.add_entry(
            session_id=session_id,
            entry_type="validation",
            user="Dr. Smith (Neurologist)",
            data={
                "candidate_id": cand_objs[0].candidate_id if cand_objs else None,
                "assessment": "plausible",
                "rationale": "Miglustat has known safety profile and plausible mechanism for NPC.",
            },
        )
        print(f"  Validation recorded: {entry1.hash[:16]}...")

        # Record self-assessment
        entry2 = await audit_svc.add_entry(
            session_id=session_id,
            entry_type="self_assessment",
            user="self",
            data={
                "candidate_id": cand_objs[0].candidate_id if cand_objs else None,
                "efficacy": 7,
                "safety": 6,
                "feasibility": 8,
                "notes": "Approved drug with known safety. Strong mechanistic rationale.",
            },
        )
        print(f"  Self-assessment recorded: {entry2.hash[:16]}...")

        # Verify
        result = await audit_svc.verify(session_id)
        print(f"  Audit trail valid: {result['valid']}")
        print(f"  Entries: {result.get('entry_count', 0)}")

    except Exception as e:
        print(f"ERROR in validation: {e}")
        import traceback

        traceback.print_exc()

    # Summary
    print_header("Demo Complete")
    print(f"Finished: {datetime.now(UTC).isoformat()}")
    print("\nPipeline summary:")
    print(f"  Disease: {disease_name}")
    print(f"  Candidates: {len(candidates)}")
    print(f"  Top candidate: {candidates[0]['drug_name'] if candidates else 'N/A'}")
    print(f"  Model probability: {candidates[0]['probability']:.3f}" if candidates else "  N/A")
    print("  Explanation: KG paths, SHAP, counterfactuals, LLM rationale")
    print("  Safety: FAERS signals, ADMET predictions, contraindications")
    print("  Dossier: PDF + JSON with credibility map")
    print("  Validation: Immutable audit trail with hash chain")
    print("\nAll outputs require human expert review before any regulatory use.")


if __name__ == "__main__":
    asyncio.run(main())
