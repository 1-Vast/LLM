"""The world model the planner consults: per-hypothesis reading distributions for each measurement.

File summary
- Path: research/belief_planning/world.py
- Purpose: for a (compound, contrast, measurement, observed history), forecast how the registered
  validator would read the measurement under each hypothesis. The forecast is an
  `maestro.acquisition.OutcomeForecast`, so the agent's planner (`maestro.planning`) consumes it
  like any other forecaster.
- Core points:
  - References. Under hypothesis h, the references are training compounds annotated h that were
    measured at the condition. Each carries its own validator reading against the other
    hypothesis, with its whole unit left out (`group_out_outcomes`). Only training folds enter;
    a sealed context has no held-out rows to offer.
  - Three layers, each shrunk to the next:
    - `pooled`: every pool reference's readings at the condition.
    - `class`: the hypothesis's references, shrunk to pooled with strength `s`.
    - `vc`: the same references weighted by the virtual cell's structural kernel (Tanimoto above
      `SIM_FLOOR`, scaled by `k`), shrunk to class with unit strength. It asks how compounds that
      resemble this one read when they belong to h.
    Thin support backs off to the layer below. It never refuses, and missing support never
    reads as zero value.
  - Feedback. A real reading already observed reweights each reference by whether its own reading
    at that condition was the same: matching references keep weight 1, mismatched ones `e`, and
    unmeasured ones the pooled frequency of the observed reading. The next forecast is therefore
    conditioned on what this compound actually did. A QC failure conditions nothing.
  - Empirical Bayes, not tuning. `s`, `k` and `e` are chosen per fold, over the fixed grids below,
    by leave-one-out predictive log-likelihood of the training references' own readings. If
    structural neighbours do not predict references' readings, `k` is 0 and the virtual cell
    abstains everywhere. Fitted values are in every forecast basis and in `hyperparameters`.
  - A factorised variant, which pooled detection across classes, was tried on SciPlex3 in
    development and was worse (B 0.558 and A 0.464 correct, against 0.590 and 0.506 here). It is
    not used. (log/20260927/0927/run-notes.md)
  - Applicability domain. The kernel is zero below `SIM_FLOOR`. A compound with no reference
    inside the domain gets the class layer, recorded as `vc_abstained`.
  - Controls:
    - `vc="masked"` removes the kernel.
    - `vc="permuted"` uses another held-out compound's similarities.
    - `feedback="withheld"` conditions only on "the reading did not end the episode". The arm
      substitutes readings for `feedback="permuted"`.
- Interfaces: `LABELS`, `ReferenceWorld`, `label_of`, `group_out_outcomes`, `GRIDS`
- Depends on: research/dynamic_world_model/common.py (fold tables, validator rule), maestro.acquisition
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dynamic_world_model"))
import common as C  # noqa: E402

from maestro.acquisition import OutcomeBranch, OutcomeForecast  # noqa: E402

MATCH_H1, MATCH_H2 = "profile_matches_h1", "profile_matches_h2"
UNRESOLVED, ABSENT, QC_FAILED = "profile_unresolved", "no_detectable_response", "quality_failed"
LABELS = (MATCH_H1, MATCH_H2, UNRESOLVED, ABSENT, QC_FAILED)
NONTERMINAL = "nonterminal_unobserved"
"""The label an arm records when feedback is withheld: a measurement ran and removed nothing."""

CODE = {"eliminate_b": 0, "eliminate_a": 1, "ambiguous": 2, "undetected": 3}
OBSERVED = {"eliminate_b": MATCH_H1, "eliminate_a": MATCH_H2, "ambiguous": UNRESOLVED,
            "undetected": ABSENT, "quality_failed": QC_FAILED}
LABEL_CODE = {UNRESOLVED: 2, ABSENT: 3}

SIM_FLOOR = 0.40
GRIDS = {"s": (1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0),
         "k": (0.0, 1.0, 2.0, 4.0, 8.0, 16.0),
         "e": (0.01, 0.03, 0.1, 0.3, 1.0)}
"""Fixed before any held-out reading was scored; each fold picks by training LOO likelihood."""


def label_of(outcome: str) -> str:
    """The registered reading label of a runner outcome (`eliminate_b` = profile matches H1)."""
    return OBSERVED[outcome]


def group_out_outcomes(ft, key, floor, margin, group_of) -> dict:
    """`common.loo_outcomes` with each reference's whole unit (skeleton or component) left out.

    A held-out compound is read against templates that contain none of its analogs, because
    folds are dealt by unit. A training reference read by single-compound LOO still sees its
    analogs. Leaving the unit out reproduces the held-out situation. It is the same Gram algebra as
    `common._loo_class_scores`, with the shared axis and the templates both recomputed without
    the unit. On the development tiers it moves pooled rates by under 0.005, because most units
    are single compounds, but it is the right counterfactual.
    """
    t = ft.tables[key]
    classes = tuple(ft.classes)
    n = len(t.names)
    out = {}
    if n < 2:
        return out
    groups: dict = {}
    for i, name in enumerate(t.names):
        groups.setdefault(group_of.get(name, name), []).append(i)
    diag = np.diag(t.G)
    member = {k: (t.klass == k) & t.detected for k in classes}
    for members in groups.values():
        X = np.asarray(members)
        keep = np.ones(n, bool)
        keep[X] = False
        d = t.s - t.G[:, X].sum(1)
        norm2 = t.total - 2.0 * t.s[X].sum() + t.G[np.ix_(X, X)].sum()
        if norm2 <= 1e-12:
            continue
        perp = np.sqrt(np.maximum(diag - d * d / norm2, 1e-12))
        measured = np.array([int(((t.klass == k) & keep).sum()) for k in classes])
        templates = np.array([int(((t.klass == k) & keep & t.detected).sum()) for k in classes])
        masks = [member[k] & keep for k in classes]
        for c in X:
            if t.klass[c] not in classes:
                continue
            row = (t.G[c] - d[c] * d / norm2) / (perp[c] * perp)
            scores = np.array([row[m].max() if m.any() else -np.inf for m in masks])
            a = classes.index(t.klass[c])
            for b in range(len(classes)):
                if b != a:
                    out[(t.names[c], classes[b])] = C.decide(bool(t.detected[c]), scores, a, b, measured, templates,
                                                             floor, margin)
    return out


def _tanimoto_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    inter = a @ b.T
    union = a.sum(1)[:, None] + b.sum(1)[None, :] - inter
    return np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)


def _kernel(sim, scale):
    return scale * np.clip((sim - SIM_FLOOR) / (1.0 - SIM_FLOOR), 0.0, None)


class ReferenceWorld:
    """Reading forecasts for one fold (or one external reference library)."""

    def __init__(self, ft, params, training_compounds, *, fingerprints=None, positions=None,
                 vc: str = "on", feedback: str = "true", partner=None, hyperparameters=None, groups=None):
        if vc not in ("on", "masked", "permuted"):
            raise ValueError(vc)
        if feedback not in ("true", "withheld", "permuted"):
            raise ValueError(feedback)
        self.ft, self.params, self.vc, self.feedback = ft, params, vc, feedback
        self.partner = partner or {}
        self.fp, self.pos = fingerprints, positions or {}
        self.classes = tuple(ft.classes)
        self.cidx = {k: i for i, k in enumerate(self.classes)}
        self.eliminates = bool(params.get("eliminates"))
        training = set(training_compounds)
        self.keys = {}
        for key, table in ft.tables.items():
            names = list(table.names)
            row = {n: i for i, n in enumerate(names)}
            # cat[r, o]: reference r's reading against pool class o (code 0-3), -1 when not scored
            cat = np.full((len(names), len(self.classes)), -1, dtype=int)
            if self.eliminates:
                if groups is not None:
                    readings = group_out_outcomes(ft, key, params["floor"], params["margin"], groups)
                else:
                    readings = C.loo_outcomes(ft, key, params["floor"], params["margin"])
                for (n, o), v in readings.items():
                    cat[row[n], self.cidx[o]] = CODE[v]
            else:
                det = np.asarray(table.detected, dtype=bool)
                cat[:] = np.where(det, 2, 3)[:, None]
            pooled = np.bincount(cat[cat >= 0], minlength=4).astype(float) + 0.5
            qc_fail = (len(training) - len(set(names) & training) + 0.5) / (len(training) + 1.0) if training else 0.5
            self.keys[key] = {"names": names, "row": row, "klass": np.asarray(table.klass, dtype=object),
                              "cat": cat, "pooled": pooled / pooled.sum(), "qc_fail": qc_fail,
                              "fp_rows": np.asarray([self.pos.get(n, -1) for n in names], dtype=int)}
        self._sim = {}
        self._cache = {}
        self.hyperparameters = dict(hyperparameters) if hyperparameters else self.fit()

    # -------------------------------------------------------------------- empirical Bayes
    def _ref_fps(self, entry):
        rows = entry["fp_rows"]
        if self.fp is None:
            return None, rows >= 0
        fp = np.where((rows >= 0)[:, None], self.fp[np.maximum(rows, 0)], 0.0)
        return fp, (rows >= 0) & fp.any(axis=1)

    def fit(self) -> dict:
        """Choose s, k and e by leave-one-out predictive log-likelihood of training references."""
        s_grid, k_grid, e_grid = GRIDS["s"], GRIDS["k"], GRIDS["e"]
        ll_s = np.zeros(len(s_grid))
        groups = []
        for key, entry in self.keys.items():
            cat, klass, pooled = entry["cat"], entry["klass"], entry["pooled"]
            for h, hi in self.cidx.items():
                rows = np.flatnonzero(klass == h)
                if len(rows) < 2:
                    continue
                groups.append((key, hi, rows))
                for oi in range(len(self.classes)):
                    if oi == hi:
                        continue
                    c = cat[rows, oi]
                    c = c[c >= 0]
                    if len(c) < 2:
                        continue
                    counts = np.bincount(c, minlength=4).astype(float)
                    for j, s in enumerate(s_grid):
                        pred = (counts - 1.0 + s * pooled) / (len(c) - 1.0 + s)
                        ll_s[j] += float((counts * np.log(np.maximum(pred, 1e-12))).sum())
        s = float(s_grid[int(np.argmax(ll_s))]) if ll_s.any() else s_grid[0]
        # kernel scale: predict each reference from structurally similar references of its class
        ll_k = np.zeros(len(k_grid))
        kernel_pairs = 0
        for key, hi, rows in groups:
            entry = self.keys[key]
            fp, has = self._ref_fps(entry)
            if fp is None:
                continue
            sub = rows[has[rows]]
            if len(sub) < 2:
                continue
            sim = _tanimoto_matrix(fp[sub], fp[sub])
            np.fill_diagonal(sim, 0.0)
            base = _kernel(sim, 1.0)
            kernel_pairs += int((base > 0).sum())
            cat, pooled = entry["cat"], entry["pooled"]
            for oi in range(len(self.classes)):
                if oi == hi:
                    continue
                c = cat[sub, oi]
                ok = c >= 0
                if ok.sum() < 2:
                    continue
                onehot = np.eye(4)[c[ok]]
                counts = onehot.sum(0)
                n = ok.sum()
                cls = (counts[None, :] - onehot + s * pooled[None, :]) / (n - 1.0 + s)
                b = base[np.ix_(ok, ok)]
                for j, k in enumerate(k_grid):
                    w = k * b
                    pred = (w @ onehot + cls) / (w.sum(1, keepdims=True) + 1.0)
                    ll_k[j] += float(np.log(np.maximum((pred * onehot).sum(1), 1e-12)).sum())
        k = float(k_grid[int(np.argmax(ll_k))]) if ll_k.any() else 0.0
        # feedback mismatch weight: a reference's reading at one condition given its reading at another
        ll_e = np.zeros(len(e_grid))
        for key, entry in self.keys.items():
            for prior_key, other in self.keys.items():
                if prior_key == key:
                    continue
                for h, hi in self.cidx.items():
                    rows = np.flatnonzero(entry["klass"] == h)
                    if len(rows) < 3:
                        continue
                    prow = np.asarray([other["row"].get(entry["names"][r], -1) for r in rows])
                    for oi in range(len(self.classes)):
                        if oi == hi:
                            continue
                        c = entry["cat"][rows, oi]
                        pc = np.where(prow >= 0, other["cat"][np.maximum(prow, 0), oi], -1)
                        # condition only on references whose earlier reading was non-eliminating (a real history)
                        targets = np.flatnonzero((c >= 0) & ((pc == 2) | (pc == 3)))
                        if len(targets) == 0 or (c >= 0).sum() < 2:
                            continue
                        onehot = np.where((c >= 0)[:, None], np.eye(4)[np.maximum(c, 0)], 0.0)
                        observed = pc[targets][:, None]
                        unmeasured = np.broadcast_to(other["pooled"][pc[targets]][:, None], (len(targets), len(c)))
                        same = pc[None, :] == observed
                        known = (pc >= 0)[None, :]
                        valid = np.repeat((c >= 0)[None, :].astype(float), len(targets), axis=0)
                        valid[np.arange(len(targets)), targets] = 0.0
                        for j, e in enumerate(e_grid):
                            w = np.where(known, np.where(same, 1.0, e), unmeasured) * valid
                            pred = (w @ onehot + s * entry["pooled"][None, :]) / (w.sum(1, keepdims=True) + s)
                            ll_e[j] += float(np.log(np.maximum(pred[np.arange(len(targets)), c[targets]], 1e-12)).sum())
        e = float(e_grid[int(np.argmax(ll_e))]) if ll_e.any() else 1.0
        return {"s": s, "k": k, "e": e, "loglik_s": ll_s.round(2).tolist(), "loglik_k": ll_k.round(2).tolist(),
                "loglik_e": ll_e.round(2).tolist(), "kernel_pairs": kernel_pairs, "sim_floor": SIM_FLOOR}

    # -------------------------------------------------------------------- pieces
    def similarity(self, compound, entry):
        """Tanimoto similarity of `compound` (or its permuted partner) to the references of `entry`."""
        query = self.partner.get(compound, compound) if self.vc == "permuted" else compound
        row = self.pos.get(query, -1)
        if self.fp is None or row < 0 or not self.fp[row].any():
            return None
        if query not in self._sim:
            x = self.fp[row]
            inter = self.fp @ x
            union = self.fp.sum(1) + x.sum() - inter
            self._sim[query] = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
        rows = entry["fp_rows"]
        return np.where(rows >= 0, self._sim[query][np.maximum(rows, 0)], 0.0)

    def _history_weights(self, rows, names, oi, history):
        w = np.ones(len(rows))
        e = self.hyperparameters["e"]
        for action_key, label in history:
            if label == QC_FAILED or action_key not in self.keys:
                continue
            other = self.keys[action_key]
            allowed = (2, 3) if label == NONTERMINAL else (LABEL_CODE[label],)
            base = sum(other["pooled"][a] for a in allowed)
            prow = np.asarray([other["row"].get(n, -1) for n in names])
            pc = np.where(prow >= 0, other["cat"][np.maximum(prow, 0), oi], -1)
            w *= np.where(pc < 0, base, np.where(np.isin(pc, allowed), 1.0, e))
        return w

    # -------------------------------------------------------------------- forecast
    def forecast(self, key, h1, h2, compound, history=()) -> OutcomeForecast:
        """Per-hypothesis label distribution for measuring `key`, given real `history` ((key, label), ...)."""
        identifier = C.action_id(key)
        if self.feedback == "withheld":
            history = tuple((k, NONTERMINAL if lab != QC_FAILED else QC_FAILED) for k, lab in history)
        cache_key = (key, h1, h2, compound, tuple(history))
        if cache_key in self._cache:
            return self._cache[cache_key]
        entry = self.keys.get(key)
        if entry is None or h1 not in self.cidx or h2 not in self.cidx:
            out = OutcomeForecast(identifier, refusal="condition_or_hypothesis_not_in_reference_library",
                                  basis="belief_planning.world")
            self._cache[cache_key] = out
            return out
        hp = self.hyperparameters
        k_scale = 0.0 if self.vc == "masked" else hp["k"]
        sim = self.similarity(compound, entry) if k_scale > 0 else None
        branches, notes = [], []
        for own, other, match_own, match_other in ((h1, h2, MATCH_H1, MATCH_H2), (h2, h1, MATCH_H2, MATCH_H1)):
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
                if sim is not None and len(rows):
                    kernel = _kernel(sim[rows], k_scale) * hist
                    if kernel.sum() > 0:
                        probs = (kernel @ onehot + probs) / (kernel.sum() + 1.0)
                        basis = "vc"
            qc = entry["qc_fail"]
            dist = {lab: float((1.0 - qc) * p) for lab, p in zip((match_own, match_other, UNRESOLVED, ABSENT), probs)}
            dist[QC_FAILED] = float(qc)
            branches.append(OutcomeBranch(own, dist, int(round(float(hist.sum()))) if len(rows) else 0))
            notes.append(basis)
        out = OutcomeForecast(identifier, tuple(branches),
                              basis=f"belief_planning.world[s={hp['s']:g},k={k_scale:g},e={hp['e']:g}]:" + "/".join(notes),
                              model_version="belief-planning-1")
        self._cache[cache_key] = out
        return out
