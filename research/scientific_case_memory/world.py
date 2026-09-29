"""Hypothesis-conditional forecasts served from a case memory.

File summary
- Path: research/scientific_case_memory/world.py
- Purpose: forecast, for each candidate action and each competing hypothesis, how the registered
  validator would read the measurement, using only the cases in a `CaseIndex`. It is the case-memory
  counterpart of `research/belief_planning/world.py::ReferenceWorld` and is an `OutcomeForecaster`
  input for the same planner.
- Core points:
  - Parity. `CaseMemoryWorld` subclasses `ReferenceWorld` and is built from the index alone. With
    `MemoryConfig.extended == False` its forecasts are the reference world's, to floating point; a
    test builds both and compares them. So any difference an extension produces is the extension's.
  - Extensions (`MemoryConfig`), each switchable and each pre-registered:
    - `quality`, `reliability`, `mechanism`, `domain_shift`: which terms of the case score enter the
      multiplier on a precedent's weight (`case_retrieval.PrecedentScorer.modifier`).
    - `unit_out_fit`: fit the structure kernel strength with same-unit analogues excluded, as a
      held-out compound would meet it. The reference world's fit keeps them.
    - `mask_codes`: readings with these codes are not scored anywhere in the memory. Codes 1 and 3
      together are the success-only memory of the ablation; 1 alone removes misleading readings (the
      failure precedents), 3 alone removes undetected readings (the negative precedents).
    - `hypothesis_prior`: the structural neighbourhood gives a prior over the two hypotheses
      (`hypothesis_prior`), fitted by leave-unit-out likelihood. It is advisory (`historical_analogy`)
      and never enters `EvidenceState`.
  - Refusal is a named result. A forecast for which no class reference of either hypothesis was
    measured returns `refusal="insufficient_support"`; `support_report` states per branch the
    number of independent references and their Kish effective number, and flags a branch resting on
    fewer than `MIN_SUPPORT` units, so a caller can decline to use it.
  - Every forecast carries `model_version` and, in `basis`, the fitted strengths and the terms used.
    A forecast is a model prediction by construction; it is never recorded as a measurement.
  - `unit_out_fit` and the extension weights are the only places where this world differs in fitting
    from the reference; `fit_hypothesis_prior` and `_fit_kernel_extended` say exactly how.
- Interfaces: `MemoryConfig`, `CaseMemoryWorld`, `CONFIGS`, `MODEL_VERSION`, `MIN_SUPPORT`
- Depends on: case_index.py, case_retrieval.py, adaptation_model.py, research/belief_planning/world.py
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from maestro.acquisition import OutcomeBranch, OutcomeForecast
from research.belief_planning import world as W

from . import adaptation_model as AM
from . import case_index as CI
from . import case_retrieval as CR

MODEL_VERSION = "case-memory-1"
MIN_SUPPORT = 6
"""Registered `min_reference_units`: a branch resting on fewer independent units is flagged low-support."""
PRIOR_GRID = (0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
"""Pseudo-counts for the neighbourhood prior, fixed before any held-out score."""
PRIOR_BOUND = 0.95
"""No hypothesis prior is allowed to exceed this: a retrieved analogy is advisory and must not make a real
reading unable to overturn it (declared before any held-out score, in the spirit of the contamination mixture)."""
MODIFIER_TERMS = ("mechanism", "quality", "reliability", "domain_shift")


@dataclass(frozen=True)
class MemoryConfig:
    name: str
    structure: bool = True
    terms: tuple[str, ...] = ()
    unit_out_fit: bool = False
    mask_codes: tuple[int, ...] = ()
    hypothesis_prior: bool = False

    @property
    def extended(self) -> bool:
        return bool(self.terms) or self.unit_out_fit or self.hypothesis_prior or bool(self.mask_codes)

    @property
    def uses_modifier(self) -> bool:
        return bool(self.terms)


CONFIGS = {
    "class": MemoryConfig("class", structure=False),
    "similarity": MemoryConfig("similarity"),
    "similarity_unitout": MemoryConfig("similarity_unitout", unit_out_fit=True),
    "cm_full": MemoryConfig("cm_full", terms=MODIFIER_TERMS, unit_out_fit=True),
    "cm_full_prior": MemoryConfig("cm_full_prior", terms=MODIFIER_TERMS, unit_out_fit=True, hypothesis_prior=True),
    "cm_nofail": MemoryConfig("cm_nofail", terms=MODIFIER_TERMS, unit_out_fit=True, mask_codes=CI.FAILURE_CODES),
    "cm_nomisleading": MemoryConfig("cm_nomisleading", terms=MODIFIER_TERMS, unit_out_fit=True, mask_codes=(1,)),
    "cm_nonegative": MemoryConfig("cm_nonegative", terms=MODIFIER_TERMS, unit_out_fit=True, mask_codes=(3,)),
    "cm_quality": MemoryConfig("cm_quality", terms=("quality",), unit_out_fit=True),
    "cm_reliability": MemoryConfig("cm_reliability", terms=("reliability",), unit_out_fit=True),
    "cm_mechanism": MemoryConfig("cm_mechanism", terms=("mechanism",), unit_out_fit=True),
    "cm_domain": MemoryConfig("cm_domain", terms=("domain_shift",), unit_out_fit=True),
    "prior_only": MemoryConfig("prior_only", unit_out_fit=True, hypothesis_prior=True),
}


def _modifier(c, terms) -> np.ndarray:
    """Multiplier in [0, 1] from the enabled terms of the case score (assay and time always count)."""
    positive = 2.0 + sum(t in terms for t in ("mechanism", "quality", "reliability"))
    total = c["assay_compatibility"] + c["temporal_compatibility"]
    if "mechanism" in terms:
        total = total + c["mechanism_compatibility"]
    if "quality" in terms:
        total = total + c["evidence_quality"]
    if "reliability" in terms:
        total = total + c["historical_reliability"]
    if "domain_shift" in terms:
        total = total - c["domain_shift"]
    return np.clip(total / positive, 0.0, 1.0)


class CaseMemoryWorld(W.ReferenceWorld):
    """Reading forecasts for one memory snapshot."""

    def __init__(self, index: CI.CaseIndex, params, training_compounds, *, config: MemoryConfig | None = None,
                 vc: str = "on", feedback: str = "true", hyperparameters=None, context: AM.Context | None = None,
                 adaptation: AM.AdaptationTable | None = None):
        config = config or CONFIGS["similarity"]
        if config.mask_codes:
            index = index.masked(config.mask_codes)
        self.index = index
        self.config = config
        self.ft = None
        self.params = params
        self.vc = "masked" if not config.structure else vc
        self.feedback = feedback
        self.partner = {}
        self.fp, self.pos = index.fp, index.fp_pos
        self.classes = tuple(index.pool)
        self.cidx = dict(index.cidx)
        self.eliminates = bool(params.get("eliminates"))
        training = set(training_compounds)
        self.training = training
        self.keys = {}
        for key in index.keys:
            t = index.tables[key]
            names = list(t.names)
            cat = t.code.copy()
            pooled = np.bincount(cat[cat >= 0], minlength=4).astype(float) + 0.5
            qc_fail = (len(training) - len(set(names) & training) + 0.5) / (len(training) + 1.0) if training else 0.5
            self.keys[key] = {"names": names, "row": dict(t.row), "klass": np.asarray(t.klass, dtype=object),
                              "cat": cat, "pooled": pooled / pooled.sum(), "qc_fail": qc_fail,
                              "fp_rows": np.asarray([self.pos.get(n, -1) for n in names], dtype=int)}
        self._sim, self._cache = {}, {}
        self.scorer = CR.PrecedentScorer(index)
        self.retriever = CR.CaseRetriever(index, adaptation, context)
        self.context = context
        self.adaptation = adaptation
        self._neigh = {}
        self.hyperparameters = dict(hyperparameters) if hyperparameters else self.fit()
        self.prior_strength = self.hyperparameters.get("prior_a")

    # ------------------------------------------------------------------ fitting
    def fit(self) -> dict:
        base = super().fit()
        hp = dict(base)
        if self.config.unit_out_fit or self.config.uses_modifier:
            hp["k"], hp["loglik_k"] = self._fit_kernel_extended(hp["s"])
            hp["k_fit"] = "unit_out_modifier" if self.config.uses_modifier else "unit_out"
        if self.config.hypothesis_prior:
            hp["prior_a"], hp["loglik_prior"] = self.fit_hypothesis_prior()
        return hp

    def _fit_kernel_extended(self, s: float):
        """Choose k by leave-one-unit-out likelihood with the modifier applied to every neighbour.

        For a pseudo-target (a training reference) the neighbours are the class references of other
        independent units. Their reliability is recomputed without the pseudo-target's reading, and
        the neighbourhood terms exclude its own unit, so nothing of the pseudo-target's reading
        reaches its own prediction.
        """
        k_grid = W.GRIDS["k"]
        ll = np.zeros(len(k_grid))
        terms = self.config.terms
        for key, entry in self.keys.items():
            t = self.index.tables[key]
            unit = t.unit
            for h, hi in self.cidx.items():
                for oi in range(len(self.classes)):
                    if oi == hi:
                        continue
                    rows = np.flatnonzero((entry["klass"] == h) & (entry["cat"][:, oi] >= 0))
                    if len(rows) < 2:
                        continue
                    fp, has = self._ref_fps({**entry, "fp_rows": entry["fp_rows"][rows]})
                    sub = np.flatnonzero(has)
                    if len(sub) < 2:
                        continue
                    sim = CR.tanimoto(fp[sub], fp[sub])
                    r_units = unit[rows][sub]
                    base_k = CR.kernel(sim)
                    base_k[r_units[:, None] == r_units[None, :]] = 0.0
                    c = entry["cat"][rows[sub], oi]
                    onehot = np.eye(4)[c]
                    n = len(sub)
                    counts = onehot.sum(0)
                    cls = (counts[None, :] - onehot + s * entry["pooled"][None, :]) / (n - 1.0 + s)
                    mods = self._modifier_matrix(key, h, oi, rows, sub, sim, terms) if terms else np.ones((n, n))
                    b = base_k * mods
                    for j, kk in enumerate(k_grid):
                        w = kk * b
                        pred = (w @ onehot + cls) / (w.sum(1, keepdims=True) + 1.0)
                        ll[j] += float(np.log(np.maximum((pred * onehot).sum(1), 1e-12)).sum())
        best = float(k_grid[int(np.argmax(ll))]) if ll.any() else 0.0
        return best, ll.round(2).tolist()

    def _compound_structures(self):
        """(names, position, unit-masked Tanimoto matrix, class array) over every indexed compound, once."""
        if getattr(self, "_cs", None) is None:
            names = sorted(self.index.cases)
            fp, has = self.scorer.fingerprints(names)
            sim = CR.tanimoto(fp, fp)
            sim = np.where(has[:, None] & has[None, :], sim, 0.0)
            units = np.array([self.index.unit_of.get(n) for n in names], dtype=object)
            sim[units[:, None] == units[None, :]] = 0.0
            klass = np.array([self.index.klass_of.get(n) for n in names], dtype=object)
            self._cs = (names, {n: i for i, n in enumerate(names)}, sim, klass)
        return self._cs

    def _modifier_matrix(self, key, own, oi, rows, sub, sim, terms) -> np.ndarray:
        """Modifier of neighbour j for pseudo-target i (rows: pseudo-targets, columns: neighbours)."""
        n = len(sub)
        t = self.index.tables[key]
        all_rows, neighbour, agree, _, _ = self.scorer._pair_structures(key, own, oi)
        pos_of = {int(r): i for i, r in enumerate(all_rows)}
        pick = np.array([pos_of[int(r)] for r in rows[sub]])
        N = neighbour[np.ix_(pick, pick)]
        A = agree[np.ix_(pick, pick)]
        s0 = self.scorer.base_agreement(key, oi)
        hits = (N & A).sum(1)[None, :] - (N & A).T  # neighbour j's hits without pseudo-target i's contribution
        total = N.sum(1)[None, :] - N.T
        rel = (hits + CR.RELIABILITY_STRENGTH * s0) / (total + CR.RELIABILITY_STRENGTH)
        quality = self.scorer.quality(key, rows[sub])[None, :].repeat(n, 0)
        names_all, by_name, tan, klass = self._compound_structures()
        who = np.array([by_name[t.names[r]] for r in rows[sub]])
        sim_all = tan[who]
        kern = CR.kernel(sim_all)
        other = self.classes[oi]
        m_own, m_other = kern[:, klass == own].sum(1), kern[:, klass == other].sum(1)
        mech = (m_own + 1.0) / (m_own + m_other + 2.0)
        shift = 1.0 - np.minimum(1.0, np.where(klass == own, sim_all, 0.0).max(1))
        c = {"assay_compatibility": np.ones((n, n)), "temporal_compatibility": np.ones((n, n)),
             "mechanism_compatibility": mech[:, None].repeat(n, 1), "evidence_quality": quality,
             "historical_reliability": rel, "domain_shift": shift[:, None].repeat(n, 1)}
        return _modifier(c, terms)

    def fit_hypothesis_prior(self):
        """Choose the neighbourhood pseudo-count by leave-unit-out likelihood of each reference's own class."""
        names, _, sim, klass = self._compound_structures()
        kern = CR.kernel(sim)
        mass = np.stack([kern[:, klass == c].sum(1) for c in self.classes], axis=1)
        member = np.array([self.cidx.get(k, -1) for k in klass])
        ll = np.zeros(len(PRIOR_GRID))
        for i in np.flatnonzero(member >= 0):
            own = member[i]
            other = np.delete(np.arange(len(self.classes)), own)
            for j, a in enumerate(PRIOR_GRID):
                ll[j] += float(np.log((mass[i, own] + a) / (mass[i, own] + mass[i, other] + 2 * a)).sum())
        best = float(PRIOR_GRID[int(np.argmax(ll))])
        return best, ll.round(2).tolist()

    # ------------------------------------------------------------------ new query compounds
    def add_query_compound(self, name: str, smiles: str | None) -> bool:
        """Make a compound that is not in the library queryable by structure; True when a fingerprint was added.

        A user's compound is never a reference: it gains a fingerprint row only, no case and no label.
        """
        if name in self.pos and self.pos[name] >= 0:
            return False
        from rdkit import Chem, RDLogger
        from rdkit.Chem import rdFingerprintGenerator

        RDLogger.DisableLog("rdApp.*")
        mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) and smiles.strip() else None
        if mol is None:
            self.pos[name] = -1
            return False
        width = self.fp.shape[1]
        row = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=width).GetFingerprintAsNumPy(mol).astype(np.float32)
        self.index.fp = np.vstack([self.index.fp, row[None, :]])
        self.pos[name] = len(self.index.fp) - 1
        self.fp = self.index.fp
        self._neigh = {}
        self._cache = {}
        return True

    # ------------------------------------------------------------------ neighbourhood
    def _neighbourhood(self, compound: str, unit: str | None = None):
        key = (compound, unit)
        if key not in self._neigh:
            row = self.pos.get(compound, -1)
            fp = self.fp[row] if (self.fp is not None and row >= 0) else None
            self._neigh[key] = self.scorer.neighbourhood(fp, unit)
        return self._neigh[key]

    def hypothesis_prior(self, compound: str, h1: str, h2: str, unit: str | None = None) -> dict[str, float]:
        """Neighbourhood prior over the two hypotheses; uniform when the target has no structural neighbour."""
        if not self.config.hypothesis_prior:
            return {h1: 0.5, h2: 0.5}
        sim, names = self._neighbourhood(compound, unit)
        kern = CR.kernel(sim)
        klass = np.array([self.index.klass_of.get(n) for n in names], dtype=object)
        a = float(self.prior_strength or PRIOR_GRID[-1])
        m1, m2 = float(kern[klass == h1].sum()), float(kern[klass == h2].sum())
        p1 = min(PRIOR_BOUND, max(1.0 - PRIOR_BOUND, (m1 + a) / (m1 + m2 + 2 * a)))
        return {h1: p1, h2: 1.0 - p1}

    # ------------------------------------------------------------------ forecast
    def forecast(self, key, h1, h2, compound, history=()) -> OutcomeForecast:
        if not self.config.uses_modifier:
            out = super().forecast(key, h1, h2, compound, history)
            return self._stamp(out)
        identifier = W.C.action_id(key)
        if self.feedback == "withheld":
            history = tuple((k, W.NONTERMINAL if lab != W.QC_FAILED else W.QC_FAILED) for k, lab in history)
        cache_key = (key, h1, h2, compound, tuple(history))
        if cache_key in self._cache:
            return self._cache[cache_key]
        entry = self.keys.get(key)
        if entry is None or h1 not in self.cidx or h2 not in self.cidx:
            out = OutcomeForecast(identifier, refusal="condition_or_hypothesis_not_in_reference_library",
                                  basis="case_memory.world", model_version=MODEL_VERSION)
            self._cache[cache_key] = out
            return out
        hp = self.hyperparameters
        k_scale = 0.0 if self.vc == "masked" else hp["k"]
        query = CR.RetrievalQuery(compound, key, (h1, h2), self.context or AM.Context("", ""),
                                  self.fp[self.pos[compound]] if (self.fp is not None and compound in self.pos and
                                                                  self.pos[compound] >= 0) else None)
        sim_cache = self._neighbourhood(compound) if k_scale > 0 else None
        branches, notes = [], []
        for own, other, match_own, match_other in ((h1, h2, W.MATCH_H1, W.MATCH_H2), (h2, h1, W.MATCH_H2, W.MATCH_H1)):
            oi = self.cidx[other]
            rows = np.flatnonzero(entry["klass"] == own)
            c = entry["cat"][rows, oi]
            ok = c >= 0
            rows, c = rows[ok], c[ok]
            names = [entry["names"][r] for r in rows]
            onehot = np.eye(4)[c] if len(c) else np.zeros((0, 4))
            hist = self._history_weights(rows, names, oi, history) if len(rows) else np.zeros(0)
            probs = (hist @ onehot + hp["s"] * entry["pooled"]) / (hist.sum() + hp["s"])
            basis = "class"
            if k_scale > 0:
                basis = "vc_abstained"
                if sim_cache is not None and len(rows):
                    comps = self.scorer.components(query, own, other, self.context or AM.Context("", ""),
                                                   self.adaptation, sim_cache)
                    kern = CR.kernel(comps["similarity"]) * _modifier(comps, self.config.terms) * hist * k_scale
                    if kern.sum() > 0:
                        probs = (kern @ onehot + probs) / (kern.sum() + 1.0)
                        basis = "vc"
            qc = entry["qc_fail"]
            dist = {lab: float((1.0 - qc) * p) for lab, p in zip((match_own, match_other, W.UNRESOLVED, W.ABSENT), probs)}
            dist[W.QC_FAILED] = float(qc)
            branches.append(OutcomeBranch(own, dist, int(round(float(hist.sum()))) if len(rows) else 0))
            notes.append(basis)
        out = OutcomeForecast(identifier, tuple(branches),
                              basis=(f"case_memory[{self.config.name}:s={hp['s']:g},k={k_scale:g},e={hp['e']:g},"
                                     f"terms={'+'.join(self.config.terms)}]:" + "/".join(notes)),
                              model_version=MODEL_VERSION)
        self._cache[cache_key] = out
        return out

    def _stamp(self, forecast: OutcomeForecast) -> OutcomeForecast:
        if forecast.model_version == MODEL_VERSION:
            return forecast
        return OutcomeForecast(forecast.action_identifier, forecast.branches,
                               basis=forecast.basis.replace("belief_planning.world", f"case_memory[{self.config.name}]"),
                               refusal=forecast.refusal, model_version=MODEL_VERSION)

    # ------------------------------------------------------------------ support
    def support_report(self, key, h1, h2, compound) -> dict:
        """Per hypothesis: independent references, Kish effective number, and whether it is low-support."""
        entry = self.keys.get(key)
        if entry is None:
            return {}
        out = {}
        sim = self._neighbourhood(compound) if self.vc != "masked" else None
        for own, other in ((h1, h2), (h2, h1)):
            oi = self.cidx[other]
            rows = np.flatnonzero((entry["klass"] == own) & (entry["cat"][:, oi] >= 0))
            units = {self.index.unit_of.get(entry["names"][r], entry["names"][r]) for r in rows}
            neighbours = 0.0
            if sim is not None:
                s_all, names = sim
                by = {n: i for i, n in enumerate(names)}
                k = CR.kernel(np.array([s_all[by[entry["names"][r]]] for r in rows])) if len(rows) else np.zeros(0)
                neighbours = float(k.sum() ** 2 / (k ** 2).sum()) if (k ** 2).sum() > 0 else 0.0
            out[own] = {"independent_units": len(units), "low_support": len(units) < MIN_SUPPORT,
                        "precedents_in_domain": neighbours}
        return out
