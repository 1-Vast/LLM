"""The strict in-context world model: block 6's in-context layer, refitted with strict inner group validation.

File summary
- Path: research/dual_core/world2.py
- Purpose: the planning-facing world model of the dual-core iteration. It gives the belief planner
  P(validator reading | hypothesis, measurement, readings and purchased prompts so far).
- Core points:
  - Same layer as `incontext_world.InContextWorld`: references of the hypothesis are weighted by
    kappa x label-history weight x prod exp(tau (sim - 1)). The layer is shrunk to the reference
    world with unit strength. kappa = 0, or no usable purchased prompt, gives exactly the reference
    world.
  - Changes from block 6:
    - Transfer. The similarity source uses `transfer.fit_pair` with the arm E1 keeps (`rrt_q` or
      `ridge_st`). Its hyperparameters come from inner group CV, and each prompt's measured quality
      enters `rrt_q`.
    - Strict nesting. `fit_incontext` deals the training references into 4 inner folds by
      independent unit. For each inner fold it refits, on the inner-training references only:
      - the transitions;
      - the projected geometry (shared axes);
      - the pooled reading frequencies;
      - the class and structural layers.
      It then scores the inner-test references' own readings. Block 6 left a reference out of the
      kernel but not out of the transition's principal components or means.
    - Prompts. They are `ledger.Prompt` objects: purchased, QC-passed and identity-checked by the
      executor's ledger. A bare array is refused.
  - The reference world's own (s, k, e) are shared with it, fitted as registered in block 2 (exact
    leave-one-compound-out counts), so the comparison isolates the in-context layer.
  - Reference prompt qualities are a training measurement field. They are passed in explicitly and
    must not name a held-out compound.
- Interfaces: `StrictInContextWorld`, `MODEL_VERSION`
- Depends on: research/incontext_world/world.py, transfer.py, ledger.py
"""
from __future__ import annotations

import numpy as np

from maestro.acquisition import OutcomeBranch, OutcomeForecast
from research.belief_planning import world as W
from research.incontext_world import metrics as M
from research.incontext_world import world as IW

from . import transfer as TF
from .ledger import Prompt

MODEL_VERSION = "dual-core-world-1"


def _geometry(Y):
    Y = np.asarray(Y, dtype=np.float64)
    u = M._unit(Y.sum(0)) if len(Y) else None
    P = Y - np.outer(Y @ u, u) if u is not None else Y
    n = np.linalg.norm(P, axis=1, keepdims=True)
    return u, np.where(n > 1e-12, P / np.maximum(n, 1e-12), 0.0)


def _cos(geom, V):
    u, Rn = geom
    V = np.atleast_2d(np.asarray(V, dtype=np.float64))
    Vp = V - np.outer(V @ u, u) if u is not None else V
    n = np.linalg.norm(Vp, axis=1, keepdims=True)
    return np.where(n > 1e-12, (Vp / np.maximum(n, 1e-12)) @ Rn.T, 0.0)


class StrictInContextWorld(IW.InContextWorld):
    """Reading forecasts for one fold with a strictly nested in-context layer."""

    def __init__(self, ft, params, training_compounds, *, reference_quality: dict, transfer_arm: str = "rrt_q",
                 source: str = "auto", incontext=None, groups=None, heldout=(), **kwargs):
        if transfer_arm not in ("rrt_q", "ridge_st"):
            raise ValueError(transfer_arm)
        leaked = set(reference_quality) & set(heldout)
        if leaked:
            raise ValueError(f"reference qualities name held-out compounds: {sorted(leaked)[:3]}")
        self.reference_quality = {n: dict(v) for n, v in reference_quality.items()}
        self.transfer_arm = transfer_arm
        self._pairs = {}
        super().__init__(ft, params, training_compounds, source=source, incontext=incontext, groups=groups, **kwargs)

    # ------------------------------------------------------------------ transitions
    def _quality(self, name, key) -> float:
        return float(self.reference_quality.get(name, {}).get(tuple(key), 0.0))

    def pair(self, p_key, c_key, names=None) -> TF.PairModel:
        """Transition p -> c on `names`; the full-training fit (names=None) is cached, inner-fold fits are not."""
        tp, tc = self.ft.tables[p_key], self.ft.tables[c_key]
        prow, crow = self.keys[p_key]["row"], self.keys[c_key]["row"]
        pool = [n for n in tc.names if n in prow] if names is None else [n for n in names if n in prow and n in crow]
        if names is None and (p_key, c_key) in self._pairs:
            return self._pairs[(p_key, c_key)]
        X = tp.Y[[prow[n] for n in pool]] if pool else np.zeros((0, tp.Y.shape[1]))
        Y = tc.Y[[crow[n] for n in pool]] if pool else np.zeros((0, tc.Y.shape[1]))
        q = [self._quality(n, p_key) for n in pool]
        model = TF.fit_pair(p_key, c_key, X, Y, q, [self.groups.get(n, n) for n in pool])
        if names is None:
            self._pairs[(p_key, c_key)] = model
        return model

    def context_logkernel(self, key, profiles: dict, source: str):
        key = tuple(key)
        prompts = {}
        for p, prompt in profiles.items():
            if prompt is None:
                continue
            if not isinstance(prompt, Prompt):
                raise TypeError("prompts must be ledger.Prompt objects (purchased, QC-passed, identity-checked)")
            if tuple(p) == key or tuple(p) not in self.keys:
                continue
            prompts[tuple(p)] = prompt
        if not prompts:
            return None
        # the kernel depends on the target and the purchased prompts only, never on hypothetical lookahead labels
        cache_key = (key, source, tuple(sorted((p, pr.digest) for p, pr in prompts.items())))
        if cache_key not in self._ic_cache:
            self._ic_cache[cache_key] = self._logkernel(key, prompts, source)
        return self._ic_cache[cache_key]

    def _logkernel(self, key, prompts: dict, source: str):
        entry = self.keys[key]
        if source == "prompt":
            total = np.zeros(len(entry["names"]))
            for p, prompt in prompts.items():
                sim = self.cosine(p, prompt.shift)
                prow = np.asarray([self.keys[p]["row"].get(n, -1) for n in entry["names"]])
                measured = prow >= 0
                values = np.where(measured, sim[np.maximum(prow, 0)], np.nan)
                fill = float(np.nanmean(values)) if measured.any() else 0.0
                total += np.where(measured, values, fill) - 1.0
            return total
        predictions, errors = [], []
        for p, prompt in prompts.items():
            pm = self.pair(p, key)
            if pm.references >= 6:
                predictions.append(pm.predict(prompt.shift, prompt.quality, self.transfer_arm))
                errors.append(pm.inner_mse.get(self.transfer_arm, np.inf))
        if not predictions:
            return None
        # several prompts: inverse inner-CV error weights (kept by E1's A2 rule)
        combined, _ = TF.aggregate(predictions, errors, "rrt_precision")
        return self.cosine(key, combined) - 1.0

    # ------------------------------------------------------------------ strict empirical Bayes
    def fit_incontext(self) -> dict:
        if self.source_mode == "off" or not self.eliminates:
            return {"source": "off", "kappa": 0.0, "tau": 0.0, "items": {}, "nesting": "strict_inner_group"}
        sources = IW.SOURCES if self.source_mode == "auto" else (self.source_mode,)
        hp = self.hyperparameters
        s, e = hp["s"], hp["e"]
        k_vc = 0.0 if self.vc == "masked" else hp["k"]
        kappas, taus = np.asarray(IW.GRIDS["kappa"]), np.asarray(IW.GRIDS["tau"])
        ll = {src: np.zeros((len(kappas), len(taus))) for src in sources}
        items = {src: 0 for src in sources}
        eye = np.eye(4)
        everyone = sorted(set().union(*[set(t.names) for t in self.ft.tables.values()]))
        inner = dict(zip(everyone, TF.inner_folds([self.groups.get(n, n) for n in everyone])))
        for f in range(TF.INNER):
            train_set = {n for n in everyone if inner[n] != f}
            geoms, pooled_inner = {}, {}
            for key, table in self.ft.tables.items():
                rows = [i for i, n in enumerate(table.names) if n in train_set]
                geoms[key] = (_geometry(table.Y[rows]), rows)
                cat = self.keys[key]["cat"][rows]
                counts = np.bincount(cat[cat >= 0], minlength=4).astype(float) + 0.5
                pooled_inner[key] = counts / counts.sum()
            for c_key, entry in self.keys.items():
                names = entry["names"]
                n_c = len(names)
                in_train = np.asarray([n in train_set for n in names])
                fp, has_fp = self._ref_fps(entry)
                tanimoto = W._tanimoto_matrix(fp, fp) if (fp is not None and k_vc > 0) else None
                cat_c = entry["cat"]
                pooled_tr = pooled_inner[c_key]
                g_c, rows_c = geoms[c_key]
                col_c = np.full(n_c, -1)
                col_c[rows_c] = np.arange(len(rows_c))
                for p_key, pent in self.keys.items():
                    if p_key == c_key:
                        continue
                    prow = np.asarray([pent["row"].get(n, -1) for n in names])
                    tp = self.ft.tables[p_key]
                    sims = {}
                    if "prompt" in sources:
                        g_p, rows_p = geoms[p_key]
                        col_p = np.full(len(tp.names), -1)
                        col_p[rows_p] = np.arange(len(rows_p))
                        S = np.full((n_c, n_c), np.nan)
                        tgt = np.flatnonzero(~in_train & (prow >= 0))
                        oth = np.flatnonzero(in_train & (prow >= 0))
                        if len(tgt) and len(oth):
                            C = _cos(g_p, tp.Y[prow[tgt]])                     # targets x inner-train refs at p
                            S[np.ix_(tgt, oth)] = C[:, col_p[prow[oth]]]
                        sims["prompt"] = S
                    if "transfer" in sources:
                        S = np.full((n_c, n_c), np.nan)
                        tgt = np.flatnonzero(~in_train & (prow >= 0))
                        pm = self.pair(p_key, c_key, names=sorted(n for n in train_set))
                        if len(tgt) and pm.references >= 6:
                            preds = np.stack([pm.predict(tp.Y[prow[t]], self._quality(names[t], p_key), self.transfer_arm)
                                              for t in tgt])
                            C = _cos(g_c, preds)                                  # targets x inner-train refs at c
                            oth = np.flatnonzero(in_train)
                            S[np.ix_(tgt, oth)] = C[:, col_c[oth]]
                        sims["transfer"] = S
                    for h, hi in self.cidx.items():
                        rows = np.flatnonzero(entry["klass"] == h)
                        if len(rows) < 3:
                            continue
                        for oi in range(len(self.classes)):
                            if oi == hi:
                                continue
                            c = cat_c[rows, oi]
                            valid = c >= 0
                            pc = np.where(prow[rows] >= 0, pent["cat"][np.maximum(prow[rows], 0), oi], -1)
                            targets = np.flatnonzero(valid & ~in_train[rows] & ((pc == 2) | (pc == 3)))
                            others = valid & in_train[rows]
                            if len(targets) == 0 or others.sum() < 2:
                                continue
                            onehot = np.where(valid[:, None], eye[np.maximum(c, 0)], 0.0)
                            label = pc[targets]
                            mask = np.broadcast_to(others[None, :], (len(targets), len(rows)))
                            known = (pc >= 0)[None, :]
                            base_p = pooled_inner[p_key][label][:, None]
                            hist = np.where(known, np.where(pc[None, :] == label[:, None], 1.0, e), base_p) * mask
                            cls = (hist @ onehot + s * pooled_tr[None, :]) / (hist.sum(1, keepdims=True) + s)
                            base = cls
                            if tanimoto is not None:
                                sub = tanimoto[np.ix_(rows[targets], rows)]
                                kern = W._kernel(sub, k_vc) * hist * has_fp[rows][None, :] * has_fp[rows[targets]][:, None]
                                base = (kern @ onehot + cls) / (kern.sum(1, keepdims=True) + 1.0)
                            truth = c[targets]
                            for src, S in sims.items():
                                L = S[np.ix_(rows[targets], rows)]
                                defined = np.isfinite(L) & mask
                                usable = np.isfinite(S[rows[targets]]).any(1)
                                full = S[rows[targets]]
                                seen = np.isfinite(full)
                                row_mean = np.where(seen, full, 0.0).sum(1) / np.maximum(seen.sum(1), 1)
                                logk = np.where(defined, L, row_mean[:, None]) - 1.0
                                keep = usable
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
        best, best_ll, table = {"source": "off", "kappa": 0.0, "tau": 0.0}, None, {}
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
        return {**best, "loglik": table, "loglik_kappa0": baseline, "items": items, "nesting": "strict_inner_group",
                "transfer_arm": self.transfer_arm,
                "gain": (best_ll - baseline.get(best["source"], best_ll)) if best_ll is not None and best["source"] != "off" else 0.0,
                "grids": {k: list(v) for k, v in IW.GRIDS.items()}}

    def forecast(self, key, h1, h2, compound, history=(), profiles=None) -> OutcomeForecast:
        out = super().forecast(key, h1, h2, compound, history, profiles=profiles)
        return OutcomeForecast(out.action_identifier, out.branches, basis=out.basis, refusal=out.refusal,
                               model_version=MODEL_VERSION)
