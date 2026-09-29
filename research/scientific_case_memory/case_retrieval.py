"""Adaptive, adaptation-aware retrieval of precedent cases, with the reasons for every case returned.

File summary
- Path: research/scientific_case_memory/case_retrieval.py
- Purpose: retrieve precedents for one forecast (a target compound, a condition, a pair of competing
  hypotheses) in four stages, and return not only the cases but why each was retrieved, what matches,
  what differs, how it would have to be adapted and how uncertain that makes it.
- Core points:
  - Stage 1, hard compatibility (`CaseIndex.eligible`): incompatible assay, measurement type, unit,
    time or dose scale, control design, quality or intervention type removes a case, with a named
    reason, before any score exists.
  - Stage 2, mechanism: a precedent of class h supports hypothesis h. `mechanism_compatibility` is the
    share of the target's structural-neighbourhood mass that lies in class h against the competing
    class, shrunk with one pseudo-count each: the neighbourhood is the contrast evidence, so a target
    whose nearest analogues belong to the other class lowers the weight of class-h precedents.
  - Stage 3, state: `state_similarity` is the structure kernel `clip((Tanimoto - floor) / (1 - floor))`
    above the registered floor; a precedent below the floor is not a precedent for this target.
  - Stage 4, adaptation-aware rerank. The score follows the design specification,
        case_score = state_similarity + mechanism_compatibility + assay_compatibility
                     + temporal_compatibility + evidence_quality + historical_reliability
                     - adaptation_cost - domain_shift - measurement_mismatch,
    with every term in [0, 1]. `evidence_quality` is the replicate agreement of the reading,
    `historical_reliability` the local predictive record of the precedent (how often its reading
    equalled that of its structural neighbours of the same class and another unit, shrunk to the
    condition's base rate), `adaptation_cost` comes from `adaptation_model.AdaptationTable`,
    `domain_shift` is one minus the target's best similarity to any precedent of the hypothesis class.
  - Weighting in the forecast. The probability model multiplies: `weight = k * history * state_similarity
    * modifier`, where `modifier = clip((score - state_similarity) / 5, 0, 1)` is every other term of the
    score. Ranking uses the additive score; the forecast uses the product, so a precedent that is
    structurally distant is never rescued by a good record.
  - Several precedents are always used: the forecast weights all of them; `retrieve` returns the top
    `top_k` for explanation and reports the effective number of independent precedents (Kish).
- Interfaces: `PrecedentScorer`, `CaseRetriever`, `RetrievalQuery`, `RetrievedCase`, `SCORE_TERMS`
- Depends on: case_index.py, adaptation_model.py, numpy, research/belief_planning/world.py (floor, kernel)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from . import adaptation_model as AM
from . import case_index as CI

SIM_FLOOR = 0.40
"""Registered structural applicability floor (belief_planning.world.SIM_FLOOR); duplicated by value and tested equal."""
SCORE_TERMS = ("state_similarity", "mechanism_compatibility", "assay_compatibility", "temporal_compatibility",
               "evidence_quality", "historical_reliability", "adaptation_cost", "domain_shift",
               "measurement_mismatch")
RELIABILITY_STRENGTH = 2.0
"""Pseudo-count that shrinks a precedent's local record to the condition's base agreement rate."""


def kernel(sim: np.ndarray) -> np.ndarray:
    return np.clip((np.asarray(sim, dtype=float) - SIM_FLOOR) / (1.0 - SIM_FLOOR), 0.0, None)


def tanimoto(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    inter = a @ b.T
    union = a.sum(1)[:, None] + b.sum(1)[None, :] - inter
    return np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)


@dataclass(frozen=True)
class RetrievalQuery:
    compound: str
    key: tuple
    hypotheses: tuple[str, str]
    context: AM.Context
    fingerprint: np.ndarray | None = None
    unit: str | None = None
    problem: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedCase:
    case_id: str
    hypothesis: str
    score: float
    components: Mapping[str, float]
    reading: str
    reading_kind: str
    matches: tuple[str, ...]
    differences: Mapping[str, object]
    adaptation: Mapping[str, object]
    why: str


class PrecedentScorer:
    """The nine terms of the case score for the references of one class at one condition."""

    def __init__(self, index: CI.CaseIndex):
        self.index = index
        self._rel: dict = {}
        self._base: dict = {}
        self._fp_ok = None

    # ------------------------------------------------------------------ fingerprints
    def fingerprints(self, names: Sequence[str]) -> tuple[np.ndarray, np.ndarray]:
        """(rows, has) for `names`; a compound without a usable structure has has=False and zero rows."""
        idx = self.index
        rows = np.array([idx.fp_pos.get(n, -1) for n in names], dtype=int)
        if idx.fp is None:
            return np.zeros((len(names), 1)), np.zeros(len(names), dtype=bool)
        fp = np.where((rows >= 0)[:, None], idx.fp[np.maximum(rows, 0)], 0.0)
        return fp, (rows >= 0) & fp.any(axis=1)

    # ------------------------------------------------------------------ reliability
    def _pair_structures(self, key: tuple, klass: str, oi: int):
        cache_key = (key, klass, oi)
        if cache_key in self._rel:
            return self._rel[cache_key]
        t = self.index.tables[key]
        rows = np.flatnonzero((t.klass == klass) & (t.code[:, oi] >= 0))
        names = [t.names[r] for r in rows]
        fp, has = self.fingerprints(names)
        unit = t.unit[rows]
        code = t.code[rows, oi]
        if len(rows) == 0:
            out = (rows, np.zeros((0, 0), bool), np.zeros((0, 0), bool), has, code)
        else:
            sim = tanimoto(fp, fp) if has.any() else np.zeros((len(rows), len(rows)))
            neighbour = (sim >= SIM_FLOOR) & has[:, None] & has[None, :] & (unit[:, None] != unit[None, :])
            agree = code[:, None] == code[None, :]
            out = (rows, neighbour, agree, has, code)
        self._rel[cache_key] = out
        return out

    def base_agreement(self, key: tuple, oi: int) -> float:
        """Mean same-code rate among structural neighbours of the same class at a condition, for shrinkage."""
        if (key, oi) in self._base:
            return self._base[(key, oi)]
        num = den = 0.0
        for klass in self.index.pool:
            rows, neighbour, agree, _, _ = self._pair_structures(key, klass, oi)
            if len(rows):
                num += float((neighbour & agree).sum())
                den += float(neighbour.sum())
        value = num / den if den else 0.5
        self._base[(key, oi)] = value
        return value

    def reliability(self, key: tuple, klass: str, oi: int, exclude: np.ndarray | None = None) -> np.ndarray:
        """Local predictive record of each class reference: neighbours' agreement with its reading.

        `exclude` (positions within the class rows) removes those neighbours from every record, which is
        what leave-one-out fitting needs so a pseudo-target's own reading never raises its neighbours'
        record.
        """
        rows, neighbour, agree, _, _ = self._pair_structures(key, klass, oi)
        s0 = self.base_agreement(key, oi)
        if len(rows) == 0:
            return np.zeros(0)
        N = neighbour.copy()
        if exclude is not None:
            N[:, exclude] = False
        hits = (N & agree).sum(1)
        total = N.sum(1)
        return (hits + RELIABILITY_STRENGTH * s0) / (total + RELIABILITY_STRENGTH)

    # ------------------------------------------------------------------ components
    def quality(self, key: tuple, rows: np.ndarray) -> np.ndarray:
        agreement = self.index.tables[key].agreement[rows]
        return np.where(np.isfinite(agreement), np.clip(agreement, 0.0, 1.0), 0.5)

    def neighbourhood(self, target_fp: np.ndarray | None, exclude_unit: str | None) -> tuple[np.ndarray, list[str]]:
        """Compound-level structure kernel of the target against every indexed compound."""
        names = sorted(self.index.cases)
        if target_fp is None or not np.any(target_fp):
            return np.zeros(len(names)), names
        fp, has = self.fingerprints(names)
        sim = tanimoto(np.asarray(target_fp, dtype=float)[None, :], fp)[0]
        sim = np.where(has, sim, 0.0)
        if exclude_unit is not None:
            same = np.array([self.index.unit_of.get(n) == exclude_unit for n in names])
            sim = np.where(same, 0.0, sim)
        return sim, names

    def mechanism_compatibility(self, sim: np.ndarray, names: Sequence[str], own: str, other: str) -> float:
        """Share of neighbourhood kernel mass in `own` against `other`, one pseudo-count each side."""
        k = kernel(sim)
        klass = np.array([self.index.klass_of.get(n) for n in names], dtype=object)
        m_own, m_other = float(k[klass == own].sum()), float(k[klass == other].sum())
        return (m_own + 1.0) / (m_own + m_other + 2.0)

    def domain_shift(self, sim: np.ndarray, names: Sequence[str], own: str) -> float:
        klass = np.array([self.index.klass_of.get(n) for n in names], dtype=object)
        best = float(sim[klass == own].max()) if (klass == own).any() else 0.0
        return 1.0 - min(1.0, best)

    def components(self, query: RetrievalQuery, own: str, other: str, table_context: AM.Context,
                   adaptation: AM.AdaptationTable | None = None, sim_cache=None) -> dict[str, np.ndarray]:
        """Score terms for every class-`own` reference with a scored reading at `query.key` against `other`."""
        idx = self.index
        t = idx.tables[query.key]
        oi = idx.cidx[other]
        rows = np.flatnonzero((t.klass == own) & (t.code[:, oi] >= 0))
        n = len(rows)
        names = [t.names[r] for r in rows]
        fp, has = self.fingerprints(names)
        sim_all, all_names = sim_cache if sim_cache is not None else self.neighbourhood(query.fingerprint, query.unit)
        by_name = {nm: i for i, nm in enumerate(all_names)}
        sim = np.array([sim_all[by_name[nm]] if nm in by_name else 0.0 for nm in names]) if n else np.zeros(0)
        if query.unit is not None and n:
            sim = np.where(t.unit[rows] == query.unit, 0.0, sim)
        state = kernel(sim)
        mech = self.mechanism_compatibility(sim_all, all_names, own, other)
        shift = self.domain_shift(sim_all, all_names, own)
        rel_rows, _, _, _, _ = self._pair_structures(query.key, own, oi)
        reliability = self.reliability(query.key, own, oi)
        # `_pair_structures` rows equal `rows` because both filter the same table the same way
        cost = 0.0
        if adaptation is not None:
            cost = adaptation.cost(AM.differences(table_context, query.context)).cost
        return {"rows": rows, "names": names, "state_similarity": state,
                "mechanism_compatibility": np.full(n, mech), "assay_compatibility": np.ones(n),
                "temporal_compatibility": np.ones(n), "evidence_quality": self.quality(query.key, rows),
                "historical_reliability": reliability if len(reliability) == n else np.full(n, 0.5),
                "adaptation_cost": np.full(n, cost), "domain_shift": np.full(n, shift),
                "measurement_mismatch": np.zeros(n), "similarity": sim}

    @staticmethod
    def case_score(c: Mapping[str, np.ndarray]) -> np.ndarray:
        """The additive score of the design specification."""
        return (c["state_similarity"] + c["mechanism_compatibility"] + c["assay_compatibility"]
                + c["temporal_compatibility"] + c["evidence_quality"] + c["historical_reliability"]
                - c["adaptation_cost"] - c["domain_shift"] - c["measurement_mismatch"])

    @staticmethod
    def modifier(c: Mapping[str, np.ndarray]) -> np.ndarray:
        """Every term of the score except state similarity, scaled to [0, 1]: the multiplier in the forecast."""
        other = PrecedentScorer.case_score(c) - c["state_similarity"]
        return np.clip(other / 5.0, 0.0, 1.0)


class CaseRetriever:
    """Four-stage retrieval with explanations."""

    def __init__(self, index: CI.CaseIndex, adaptation: AM.AdaptationTable | None = None,
                 table_context: AM.Context | None = None):
        self.index = index
        self.scorer = PrecedentScorer(index)
        self.adaptation = adaptation or AM.AdaptationTable()
        self.table_context = table_context

    def retrieve(self, query: RetrievalQuery, top_k: int = 5) -> dict:
        """Precedents for `query` under each of its two hypotheses.

        Returns a dictionary with the eligible/excluded counts of stage 1 and, per hypothesis, the top
        `top_k` cases, the Kish effective number of independent precedents and a plain statement of
        whether the neighbourhood supports enough precedents to be used at all.
        """
        eligible, dropped = self.index.eligible(dict(query.problem))
        eligible_set = set(eligible)
        ctx = self.table_context or query.context
        sim_cache = self.scorer.neighbourhood(query.fingerprint, query.unit)
        out: dict = {"stage1": {"eligible": len(eligible), "excluded": len(dropped),
                                "reasons": _count(dropped.values())}, "hypotheses": {}}
        h1, h2 = query.hypotheses
        for own, other in ((h1, h2), (h2, h1)):
            c = self.scorer.components(query, own, other, ctx, self.adaptation, sim_cache)
            keep = np.array([nm in eligible_set for nm in c["names"]], dtype=bool)
            if not keep.any():
                out["hypotheses"][own] = {"cases": [], "kish": 0.0, "usable": False,
                                          "reason": "no_eligible_precedent_after_stage1"}
                continue
            score = self.scorer.case_score(c)
            gated = np.where((c["state_similarity"] > 0) & keep, score, -np.inf)
            order = np.argsort(-gated)
            weights = np.where(np.isfinite(gated), c["state_similarity"] * self.scorer.modifier(c), 0.0)
            kish = float(weights.sum() ** 2 / (weights ** 2).sum()) if (weights ** 2).sum() > 0 else 0.0
            cases = []
            t = self.index.tables[query.key]
            oi = self.index.cidx[other]
            for i in order[:top_k]:
                if not np.isfinite(gated[i]):
                    break
                cases.append(self._explain(query, c, int(i), own, other, t, oi, ctx))
            out["hypotheses"][own] = {"cases": cases, "kish": kish, "usable": bool(kish >= 2.0),
                                      "reason": None if kish >= 2.0 else "fewer_than_two_effective_precedents"}
        return out

    def _explain(self, query: RetrievalQuery, c: Mapping, i: int, own: str, other: str, t, oi: int,
                 ctx: AM.Context) -> RetrievedCase:
        components = {k: float(c[k][i]) for k in SCORE_TERMS}
        name = c["names"][i]
        case = self.index.cases[name]
        code = int(t.code[c["rows"][i], oi])
        diff = AM.differences(ctx, query.context)
        priced = self.adaptation.cost(diff)
        matches = tuple(sorted(k for k, v in {"assay": not diff["assay"], "dataset": not diff["dataset"],
                                              "cell_line": diff["cell_line"] is False,
                                              "time": diff["time"] == "same", "dose": diff["dose"] == "same"}.items() if v))
        differing = {k: v for k, v in diff.items() if v not in (False, "same", None)}
        why = (f"class {own}, structural similarity {float(c['similarity'][i]):.2f} "
               f"(kernel {components['state_similarity']:.2f}); read as {CI.LABEL_OF_CODE.get(code, 'not_scored')} "
               f"against {other}; neighbourhood supports {own} at {components['mechanism_compatibility']:.2f}")
        return RetrievedCase(name, own, float(self.scorer.case_score(c)[i]), components,
                             CI.LABEL_OF_CODE.get(code, "not_scored"), CI.KIND_OF_CODE[code].value if code in CI.KIND_OF_CODE
                             else "not_scored", matches, differing,
                             {"operations": AM.operations_for(diff), "cost": priced.cost, "supported": priced.supported,
                              "trials": priced.trials, "uncertainty": priced.uncertainty, "basis": priced.reason}, why)


def _count(items) -> dict:
    out: dict = {}
    for item in items:
        head = str(item).split(":")[0]
        out[head] = out.get(head, 0) + 1
    return out
