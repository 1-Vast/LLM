"""Training-reference forecasts with separate local and marginal group support.

Conditional counts shrink toward disjoint target-condition references. The two
prior units are modelling weight, never additional measured reference groups.
This experimental model accepts no held-out compound, profile or mechanism truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
from scipy.stats import beta

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dynamic_world_model"))
import common as C  # noqa: E402

LABELS = ("profile_matches_h1", "profile_matches_h2", "profile_unresolved", "no_detectable_response")
KAPPA = 2.0


@dataclass(frozen=True)
class Branch:
    hypothesis: str
    probabilities: dict[str, float]
    alpha: dict[str, float]
    p_correct: float
    p_wrong: float
    value_mean: float
    value_variance: float
    wrong_upper95: float
    local_compounds: tuple[str, ...]
    local_groups: tuple[str, ...]
    parent_compounds: tuple[str, ...]
    parent_groups: tuple[str, ...]
    local_support: int
    parent_support: int
    basis: str
    prior_strength: float


@dataclass(frozen=True)
class Forecast:
    branches: dict[str, Branch]
    refusal: str | None = None

    def branch_for(self, hypothesis):
        return self.branches.get(hypothesis)


class SparseReferenceModel:
    """One outer-training fold, its frozen validator, and compound-to-split-group IDs.

    ``group_map`` uses scaffold/identity groups, matching the held-out split unit.
    Every group contributes total weight one even if it contains multiple compounds.
    Marginal backoff is explicit; it does not establish conditional exchangeability.
    """

    def __init__(self, ft, params, group_map, *, pooling=True):
        self.ft, self.params, self.group_map = ft, params, group_map
        self.pooling = pooling
        self._cache = {}

    def _readings(self, key, own, other, h1):
        if key not in self.ft.tables:
            return {}
        table = self.ft.tables[key]
        names = [c for c, klass in zip(table.names, table.klass) if klass == own]
        if not self.params["eliminates"]:
            detected = dict(zip(table.names, table.detected))
            return {c: LABELS[2] if detected[c] else LABELS[3] for c in names}
        outcomes = C.loo_outcomes(self.ft, key, self.params["floor"], self.params["margin"])
        labels = {"eliminate_b": LABELS[0 if own == h1 else 1],
                  "eliminate_a": LABELS[1 if own == h1 else 0],
                  "ambiguous": LABELS[2], "undetected": LABELS[3]}
        return {c: labels[outcomes[c, other]] for c in names}

    def _counts(self, refs, readings):
        grouped = {}
        for compound in refs:
            grouped.setdefault(str(self.group_map[compound]), []).append(compound)
        counts = np.zeros(len(LABELS))
        for members in grouped.values():
            for compound in members:
                counts[LABELS.index(readings[compound])] += 1 / len(members)
        return counts, tuple(sorted(grouped))

    def forecast(self, target, h1, h2, *, source=None, observed_label=None):
        if (source is None) != (observed_label is None):
            raise ValueError("source_and_observed_label_must_be_supplied_together")
        if observed_label is not None and observed_label not in LABELS[2:]:
            raise ValueError("conditioning_requires_neutral_outcome")
        query = (target, h1, h2, source, observed_label)
        if query not in self._cache:
            self._cache[query] = self._forecast(target, h1, h2, source, observed_label)
        return self._cache[query]

    def _forecast(self, target, h1, h2, source, observed_label):
        branches = {}
        for own, other in ((h1, h2), (h2, h1)):
            readings = self._readings(target, own, other, h1)
            if not readings:
                return Forecast({}, f"no_target_references:{own}")
            first = self._readings(source, own, other, h1) if source is not None else {}
            local = tuple(sorted(c for c in readings if source is not None and first.get(c) == observed_label))
            local_counts, local_groups = self._counts(local, readings)
            # Exclude entire local groups, including aliases that did not match the first label.
            parent = tuple(sorted(c for c in readings if str(self.group_map[c]) not in local_groups))
            parent_counts, parent_groups = self._counts(parent, readings)
            if source is None:
                alpha = parent_counts + 0.5
                basis = "unconditional"
            elif not self.pooling:
                if not local:
                    return Forecast({}, f"no_paired_references:{own}:{observed_label}")
                alpha = local_counts + 0.5
                basis = "paired_only"
            elif parent:
                parent_probs = (parent_counts + 0.5) / (parent_counts.sum() + 2.0)
                alpha = local_counts + KAPPA * parent_probs
                basis = "partially_pooled" if local else "marginal_backoff"
            else:
                alpha = local_counts + 0.5
                basis = "local_only"
            total = float(alpha.sum())
            probabilities = alpha / total
            correct, wrong = (0, 1) if own == h1 else (1, 0)
            weights = np.zeros(len(LABELS))
            weights[correct], weights[wrong] = 1.0, -2.0
            value = float(probabilities @ weights)
            # This is variance of the estimated mean utility, not realised outcome variance.
            variance = float((probabilities @ (weights ** 2) - value ** 2) / (total + 1.0))
            branches[own] = Branch(
                own, dict(zip(LABELS, probabilities.tolist())), dict(zip(LABELS, alpha.tolist())),
                float(probabilities[correct]), float(probabilities[wrong]), value, variance,
                float(beta.ppf(0.95, alpha[wrong], total - alpha[wrong])),
                local, local_groups, parent, parent_groups, len(local_groups), len(parent_groups), basis, KAPPA)
        return Forecast(branches)
