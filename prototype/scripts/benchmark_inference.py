"""Compare serial and batched inference on reproducible synthetic drug inputs.

Run from the repository root: python prototype/scripts/benchmark_inference.py
This measures inference overhead, not biological accuracy or production latency.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from time import perf_counter

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.ml.featurizer import ATOM_FEATURE_DIM  # noqa: E402
from app.ml.indication_model import IndicationModel, SimpleIndicationModel  # noqa: E402
from app.services.indication_service import IndicationService  # noqa: E402


def benchmark(architecture: str, drugs: int, batch_size: int, repeats: int) -> dict:
    """Measure warmed inference with the same model and inputs at two batch sizes."""
    torch.manual_seed(42)
    service = IndicationService(batch_size=batch_size)
    if architecture == "MLP":
        service.model = SimpleIndicationModel(fp_dim=128, kg_dim=32, hidden_dim=64)
        service.config = {"architecture": "SimpleIndicationModel_MLP"}
    else:
        service.model = IndicationModel(
            node_feature_dim=ATOM_FEATURE_DIM, kg_dim=32, hidden_dim=64, num_layers=2
        )
    service.model.eval()
    service.drug_smiles = {str(i): "CC(=O)Oc1ccccc1C(=O)O" for i in range(drugs)}
    service.drug_fingerprints = {str(i): torch.randn(128) for i in range(drugs)}
    service.disease_map = {"synthetic": 0}
    service.disease_embeddings = torch.randn(1, 32)
    service._loaded = True

    timings = {}
    outputs = {}
    # Warm both paths first, including the molecular graph cache.
    for label, size in (("serial", 1), ("batched", batch_size)):
        service.batch_size = size
        outputs[label] = service.score_drugs("synthetic")
    serial = {r["drug_id"]: r["probability"] for r in outputs["serial"]}
    error = max(abs(r["probability"] - serial[r["drug_id"]]) for r in outputs["batched"])
    if error > 1e-6:
        raise AssertionError(f"Batched probabilities drifted: {error}")

    # Alternate the paths to reduce systematic bias from timing them in separate runs.
    samples: dict[str, list[float]] = {"serial": [], "batched": []}
    for repeat in range(repeats):
        paths = [("serial", 1), ("batched", batch_size)]
        for label, size in paths if repeat % 2 == 0 else reversed(paths):
            service.batch_size = size
            start = perf_counter()
            service.score_drugs("synthetic")
            samples[label].append((perf_counter() - start) * 1000)
    for label, values in samples.items():
        timings[label] = round(statistics.median(values), 3)
    return {
        "architecture": architecture,
        "drugs": drugs,
        "batch_size": batch_size,
        "median_ms": timings,
        "speedup": round(timings["serial"] / timings["batched"], 2),
        "max_probability_error": error,
    }


def main() -> None:
    """Print reproducible performance measurements as JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drugs", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()
    if min(args.drugs, args.batch_size, args.repeats, args.threads) < 1:
        parser.error("all arguments must be positive")
    torch.set_num_threads(args.threads)
    print(
        json.dumps(
            {
                "fixture": "synthetic, warm CPU inference, batch size 1 reference",
                "torch": torch.__version__,
                "threads": args.threads,
                "results": [
                    benchmark(arch, args.drugs, args.batch_size, args.repeats)
                    for arch in ("MLP", "GNN")
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
