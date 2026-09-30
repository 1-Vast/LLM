"""The in-context world model: reading forecasts conditioned on the compound's own measured prompts.

File summary
- Path: research/incontext_world/world.py
- Purpose: extend `belief_planning.world.ReferenceWorld` with one in-context layer. The current
  world model conditions a forecast on the *labels* of earlier readings only. This layer also
  conditions on the measured *shifts* behind them, as Stack conditions a prediction on prompt cells
  from the same condition.
- Core points:
  - The layer. Under hypothesis h, each reference r of h gets the weight
        a_r = kappa * (label-history weight of r) * prod_p exp(tau * (sim_r(p) - 1)),
    and the forecast is (sum_r a_r * reading_r + reference forecast) / (sum_r a_r + 1). The layer
    is shrunk to the current forecast with unit strength, like the structural layer beneath it.
    kappa = 0, no prompt, or only hypothetical (lookahead) prompts give exactly the reference
    forecast.
  - Two knowledge sources (PRESAGE: knowledge-source choice matters more than architecture):
    - `prompt`: the projected cosine at the prompt condition p between the compound's measured
      shift and reference r's. It is the validator's geometry, with the shared axis of p's
      references removed. A reference not measured at p gets the mean similarity of those that were.
    - `transfer`: the projected cosine at the target condition c between the virtual cell's
      prediction of the compound's shift at c (`transition.ridge_st` from each prompt, averaged
      over prompts) and reference r's measured shift at c. This is the virtual-cell observation
      model used as a similarity, not as a result.
  - Empirical Bayes, not tuning. Source, kappa and tau come from the fixed grids below. They are
    chosen per fold by the predictive log-likelihood of training references' own readings under
    single-prompt histories. Each target reference is predicted with every reference of its own
    unit left out, and only from non-eliminating prompt readings, the states a planner can be in.
    Transfer similarities use each reference's leave-one-out transition prediction.
  - Availability (Stack's rule). A prompt is a real, QC-passed measurement of the same compound
    already bought in this episode. The target condition's own shift is never a prompt. A QC
    failure conditions nothing.
  - Every forecast carries `model_version`, the fitted layer in `basis`, and the in-context
    effective support (Kish) of each branch. A refusal of the reference model passes through.
- Interfaces: `InContextWorld`, `GRIDS`, `SOURCES`, `MODEL_VERSION`
- Depends on: research/belief_planning/world.py, transition.py, metrics.py, maestro.acquisition
"""
from __future__ import annotations

import hashlib

import numpy as np

from maestro.acquisition import OutcomeBranch, OutcomeForecast
from research.belief_planning import world as W

from . import metrics as M
from . import transition as TR

MODEL_VERSION = "incontext-world-1"
SOURCES = ("prompt", "transfer")
GRIDS = {"kappa": (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0), "tau": (1.0, 2.0, 4.0, 8.0, 16.0, 32.0)}
"""Fixed in spec.json before any score; each fold picks by training leave-one-unit-out likelihood."""


def restrict(fitted: dict, source: str) -> dict:
    """The fitted layer with the source fixed: the best (kappa, tau) within that source's likelihood table."""
    table = fitted.get("loglik", {}).get(source)
    if not table or not fitted.get("items", {}).get(source):
        return {"source": "off", "kappa": 0.0, "tau": 0.0}
    ll = np.asarray(table)
    i, j = np.unravel_index(int(np.argmax(ll)), ll.shape)
    kappa, tau = float(GRIDS["kappa"][i]), float(GRIDS["tau"][j])
    if kappa == 0.0:
        return {"source": "off", "kappa": 0.0, "tau": 0.0}
    return {"source": source, "kappa": kappa, "tau": tau, "gain": float(ll[i, j] - ll[0, 0])}


def _digest(profiles: dict) -> tuple:
    return tuple(sorted((tuple(k), hashlib.sha1(np.ascontiguousarray(v, dtype=np.float64).tobytes()).hexdigest()[:16])
                        for k, v in profiles.items() if v is not None))


class InContextWorld(W.ReferenceWorld):
    """Reading forecasts for one fold, with the in-context layer on top of the reference world."""

    def __init__(self, ft, params, training_compounds, *, source: str = "auto", incontext=None, groups=None, **kwargs):
        if source not in ("auto", "off") + SOURCES:
            raise ValueError(source)
        super().__init__(ft, params, training_compounds, groups=groups, **kwargs)
        self.groups = dict(groups or {})
        self.source_mode = source
        self._geometry, self._transitions, self._ic_cache = {}, {}, {}
        self.incontext = dict(incontext) if incontext else self.fit_incontext()

    # ------------------------------------------------------------------ geometry and transitions
    def geometry(self, key):
        """(shared axis, unit projected rows) of the references at `key`, the validator's geometry."""
        if key not in self._geometry:
            Y = np.asarray(self.ft.tables[key].Y, dtype=np.float64)
            u = M._unit(Y.sum(0)) if len(Y) else None
            P = Y - np.outer(Y @ u, u) if u is not None else Y
            norms = np.linalg.norm(P, axis=1, keepdims=True)
            self._geometry[key] = (u, np.where(norms > 1e-12, P / np.maximum(norms, 1e-12), 0.0))
        return self._geometry[key]

    def cosine(self, key, v) -> np.ndarray:
        """Projected cosine of shift `v` to every reference at `key`."""
        u, Rn = self.geometry(key)
        v = np.asarray(v, dtype=np.float64)
        vp = v - (v @ u) * u if u is not None else v
        n = float(np.linalg.norm(vp))
        return Rn @ vp / n if n > 1e-12 else np.zeros(len(Rn))

    def cosines(self, key, V) -> np.ndarray:
        """Projected cosines of each row of `V` to every reference at `key` (rows x references)."""
        u, Rn = self.geometry(key)
        V = np.atleast_2d(np.asarray(V, dtype=np.float64))
        Vp = V - np.outer(V @ u, u) if u is not None else V
        n = np.linalg.norm(Vp, axis=1, keepdims=True)
        return np.where(n > 1e-12, (Vp / np.maximum(n, 1e-12)) @ Rn.T, 0.0)

    def transition(self, p_key, c_key) -> TR.Transition:
        if (p_key, c_key) not in self._transitions:
            tp, tc = self.ft.tables[p_key], self.ft.tables[c_key]
            prow = self.keys[p_key]["row"]
            names = [n for n in tc.names if n in prow]
            crow = self.keys[c_key]["row"]
            X = tp.Y[[prow[n] for n in names]] if names else np.zeros((0, tp.Y.shape[1]))
            Y = tc.Y[[crow[n] for n in names]] if names else np.zeros((0, tc.Y.shape[1]))
            self._transitions[(p_key, c_key)] = TR.fit(p_key, c_key, names, X, Y, np.zeros(tc.Y.shape[1]))
        return self._transitions[(p_key, c_key)]

    def context_logkernel(self, key, profiles: dict, source: str):
        """Per reference at `key`: the summed (similarity - 1) over usable prompts; None if none is usable."""
        entry = self.keys[key]
        prompts = [(tuple(p), v) for p, v in profiles.items()
                   if v is not None and tuple(p) != tuple(key) and tuple(p) in self.keys]
        if not prompts:
            return None
        if source == "prompt":
            total = np.zeros(len(entry["names"]))
            for p, v in prompts:
                sim = self.cosine(p, v)
                prow = np.asarray([self.keys[p]["row"].get(n, -1) for n in entry["names"]])
                measured = prow >= 0
                values = np.where(measured, sim[np.maximum(prow, 0)], np.nan)
                fill = float(np.nanmean(values)) if measured.any() else 0.0
                total += np.where(measured, values, fill) - 1.0
            return total
        predictions = []
        for p, v in prompts:
            tr = self.transition(p, tuple(key))
            if tr.k > 0:
                predictions.append(tr.predict(v))
        if not predictions:
            return None
        return self.cosine(tuple(key), np.mean(predictions, axis=0)) - 1.0

    # ------------------------------------------------------------------ empirical Bayes
    def fit_incontext(self) -> dict:
        """Choose (source, kappa, tau) by leave-one-unit-out likelihood of training references' readings."""
        if self.source_mode == "off" or not self.eliminates:
            return {"source": "off", "kappa": 0.0, "tau": 0.0, "items": 0}
        sources = SOURCES if self.source_mode == "auto" else (self.source_mode,)
        hp = self.hyperparameters
        s, e = hp["s"], hp["e"]
        k_vc = 0.0 if self.vc == "masked" else hp["k"]
        kappas, taus = np.asarray(GRIDS["kappa"]), np.asarray(GRIDS["tau"])
        ll = {src: np.zeros((len(kappas), len(taus))) for src in sources}
        items = {src: 0 for src in sources}
        eye = np.eye(4)
        for c_key, entry in self.keys.items():
            names = entry["names"]
            unit = np.asarray([self.groups.get(n, n) for n in names], dtype=object)
            fp, has_fp = self._ref_fps(entry)
            tanimoto = W._tanimoto_matrix(fp, fp) if (fp is not None and k_vc > 0) else None
            for p_key, pent in self.keys.items():
                if p_key == c_key:
                    continue
                prow = np.asarray([pent["row"].get(n, -1) for n in names])
                sims = {}
                if "prompt" in sources:
                    _, Rn = self.geometry(p_key)
                    measured = prow >= 0
                    S = np.full((len(names), len(names)), np.nan)
                    idx = np.flatnonzero(measured)
                    if len(idx):
                        V = Rn[prow[idx]]
                        S[np.ix_(idx, idx)] = V @ V.T
                    sims["prompt"] = S
                if "transfer" in sources:
                    tr = self.transition(p_key, c_key)
                    S = np.full((len(names), len(names)), np.nan)
                    if tr.k > 0:
                        rows = np.asarray([entry["row"][n] for n in tr.names])
                        S[rows] = self.cosines(c_key, tr.loo_predictions())
                    sims["transfer"] = S
                for h, hi in self.cidx.items():
                    rows = np.flatnonzero(entry["klass"] == h)
                    if len(rows) < 3:
                        continue
                    for oi in range(len(self.classes)):
                        if oi == hi:
                            continue
                        c = entry["cat"][rows, oi]
                        valid = c >= 0
                        pc = np.where(prow[rows] >= 0, pent["cat"][np.maximum(prow[rows], 0), oi], -1)
                        # targets: references with a non-eliminating prompt reading and a scored target reading
                        targets = np.flatnonzero(valid & ((pc == 2) | (pc == 3)))
                        if len(targets) == 0:
                            continue
                        onehot = np.where(valid[:, None], eye[np.maximum(c, 0)], 0.0)
                        label = pc[targets]
                        same_unit = unit[rows][targets][:, None] == unit[rows][None, :]
                        mask = (~same_unit) & valid[None, :]
                        if (mask.sum(1) < 2).all():
                            continue
                        base_p = pent["pooled"][label][:, None]
                        known = (pc >= 0)[None, :]
                        hist = np.where(known, np.where(pc[None, :] == label[:, None], 1.0, e), base_p) * mask
                        cls = (hist @ onehot + s * entry["pooled"][None, :]) / (hist.sum(1, keepdims=True) + s)
                        base = cls
                        if tanimoto is not None:
                            sub = tanimoto[np.ix_(rows[targets], rows)]
                            kern = W._kernel(sub, k_vc) * hist * has_fp[rows][None, :] * has_fp[rows[targets]][:, None]
                            base = (kern @ onehot + cls) / (kern.sum(1, keepdims=True) + 1.0)
                        truth = c[targets]
                        for src, S in sims.items():
                            L = S[np.ix_(rows[targets], rows)]
                            defined = np.isfinite(L) & mask
                            usable = np.isfinite(S[rows[targets], rows[targets]]) if src == "prompt" else \
                                np.isfinite(S[rows[targets]]).any(1)
                            # a reference unmeasured at p gets the mean similarity over every reference
                            # measured there (all classes, the target's unit excluded), as in `forecast`
                            full = S[rows[targets]]
                            seen = np.isfinite(full) & (unit[None, :] != unit[rows][targets][:, None])
                            row_mean = np.where(seen, full, 0.0).sum(1) / np.maximum(seen.sum(1), 1)
                            logk = np.where(defined, L, row_mean[:, None]) - 1.0
                            keep = usable & (mask.sum(1) >= 2)
                            if not keep.any():
                                continue
                            items[src] += int(keep.sum())
                            for j, tau in enumerate(taus):
                                w = hist * np.exp(tau * logk)
                                A = w @ onehot
                                Wsum = w.sum(1)
                                for i, kappa in enumerate(kappas):
                                    probs = (kappa * A + base) / (kappa * Wsum + 1.0)[:, None]
                                    picked = probs[np.arange(len(targets)), truth]
                                    ll[src][i, j] += float(np.log(np.maximum(picked[keep], 1e-12)).sum())
        best = {"source": "off", "kappa": 0.0, "tau": 0.0}
        best_ll = None
        table = {}
        for src in sources:
            table[src] = ll[src].round(3).tolist()
            if items[src] == 0:
                continue
            i, j = np.unravel_index(int(np.argmax(ll[src])), ll[src].shape)
            if best_ll is None or ll[src][i, j] > best_ll + 1e-9:
                best_ll = float(ll[src][i, j])
                best = {"source": src, "kappa": float(kappas[i]), "tau": float(taus[j])}
        if best["kappa"] == 0.0:
            best = {"source": "off", "kappa": 0.0, "tau": 0.0}
        baseline = {src: float(ll[src][0, 0]) for src in sources if items[src]}
        return {**best, "loglik": table, "loglik_kappa0": baseline, "items": items,
                "gain": (best_ll - baseline.get(best["source"], best_ll)) if best_ll is not None and best["source"] != "off" else 0.0,
                "grids": {k: list(v) for k, v in GRIDS.items()}}

    # ------------------------------------------------------------------ forecast
    def forecast(self, key, h1, h2, compound, history=(), profiles=None) -> OutcomeForecast:
        """Per-hypothesis reading distribution for measuring `key`.

        `history` is ((key, label), ...) as for the reference world. `profiles` maps each already
        measured, QC-passed condition of this compound to its measured shift. Hypothetical
        lookahead steps have labels but no shifts, so they condition only through labels.
        """
        base = super().forecast(key, h1, h2, compound, history)
        hp = self.incontext
        source = hp.get("source", "off")
        if base.refusal or not profiles or source == "off" or hp.get("kappa", 0.0) <= 0.0:
            return self._stamp(base, "incontext:off" if source == "off" or hp.get("kappa", 0.0) <= 0 else "incontext:no_prompt")
        cache_key = (tuple(key), h1, h2, compound, tuple(history), _digest(profiles))
        if cache_key in self._ic_cache:
            return self._ic_cache[cache_key]
        logk = self.context_logkernel(tuple(key), profiles, source)
        if logk is None:
            out = self._stamp(base, "incontext:no_usable_prompt")
            self._ic_cache[cache_key] = out
            return out
        used = history
        if self.feedback == "withheld":
            used = tuple((k, W.NONTERMINAL if lab != W.QC_FAILED else W.QC_FAILED) for k, lab in history)
        entry = self.keys[tuple(key)]
        branches, neff = [], []
        for branch, (own, other, match_own, match_other) in zip(
                base.branches, ((h1, h2, W.MATCH_H1, W.MATCH_H2), (h2, h1, W.MATCH_H2, W.MATCH_H1))):
            oi = self.cidx[other]
            rows = np.flatnonzero(entry["klass"] == own)
            c = entry["cat"][rows, oi]
            ok = c >= 0
            rows, c = rows[ok], c[ok]
            labels = (match_own, match_other, W.UNRESOLVED, W.ABSENT)
            qc = float(branch.probabilities.get(W.QC_FAILED, 0.0))
            prior = np.array([branch.probabilities.get(lab, 0.0) for lab in labels]) / max(1.0 - qc, 1e-12)
            if len(rows) == 0:
                branches.append(branch)
                neff.append(0.0)
                continue
            names = [entry["names"][r] for r in rows]
            hist = self._history_weights(rows, names, oi, used)
            a = hp["kappa"] * hist * np.exp(hp["tau"] * logk[rows])
            probs = (a @ np.eye(4)[c] + prior) / (a.sum() + 1.0)
            dist = {lab: float((1.0 - qc) * p) for lab, p in zip(labels, probs)}
            dist[W.QC_FAILED] = qc
            branches.append(OutcomeBranch(own, dist, branch.support))
            neff.append(float(a.sum() ** 2 / (a ** 2).sum()) if (a ** 2).sum() > 0 else 0.0)
        basis = (f"{base.basis}|incontext[{source},kappa={hp['kappa']:g},tau={hp['tau']:g},"
                 f"prompts={len([v for v in profiles.values() if v is not None])},"
                 f"neff={'/'.join(f'{x:.2f}' for x in neff)}]")
        out = OutcomeForecast(base.action_identifier, tuple(branches), basis=basis, model_version=MODEL_VERSION)
        self._ic_cache[cache_key] = out
        return out

    def _stamp(self, forecast: OutcomeForecast, note: str) -> OutcomeForecast:
        if forecast.refusal:
            return OutcomeForecast(forecast.action_identifier, forecast.branches, basis=f"{forecast.basis}|{note}",
                                   refusal=forecast.refusal, model_version=MODEL_VERSION)
        return OutcomeForecast(forecast.action_identifier, forecast.branches, basis=f"{forecast.basis}|{note}",
                               model_version=MODEL_VERSION)
