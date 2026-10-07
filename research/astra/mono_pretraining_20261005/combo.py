"""Combination-history fine-tuning and scoring for one target line (no outcome access of its own).

File summary
- Path: research/astra/mono_pretraining_20261005/combo.py
- Purpose: turn the legal history of a target (rows of other lines of the tissue) into leave-one-line-out
  residual training rows, fit the shared head (`bilinear.finetune_combo`) from a given initial (W, E, beta),
  and return the learned screen score S_both-prior + g for the target's menu.
- Core points:
  - Residual of a history row = its orientation label minus the shrunk two-orientation pair mean computed on
    the OTHER history lines (a row never sees its own line in its prior); residuals are centred within each
    history line and divided by their pooled SD, so global line offsets cannot be learned.
  - The target-time prior is the contract's S_both on the full history; g (SD units rescaled to label units)
    is centred over the target's mapped pairs. Pairs with an unmapped drug (no mono label) get g = 0 and
    their history rows are excluded from every learned arm identically.
  - Both orientations are trained as ordered (anchor, library) experiments; the score uses their mean.
  - Optional `own` table: observed GDSC2 shifts of the line's own mono (ceiling arm, never deployable on
    a line without mono data).
  - Fits are cached per (arm, history tuple, config).
- Interfaces: `Fitter`, `training_rows`, `additive_scores`.
- Depends on: numpy; `bilinear`; the frozen campaign engine (`campaign.history_quantities`, `restrict`).
"""
from __future__ import annotations

import numpy as np

from research.astra.confirmation_campaign_20261004.design import campaign as c

from .bilinear import ComboConfig, finetune_combo, predict_combo

U_CLIP = 4.0


def _loo_prior(H: c.TissueData, hist_lines: list[str], row_line: np.ndarray) -> np.ndarray:
    """S_both prior of every history row computed without that row's own line."""
    prior = np.full(H.n_rows, np.nan)
    for sidm in hist_lines:
        others = [s for s in hist_lines if s != sidm]
        if not others:
            raise ValueError("leave-one-line-out prior needs at least two history lines")
        rows = np.flatnonzero(row_line == sidm)
        q = c.history_quantities(c.restrict(H, others), "SV", H.pid[rows])
        prior[rows] = q["S_both"]
    return prior


def own_shift(own: dict | None, beta: np.ndarray, sidm: str, drug_rows: np.ndarray) -> np.ndarray:
    """Observed own-mono shift u = y_rel - beta_drug (NaN where the line has no record), clipped."""
    if own is None:
        return np.full(len(drug_rows), np.nan)
    out = np.array([own.get((sidm, int(d)), np.nan) for d in drug_rows], float) - beta[drug_rows]
    return np.clip(out, -U_CLIP, U_CLIP)


def training_rows(H: c.TissueData, drug_index: dict, line_row: dict, mapped: np.ndarray) -> dict:
    """Ordered-experiment rows (mapped drug pairs only): cell row, anchor, library, centred scaled residual."""
    hist = sorted(H.present_lines)
    row_line = np.array([H.lines[int(i)] for i in H.c])
    prior = _loo_prior(H, hist, row_line)
    A = H.arrays["SV"]                       # y_s: S anchored, V library; y_v: V anchored, S library
    s = np.array([drug_index[p[0]] for p in H.pairs])
    v = np.array([drug_index[p[1]] for p in H.pairs])
    keep = mapped[s] & mapped[v]
    cell = np.array([line_row[x] for x in row_line])
    out = {"cell": [], "anchor": [], "library": [], "y": [], "line": []}
    for anchor, library, y in ((s, v, A["y_s"]), (v, s, A["y_v"])):
        out["cell"].append(cell[keep]); out["anchor"].append(anchor[keep]); out["library"].append(library[keep])
        out["y"].append((y - prior)[keep]); out["line"].append(row_line[keep])
    cat = {k: np.concatenate(v) for k, v in out.items()}
    for sidm in hist:                        # centre within line, both orientations pooled
        m = cat["line"] == sidm
        cat["y"][m] = cat["y"][m] - cat["y"][m].mean()
    cat["scale"] = float(max(cat["y"].std(), 1e-6))
    cat["y"] = cat["y"] / cat["scale"]
    return cat


class Fitter:
    """Caches fitted heads; `init` is the starting parameter dict (pretrained, scratch or permuted)."""

    def __init__(self, z: np.ndarray, drug_index: dict, line_row: dict, mapped: np.ndarray, own: dict | None = None):
        self.z, self.drug_index, self.line_row, self.mapped, self.own = z, drug_index, line_row, mapped, own
        self._cache: dict = {}

    def _uo(self, params, rows: dict):
        if self.own is None:
            return None
        sid = {v: k for k, v in self.line_row.items()}
        uo_a = np.array([own_shift(self.own, params["beta"], sid[int(ci)], np.array([a]))[0]
                         for ci, a in zip(rows["cell"], rows["anchor"])])
        uo_b = np.array([own_shift(self.own, params["beta"], sid[int(ci)], np.array([b]))[0]
                         for ci, b in zip(rows["cell"], rows["library"])])
        return uo_a, uo_b

    def fit(self, arm: str, init: dict, H: c.TissueData, cfg: ComboConfig) -> dict:
        key = (arm, H.tissue, tuple(sorted(H.present_lines)), cfg)
        if key not in self._cache:
            rows = training_rows(H, self.drug_index, self.line_row, self.mapped)
            p = finetune_combo(init, self.z, rows["cell"], rows["anchor"], rows["library"], rows["y"], cfg,
                               uo=self._uo(init, rows))
            p["scale"] = rows["scale"]
            self._cache[key] = p
        return self._cache[key]

    def target_score(self, params: dict, full: c.TissueData, tg: c.Target) -> np.ndarray:
        """Screen score of the target's menu: contract S_both prior + centred g (mean of both orientations)."""
        pairs = [full.pairs[i] for i in tg.rows]
        s = np.array([self.drug_index[p[0]] for p in pairs])
        v = np.array([self.drug_index[p[1]] for p in pairs])
        cell = np.full(len(pairs), self.line_row[tg.sidm])
        uo1 = uo2 = None
        if self.own is not None:
            ua = own_shift(self.own, params["beta"], tg.sidm, s)
            ub = own_shift(self.own, params["beta"], tg.sidm, v)
            uo1, uo2 = (ua, ub), (ub, ua)
        g = (predict_combo(params, self.z, cell, s, v, uo1) + predict_combo(params, self.z, cell, v, s, uo2)) / 2.0
        ok = self.mapped[s] & self.mapped[v]
        g = np.where(ok, g - g[ok].mean(), 0.0) * params["scale"]
        return tg.q["S_both"] + g


def additive_scores(H: c.TissueData, full_pairs: list, target_pid: np.ndarray, k0: float = 2.0) -> np.ndarray:
    """D_add: additive S-drug + V-drug effects on the two-orientation mean, shrunk, from the same history."""
    A = H.arrays["SV"]
    y = (A["y_s"] + A["y_v"]) / 2.0
    s = np.array([p[0] for p in H.pairs]); v = np.array([p[1] for p in H.pairs])
    mu = y.mean()
    a_eff, b_eff = {}, {}
    for _ in range(5):
        r = y - mu - np.array([b_eff.get(x, 0.0) for x in v])
        a_eff = {d: r[s == d].sum() / ((s == d).sum() + k0) for d in set(s)}
        r = y - mu - np.array([a_eff.get(x, 0.0) for x in s])
        b_eff = {d: r[v == d].sum() / ((v == d).sum() + k0) for d in set(v)}
    return np.array([mu + a_eff.get(p[0], 0.0) + b_eff.get(p[1], 0.0) for p in full_pairs])
