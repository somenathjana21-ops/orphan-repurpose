#!/usr/bin/env python3
"""
Run FAERS disproportionality analysis.
Computes ROR (Reporting Odds Ratio), PRR (Proportional Reporting Ratio),
and BCPNN (Bayesian Confidence Propagation Neural Network) for drug-event pairs.

Reference: FDA FAERS disproportionality analysis methods
"""
import json
import math
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()


def compute_ror(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    """
    Compute Reporting Odds Ratio.
    a = drug+event, b = drug+no event, c = no drug+event, d = no drug+no event
    """
    if min(a, b, c, d) == 0:
        # Haldane-Anscombe correction
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    ror = (a * d) / (b * c)
    # 95% CI using log method
    se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    ci_low = math.exp(math.log(ror) - 1.96 * se)
    ci_high = math.exp(math.log(ror) + 1.96 * se)
    return ror, ci_low, ci_high


def compute_prr(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    """
    Compute Proportional Reporting Ratio.
    """
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    prr = (a / (a + b)) / (c / (c + d))
    # 95% CI
    se = math.sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d))
    ci_low = math.exp(math.log(prr) - 1.96 * se)
    ci_high = math.exp(math.log(prr) + 1.96 * se)
    return prr, ci_low, ci_high


def compute_bcpnn(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    """
    Compute Bayesian Confidence Propagation Neural Network (BCPNN) IC value.
    """
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    n = a + b + c + d
    # IC = log2( (a / (a+b)) / ((a+c) / n) )
    ic = math.log2((a / (a + b)) / ((a + c) / n))
    # Variance of IC
    var_ic = (1 / (a + 0.5) - 1 / (a + b + 0.5) +
              1 / (a + c + 0.5) - 1 / (n + 0.5))
    ci_low = ic - 1.96 * math.sqrt(var_ic)
    ci_high = ic + 1.96 * math.sqrt(var_ic)
    return ic, ci_low, ci_high


def run_disproportionality_analysis(drug_events: pd.DataFrame) -> pd.DataFrame:
    """Run disproportionality analysis on drug-event pairs."""
    if drug_events.empty:
        logger.warning("faers_no_data")
        return pd.DataFrame()

    # Build contingency table
    # For each drug-event pair, compute:
    # a = count of this drug-event pair
    # b = count of this drug with other events
    # c = count of other drugs with this event
    # d = count of other drug-event pairs

    drug_event_counts = drug_events.groupby(["drug_name", "event_name"]).size().reset_index(name="count")
    drug_totals = drug_events.groupby("drug_name").size().reset_index(name="drug_total")
    event_totals = drug_events.groupby("event_name").size().reset_index(name="event_total")
    grand_total = len(drug_events)

    # Merge
    df = drug_event_counts.merge(drug_totals, on="drug_name")
    df = df.merge(event_totals, on="event_name")

    # Compute a, b, c, d
    df["a"] = df["count"]
    df["b"] = df["drug_total"] - df["a"]
    df["c"] = df["event_total"] - df["a"]
    df["d"] = grand_total - df["a"] - df["b"] - df["c"]

    # Compute signals
    rors = []
    prrs = []
    bcpnns = []
    for _, row in df.iterrows():
        a, b, c, d = int(row["a"]), int(row["b"]), int(row["c"]), int(row["d"])
        ror, ror_ci_low, ror_ci_high = compute_ror(a, b, c, d)
        prr, prr_ci_low, prr_ci_high = compute_prr(a, b, c, d)
        ic, ic_ci_low, ic_ci_high = compute_bcpnn(a, b, c, d)
        rors.append({"ror": ror, "ror_ci_low": ror_ci_low, "ror_ci_high": ror_ci_high})
        prrs.append({"prr": prr, "prr_ci_low": prr_ci_low, "prr_ci_high": prr_ci_high})
        bcpnns.append({"ic": ic, "ic_ci_low": ic_ci_low, "ic_ci_high": ic_ci_high})

    ror_df = pd.DataFrame(rors)
    prr_df = pd.DataFrame(prrs)
    bcpnn_df = pd.DataFrame(bcpnns)

    result = pd.concat([df, ror_df, prr_df, bcpnn_df], axis=1)

    # Filter for signals (ROR CI lower bound > 1, PRR >= 2, IC CI lower bound > 0)
    result["is_signal"] = (
        (result["ror_ci_low"] > 1) &
        (result["prr"] >= 2) &
        (result["ic_ci_low"] > 0)
    )

    return result


def run_faers_signals(processed_dir: Path, output_dir: Path) -> None:
    """Run FAERS disproportionality analysis and save results."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load processed FAERS data
    faers_path = processed_dir / "faers_drug_events.parquet"
    if not faers_path.exists():
        logger.warning("faers_processed_missing", path=str(faers_path))
        # Create empty output
        pd.DataFrame().to_parquet(output_dir / "faers_signals.parquet", index=False)
        return

    drug_events = pd.read_parquet(faers_path)
    logger.info("faers_signals_input", rows=len(drug_events))

    # Run analysis
    signals = run_disproportionality_analysis(drug_events)
    logger.info("faers_signals_computed", total_pairs=len(signals),
                 signals=int(signals["is_signal"].sum()) if not signals.empty else 0)

    # Save results
    signals.to_parquet(output_dir / "faers_signals.parquet", index=False)
    signals.to_csv(output_dir / "faers_signals.csv", index=False)

    # Save significant signals only
    if not signals.empty:
        sig = signals[signals["is_signal"]].sort_values("ror", ascending=False)
        sig.to_parquet(output_dir / "faers_significant.parquet", index=False)
        sig.to_csv(output_dir / "faers_significant.csv", index=False)

        # Save summary
        summary = {
            "total_drug_event_pairs": len(signals),
            "significant_signals": len(sig),
            "unique_drugs": signals["drug_name"].nunique() if not signals.empty else 0,
            "unique_events": signals["event_name"].nunique() if not signals.empty else 0,
            "top_signals": sig.head(50)[["drug_name", "event_name", "ror", "prr", "ic"]].to_dict("records"),
        }
        with open(output_dir / "faers_signals_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

    logger.info("faers_signals_complete", output_dir=str(output_dir))


def main() -> None:
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data")
    processed_dir = data_dir / "processed" / "faers"
    output_dir = data_dir / "safety" / "faers_signals"

    print("⚠️  Computing FAERS disproportionality signals...")
    run_faers_signals(processed_dir, output_dir)
    print(f"\nFAERS signals complete. Output: {output_dir}")


if __name__ == "__main__":
    main()
