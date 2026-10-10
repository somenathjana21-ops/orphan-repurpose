"""
FAERS disproportionality analysis module.

Computes pharmacovigilance signal detection metrics from FAERS data:
- ROR (Reporting Odds Ratio)
- PRR (Proportional Reporting Ratio)
- BCPNN (Bayesian Confidence Propagation Neural Network)
- EBGM (Empirical Bayes Geometric Mean)

References:
- van der Elst et al. (2012) "The ROR and PRR"
- Norén et al. (2016) "A computationally efficient BCPNN"
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class ContingencyTable:
    """2x2 contingency table for a drug-event pair."""
    a: int  # drug + event
    b: int  # drug + other events
    c: int  # other drugs + event
    d: int  # other drugs + other events

    @property
    def total(self) -> int:
        return self.a + self.b + self.c + self.d

    @property
    def total_drug(self) -> int:
        return self.a + self.b

    @property
    def total_event(self) -> int:
        return self.a + self.c

    @property
    def total_other_drug(self) -> int:
        return self.c + self.d


@dataclass
class DisproportionalityResult:
    """Results of disproportionality analysis for a drug-event pair."""
    drug_id: str
    drug_name: str
    event: str
    meddra_pt: str
    n_reports: int  # a
    ror: float
    ror_ci_lower: float
    ror_ci_upper: float
    prr: float
    prr_chi2: float
    bcpnn_ic: float
    bcpnn_ic_lower: float
    bcpnn_ic_upper: float
    ebge: float  # EBGM
    level: str  # 'pass' | 'caution' | 'fail'


class FAERSAnalyzer:
    """Computes pharmacovigilance disproportionality metrics."""

    def __init__(self, min_reports: int = 3, ror_threshold: float = 2.0, prr_threshold: float = 2.0, bcpnn_threshold: float = 0.0):
        self.min_reports = min_reports
        self.ror_threshold = ror_threshold
        self.prr_threshold = prr_threshold
        self.bcpnn_threshold = bcpnn_threshold
        self._table_cache: Dict[Tuple[str, str], ContingencyTable] = {}

    def compute_ror(self, table: ContingencyTable) -> Tuple[float, float, float]:
        """Compute Reporting Odds Ratio with 95% confidence interval.

        ROR = (a/c) / (b/d) = (a*d) / (b*c)

        If any cell is 0, apply 0.5 correction.
        """
        a, b, c, d = table.a, table.b, table.c, table.d

        # Haldane-Anscombe correction for zero cells
        if a == 0 or b == 0 or c == 0 or d == 0:
            a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5

        ror = (a * d) / (b * c)

        # 95% CI
        se = math.sqrt(1/a + 1/b + 1/c + 1/d)
        ci_lower = math.exp(math.log(ror) - 1.96 * se)
        ci_upper = math.exp(math.log(ror) + 1.96 * se)

        return ror, ci_lower, ci_upper

    def compute_prr(self, table: ContingencyTable) -> Tuple[float, float]:
        """Compute Proportional Reporting Ratio with chi-square.

        PRR = (a / (a + c)) / (b / (b + d)) = (a * (b + d)) / (b * (a + c))

        If any cell is 0, apply 0.5 correction.
        """
        a, b, c, d = table.a, table.b, table.c, table.d

        # Haldane-Anscombe correction
        if a == 0 or b == 0 or c == 0 or d == 0:
            a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5

        prr = (a * (b + d)) / (b * (a + c))

        # Chi-square test
        n = a + b + c + d
        if n > 0:
            expected_a = (a + b) * (a + c) / n
            expected_c = (c + d) * (a + c) / n
            chi2 = 0.0
            if expected_a > 0:
                chi2 += (a - expected_a) ** 2 / expected_a
            if expected_c > 0:
                chi2 += (c - expected_c) ** 2 / expected_c
        else:
            chi2 = 0.0

        return prr, chi2

    def compute_bcpnn(self, table: ContingencyTable) -> Tuple[float, float, float]:
        """Compute Bayesian Confidence Propagation Neural Network (BCPNN).

        IC = log2( (a + gamma) / ((a + c) * (a + b) / (a + b + c + d + gamma)) )

        With 95% CI using the normal approximation.
        """
        a, b, c, d = table.a, table.b, table.c, table.d
        n = a + b + c + d

        # Prior (uniform)
        gamma = 0.5

        # Expected count under null
        expected = (a + c) * (a + b) / (n + gamma) if n > 0 else 1.0

        # Information Component
        ic = math.log2((a + gamma) / (expected + gamma)) if expected > 0 else 0.0

        # Variance of IC (approximate)
        if a > 0 and expected > 0:
            var_ic = 1.0 / ((a + gamma) * math.log(2) ** 2) + 1.0 / (expected * math.log(2) ** 2)
        else:
            var_ic = 1.0

        se_ic = math.sqrt(var_ic)
        ic_lower = ic - 1.96 * se_ic
        ic_upper = ic + 1.96 * se_ic

        return ic, ic_lower, ic_upper

    def compute_ebge(self, table: ContingencyTable) -> float:
        """Compute Empirical Bayes Geometric Mean (EBGM).

        EBGM = (a + 0.5) / ((a + c) * (a + b) / (a + b + c + d + 1))
        """
        a, b, c, d = table.a, table.b, table.c, table.d
        n = a + b + c + d

        numerator = a + 0.5
        denominator = (a + c) * (a + b) / (n + 1) if n > 0 else 1.0

        if denominator > 0:
            return numerator / denominator
        return 0.0

    def classify_signal(self, ror: float, prr: float, bcpnn_ic: float, n_reports: int) -> str:
        """Classify signal level based on thresholds.

        'fail': ROR >= 2 AND ROR CI lower > 1 AND PRR >= 2 AND BCPNN IC > 0
        'caution': ROR >= 1.5 OR PRR >= 1.5 OR BCPNN IC > -0.5
        'pass': otherwise
        """
        if n_reports < self.min_reports:
            return "pass"

        # Strong signal
        if ror >= self.ror_threshold and prr >= self.prr_threshold and bcpnn_ic > self.bcpnn_threshold:
            return "fail"

        # Weak signal
        if ror >= 1.5 or prr >= 1.5 or bcpnn_ic > -0.5:
            return "caution"

        return "pass"

    def analyze(
        self,
        drug_id: str,
        drug_name: str,
        event: str,
        meddra_pt: str,
        table: ContingencyTable,
    ) -> DisproportionalityResult:
        """Full disproportionality analysis for a drug-event pair."""
        ror, ror_lower, ror_upper = self.compute_ror(table)
        prr, prr_chi2 = self.compute_prr(table)
        bcpnn_ic, bcpnn_lower, bcpnn_upper = self.compute_bcpnn(table)
        ebge = self.compute_ebge(table)
        level = self.classify_signal(ror, prr, bcpnn_ic, table.a)

        return DisproportionalityResult(
            drug_id=drug_id,
            drug_name=drug_name,
            event=event,
            meddra_pt=meddra_pt,
            n_reports=table.a,
            ror=round(ror, 3),
            ror_ci_lower=round(ror_lower, 3),
            ror_ci_upper=round(ror_upper, 3),
            prr=round(prr, 3),
            prr_chi2=round(prr_chi2, 3),
            bcpnn_ic=round(bcpnn_ic, 3),
            bcpnn_ic_lower=round(bcpnn_lower, 3),
            bcpnn_ic_upper=round(bcpnn_upper, 3),
            ebge=round(ebge, 3),
            level=level,
        )


def compute_2x2_table(
    drug_event_count: int,
    drug_other_count: int,
    other_event_count: int,
    other_other_count: int,
) -> ContingencyTable:
    """Build a 2x2 contingency table from counts."""
    return ContingencyTable(
        a=drug_event_count,
        b=drug_other_count,
        c=other_event_count,
        d=other_other_count,
    )


def merge_faers_reports(
    reports: List[Dict[str, Any]],
) -> Dict[Tuple[str, str], ContingencyTable]:
    """Aggregate FAERS reports into drug-event count pairs.


    Each report: {drug_id, drug_name, event, meddra_pt, ...}
    Returns: {(drug_id, event): {a, b, c, d}}
    """
    # First pass: count per drug-event
    drug_event_counts: Dict[Tuple[str, str], int] = {}
    drug_counts: Dict[str, int] = {}
    event_counts: Dict[str, int] = {}
    total = 0

    for report in reports:
        drug_id = report.get("drug_id", "")
        event = report.get("event", "")
        if not drug_id or not event:
            continue

        key = (drug_id, event)
        drug_event_counts[key] = drug_event_counts.get(key, 0) + 1
        drug_counts[drug_id] = drug_counts.get(drug_id, 0) + 1
        event_counts[event] = event_counts.get(event, 0) + 1
        total += 1

    # Build 2x2 tables
    tables: Dict[Tuple[str, str], ContingencyTable] = {}
    for (drug_id, event), a in drug_event_counts.items():
        b = drug_counts[drug_id] - a
        c = event_counts[event] - a
        d = total - a - b - c
        tables[(drug_id, event)] = ContingencyTable(a=max(a, 0), b=max(b, 0), c=max(c, 0), d=max(d, 0))

    return tables
