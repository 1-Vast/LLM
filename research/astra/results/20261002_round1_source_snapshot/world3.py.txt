"""World model v2: training-selected conversion from a predicted response to reading probabilities, with a strict prompt contract.

File summary
- Path: research/dual_core_v2/world3.py
- Purpose: the planning-facing world model of the dual-core v2 correction. It extends block 7's
  `world2.StrictInContextWorld` and leaves its two sources byte-for-byte the same, so the block 7
  world is an exact restriction of this one.
- Core points:
  - Sources (the conversion from a purchased prompt to reference weights). All compete through the
    same strictly nested, training-only criterion: the inner-fold log-likelihood of training
    references' own readings (`fit_incontext`). Kappa = 0 (the reference world) always competes.
    - `prompt`: projected cosine at the prompt condition (block 6 and 7);
    - `transfer`: projected cosine at the target between the `rrt_q` prediction and each reference
      (block 7);
    - `additive`: the same with additive transfer, x + m_c - m_p. Block 7's E1 found it discriminates
      compounds better on L1000, yet world2 refused it;
    - `transfer_dist`: the `rrt_q` prediction with a Euclidean kernel in the projected space,
      -|v - r|^2 / (2 s_c), where s_c is the median squared projected norm of the training
      references at the target. It keeps magnitude, which the cosine discards and which predicts
      detection (E1 effect AUROC 0.84-0.85). It is the one alternative conversion tested.
    - `oracle`, `oracle_dist` (diagnostic only, `diagnostic=True`): the target reference's own
      measured shift in place of a prediction. They bound what a perfect response model could do
      through this interface. They are never selectable and are only reached by
      `forecast_from_logkernel` in evaluation code.
  - Prompt contract. `forecast` accepts prompts only as a `PromptSet` issued by `LedgerV2`. It
    refuses, by named reason, a bare mapping (`not_a_prompt_set`), another compound's prompt
    (`identity_mismatch`), another dataset or assay (`dataset_mismatch`), a prompt bought at or
    after the decision point (`future_measurement`), the target condition (`target_outcome_leakage`),
    an unknown condition (`unknown_condition`) and a non-finite quality (`invalid_quality`).
  - Cache identity. Kernels are cached on (target, source, and per prompt: condition, shift digest,
    quality, compound, row); forecasts additionally on the in-context parameters (source, kappa,
    tau). Block 7 keyed both on the shift digest alone, so a changed quality could reuse a stale
    kernel. On the frozen data a row's quality never changes, so this is a contract repair, not the
    cause of any historical result.
  - `variant(source)` returns a clone restricted to one source, or `variant("v1")` the block 7
    selection (best of prompt and transfer), sharing fitted transitions and reference caches.
  - Predictions stay predictions: forecasts carry `MODEL_VERSION`; nothing here touches evidence.
- Interfaces: `SOURCES`, `DIAGNOSTIC_SOURCES`, `PromptSet`, `PromptRefused`, `LedgerV2`, `WorldV2`,
  `MODEL_VERSION`
- Depends on: research/dual_core (world2, transfer, ledger), research/incontext_world, research/belief_planning
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np

from maestro.acquisition import OutcomeBranch, OutcomeForecast
from research.belief_planning import world as W
from research.dual_core import transfer as TF
from research.dual_core import world2 as W2
from research.dual_core.ledger import Prompt, PurchaseLedger
from research.incontext_world import world as IW

MODEL_VERSION = "dual-core-world-2"
SOURCES = ("prompt", "transfer", "additive", "transfer_dist")
DIAGNOSTIC_SOURCES = ("oracle", "oracle_dist")
V1_SOURCES = ("prompt", "transfer")


class PromptRefused(ValueError):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason


@dataclass(frozen=True)
class PromptSet:
    """Prompts a ledger issued for one forecast: the compound, the decision point and the prompts."""

    compound: str
    dataset: str
    assay: str
    decision_point: int
    prompts: tuple
    issuer: str

    def by_condition(self) -> dict:
        return {tuple(p.condition): p for p in self.prompts}

    def identity(self) -> tuple:
        return tuple(sorted((tuple(p.condition), p.digest, round(float(p.quality), 12), p.compound, p.row)
                            for p in self.prompts))


class LedgerV2(PurchaseLedger):
    """Block 7's ledger plus `prompt_set`, the only constructor of a `PromptSet`."""

    def prompt_set(self, *, target, executed) -> PromptSet:
        prompts = self.prompts(target=target, executed=executed)
        return PromptSet(self.compound, self.dataset, self.assay, len(executed), tuple(prompts.values()),
                         f"ledger:{id(self)}")


def _median_sq_norm(geom_u, Y) -> float:
    Y = np.atleast_2d(np.asarray(Y, dtype=np.float64))
    P = Y - np.outer(Y @ geom_u, geom_u) if geom_u is not None else Y
    return float(np.median((P * P).sum(1))) if len(P) else 1.0


def _dist_logk(geom_u, V, R, scale) -> np.ndarray:
    """-|v_perp - r_perp|^2 / (2 scale) for each row of V against each row of R (shared axis removed)."""
    V = np.atleast_2d(np.asarray(V, dtype=np.float64))
    R = np.atleast_2d(np.asarray(R, dtype=np.float64))
    if geom_u is not None:
        V = V - np.outer(V @ geom_u, geom_u)
        R = R - np.outer(R @ geom_u, geom_u)
    d2 = (V * V).sum(1)[:, None] + (R * R).sum(1)[None, :] - 2 * V @ R.T
    return -np.maximum(d2, 0.0) / (2.0 * max(scale, 1e-12))


class WorldV2(W2.StrictInContextWorld):
    """Reading forecasts for one fold with training-selected conversion sources and a strict prompt contract."""

    def __init__(self, ft, params, training_compounds, *, dataset: str, assay: str, sources=SOURCES,
                 diagnostic: bool = False, **kwargs):
        self.dataset, self.assay = dataset, assay
        self.candidate_sources = tuple(sources)
        self.diagnostic = bool(diagnostic)
        self._scales = {}
        kwargs.setdefault("transfer_arm", "rrt_q")
        super().__init__(ft, params, training_compounds, **kwargs)

    # ------------------------------------------------------------------ variants
    def variant(self, which: str) -> "WorldV2":
        """A clone restricted to one source ('off', a source, 'v1' or 'auto'); fits and caches are shared."""
        clone = copy.copy(self)
        clone._ic_cache = {}
        fitted = self.fitted
        if which == "auto":
            chosen = self._best(fitted, self.candidate_sources)
        elif which == "v1":
            chosen = self._best(fitted, V1_SOURCES)
        elif which == "off":
            chosen = {"source": "off", "kappa": 0.0, "tau": 0.0}
        else:
            chosen = IW.restrict(fitted, which)
        clone.incontext = {**{k: v for k, v in fitted.items() if k not in ("source", "kappa", "tau", "gain")},
                           **chosen, "variant": which}
        return clone

    @staticmethod
    def _best(fitted: dict, sources) -> dict:
        best, best_ll = {"source": "off", "kappa": 0.0, "tau": 0.0}, None
        for src in sources:
            table = fitted.get("loglik", {}).get(src)
            if not table or not fitted.get("items", {}).get(src):
                continue
            ll = np.asarray(table)
            i, j = np.unravel_index(int(np.argmax(ll)), ll.shape)
            if best_ll is None or ll[i, j] > best_ll + 1e-9:
                best_ll = float(ll[i, j])
                best = {"source": src, "kappa": float(IW.GRIDS["kappa"][i]), "tau": float(IW.GRIDS["tau"][j])}
        if best["kappa"] == 0.0:
            best = {"source": "off", "kappa": 0.0, "tau": 0.0}
        base = fitted.get("loglik_kappa0", {}).get(best["source"])
        return {**best, "gain": (best_ll - base) if (best_ll is not None and base is not None and best["source"] != "off") else 0.0}

    def scale(self, key) -> float:
        if key not in self._scales:
            u, _ = self.geometry(key)
            self._scales[key] = _median_sq_norm(u, self.ft.tables[key].Y)
        return self._scales[key]

    # ------------------------------------------------------------------ strict empirical Bayes
    def fit_incontext(self) -> dict:
        """Block 7's strictly nested fit, extended with the v2 sources; prompt and transfer are unchanged."""
        if self.source_mode == "off" or not self.eliminates:
            self.fitted = {"source": "off", "kappa": 0.0, "tau": 0.0, "items": {}, "nesting": "strict_inner_group"}
            return dict(self.fitted)
        sources = tuple(self.candidate_sources) + (DIAGNOSTIC_SOURCES if self.diagnostic else ())
        hp = self.hyperparameters
        s, e = hp["s"], hp["e"]
        k_vc = 0.0 if self.vc == "masked" else hp["k"]
        kappas, taus = np.asarray(IW.GRIDS["kappa"]), np.asarray(IW.GRIDS["tau"])
        ll = {src: np.zeros((len(kappas), len(taus))) for src in sources}
        items = {src: 0 for src in sources}
        eye = np.eye(4)
        everyone = sorted(set().union(*[set(t.names) for t in self.ft.tables.values()]))
        inner = dict(zip(everyone, TF.inner_folds([self.groups.get(n, n) for n in everyone])))
        transfer_like = {"transfer", "additive", "transfer_dist"} & set(sources)
        for f in range(TF.INNER):
            train_set = {n for n in everyone if inner[n] != f}
            geoms, pooled_inner = {}, {}
            for key, table in self.ft.tables.items():
                rows = [i for i, n in enumerate(table.names) if n in train_set]
                geoms[key] = (W2._geometry(table.Y[rows]), rows)
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
                tc = self.ft.tables[c_key]
                scale_c = _median_sq_norm(g_c[0], tc.Y[rows_c]) if len(rows_c) else 1.0
                oth_all = np.flatnonzero(in_train)
                for p_key, pent in self.keys.items():
                    if p_key == c_key:
                        continue
                    prow = np.asarray([pent["row"].get(n, -1) for n in names])
                    tp = self.ft.tables[p_key]
                    sims = {}
                    tgt = np.flatnonzero(~in_train & (prow >= 0))
                    if "prompt" in sources:
                        g_p, rows_p = geoms[p_key]
                        col_p = np.full(len(tp.names), -1)
                        col_p[rows_p] = np.arange(len(rows_p))
                        S = np.full((n_c, n_c), np.nan)
                        oth = np.flatnonzero(in_train & (prow >= 0))
                        if len(tgt) and len(oth):
                            C = W2._cos(g_p, tp.Y[prow[tgt]])
                            S[np.ix_(tgt, oth)] = C[:, col_p[prow[oth]]]
                        sims["prompt"] = S
                    if transfer_like:
                        pm = self.pair(p_key, c_key, names=sorted(n for n in train_set))
                        usable = len(tgt) and pm.references >= 6
                        if usable:
                            xs = [tp.Y[prow[t]] for t in tgt]
                            qs = [self._quality(names[t], p_key) for t in tgt]
                            rrt = np.stack([pm.predict(x, q, self.transfer_arm) for x, q in zip(xs, qs)])
                        for src in transfer_like:
                            S = np.full((n_c, n_c), np.nan)
                            if usable:
                                if src == "transfer":
                                    S[np.ix_(tgt, oth_all)] = W2._cos(g_c, rrt)[:, col_c[oth_all]]
                                elif src == "additive":
                                    add = np.stack([pm.predict(x, q, "additive") for x, q in zip(xs, qs)])
                                    S[np.ix_(tgt, oth_all)] = W2._cos(g_c, add)[:, col_c[oth_all]]
                                else:
                                    S[np.ix_(tgt, oth_all)] = 1.0 + _dist_logk(g_c[0], rrt, tc.Y[rows_c], scale_c)[:, col_c[oth_all]]
                            sims[src] = S
                    if self.diagnostic:
                        own = np.flatnonzero(~in_train & (prow >= 0))
                        truth_rows = tc.Y[own] if len(own) else np.zeros((0, tc.Y.shape[1]))
                        for src in DIAGNOSTIC_SOURCES:
                            S = np.full((n_c, n_c), np.nan)
                            if len(own):
                                block = W2._cos(g_c, truth_rows) if src == "oracle" else \
                                    1.0 + _dist_logk(g_c[0], truth_rows, tc.Y[rows_c], scale_c)
                                S[np.ix_(own, oth_all)] = block[:, col_c[oth_all]]
                            sims[src] = S
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
                                usable_rows = np.isfinite(S[rows[targets]]).any(1)
                                full = S[rows[targets]]
                                seen = np.isfinite(full)
                                row_mean = np.where(seen, full, 0.0).sum(1) / np.maximum(seen.sum(1), 1)
                                logk = np.where(defined, L, row_mean[:, None]) - 1.0
                                if not usable_rows.any():
                                    continue
                                items[src] += int(usable_rows.sum())
                                for j, tau in enumerate(taus):
                                    w = hist * np.exp(tau * logk)
                                    A = w @ onehot
                                    Wsum = w.sum(1)
                                    for i, kappa in enumerate(kappas):
                                        probs = (kappa * A + base) / (kappa * Wsum + 1.0)[:, None]
                                        picked = probs[np.arange(len(targets)), truth]
                                        ll[src][i, j] += float(np.log(np.maximum(picked[usable_rows], 1e-12)).sum())
        table = {src: ll[src].round(3).tolist() for src in sources}
        baseline = {src: float(ll[src][0, 0]) for src in sources if items[src]}
        fitted = {"loglik": table, "loglik_kappa0": baseline, "items": items, "nesting": "strict_inner_group",
                  "transfer_arm": self.transfer_arm, "grids": {k: list(v) for k, v in IW.GRIDS.items()},
                  "candidate_sources": list(self.candidate_sources)}
        self.fitted = fitted
        return {**fitted, **self._best(fitted, self.candidate_sources)}

    # ------------------------------------------------------------------ prompt contract
    def validate(self, key, compound, prompts) -> dict:
        """The usable prompts of a `PromptSet` for forecasting `key`; raises `PromptRefused` otherwise."""
        if prompts is None:
            return {}
        if not isinstance(prompts, PromptSet):
            raise PromptRefused("not_a_prompt_set", type(prompts).__name__)
        if prompts.compound != compound:
            raise PromptRefused("identity_mismatch", f"set for {prompts.compound}, query {compound}")
        if (prompts.dataset, prompts.assay) != (self.dataset, self.assay):
            raise PromptRefused("dataset_mismatch", f"{prompts.dataset}/{prompts.assay}")
        out = {}
        for p in prompts.prompts:
            if not isinstance(p, Prompt):
                raise PromptRefused("not_a_prompt", type(p).__name__)
            cond = tuple(p.condition)
            if p.compound != compound:
                raise PromptRefused("identity_mismatch", f"prompt of {p.compound}")
            if (p.dataset, p.assay) != (self.dataset, self.assay):
                raise PromptRefused("dataset_mismatch", f"{p.dataset}/{p.assay}")
            if p.step >= prompts.decision_point:
                raise PromptRefused("future_measurement", f"step {p.step} >= decision point {prompts.decision_point}")
            if cond == tuple(key):
                raise PromptRefused("target_outcome_leakage", str(cond))
            if cond not in self.keys:
                raise PromptRefused("unknown_condition", str(cond))
            if not (np.isfinite(p.quality) and 0.0 <= p.quality <= 1.0):
                raise PromptRefused("invalid_quality", str(p.quality))
            out[cond] = p
        return out

    # ------------------------------------------------------------------ kernels
    def _logkernel_v2(self, key, prompts: dict, source: str):
        if source in ("prompt", "transfer"):
            return self._logkernel(key, prompts, source)
        preds = []
        for p, prompt in prompts.items():
            pm = self.pair(p, key)
            if pm.references >= 6:
                arm = "additive" if source == "additive" else self.transfer_arm
                preds.append(pm.predict(prompt.shift, prompt.quality, arm))
        if not preds:
            return None
        combined = np.mean(preds, axis=0)          # equal weights; several prompts never occur in E2
        if source == "additive":
            return self.cosine(key, combined) - 1.0
        u, _ = self.geometry(key)
        return _dist_logk(u, combined, self.ft.tables[key].Y, self.scale(key))[0]

    def context_logkernel(self, key, prompts: dict, source: str):
        key = tuple(key)
        if not prompts:
            return None
        cache_key = ("kernel", key, source, tuple(sorted((p, pr.digest, round(float(pr.quality), 12), pr.compound, pr.row)
                                                        for p, pr in prompts.items())))
        if cache_key not in self._ic_cache:
            self._ic_cache[cache_key] = self._logkernel_v2(key, prompts, source)
        return self._ic_cache[cache_key]

    # ------------------------------------------------------------------ forecasts
    def forecast(self, key, h1, h2, compound, history=(), prompts=None) -> OutcomeForecast:
        key = tuple(key)
        usable = self.validate(key, compound, prompts)
        hp = self.incontext
        source = hp.get("source", "off")
        base = W.ReferenceWorld.forecast(self, key, h1, h2, compound, history)
        if base.refusal or not usable or source == "off" or hp.get("kappa", 0.0) <= 0.0:
            note = "incontext:off" if source == "off" or hp.get("kappa", 0.0) <= 0 else "incontext:no_prompt"
            return self._stamp2(base, note)
        cache_key = ("forecast", key, h1, h2, compound, tuple(history), prompts.identity(), source,
                     hp.get("kappa"), hp.get("tau"))
        if cache_key in self._ic_cache:
            return self._ic_cache[cache_key]
        logk = self.context_logkernel(key, usable, source)
        out = self.forecast_from_logkernel(key, h1, h2, compound, history, logk, hp, base=base,
                                           prompts=len(usable))
        self._ic_cache[cache_key] = out
        return out

    def forecast_from_logkernel(self, key, h1, h2, compound, history, logk, hp, *, base=None, prompts=0):
        """The in-context forecast for a given per-reference log-kernel (used directly by diagnostics)."""
        key = tuple(key)
        base = base or W.ReferenceWorld.forecast(self, key, h1, h2, compound, history)
        if logk is None or base.refusal or hp.get("kappa", 0.0) <= 0.0:
            return self._stamp2(base, "incontext:no_usable_prompt")
        used = history
        if self.feedback == "withheld":
            used = tuple((k, W.NONTERMINAL if lab != W.QC_FAILED else W.QC_FAILED) for k, lab in history)
        entry = self.keys[key]
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
        basis = (f"{base.basis}|incontext[{hp.get('source')},kappa={hp['kappa']:g},tau={hp['tau']:g},"
                 f"prompts={prompts},neff={'/'.join(f'{x:.2f}' for x in neff)}]")
        return OutcomeForecast(base.action_identifier, tuple(branches), basis=basis, model_version=MODEL_VERSION)

    def _stamp2(self, forecast: OutcomeForecast, note: str) -> OutcomeForecast:
        return OutcomeForecast(forecast.action_identifier, forecast.branches, basis=f"{forecast.basis}|{note}",
                               refusal=forecast.refusal, model_version=MODEL_VERSION)
