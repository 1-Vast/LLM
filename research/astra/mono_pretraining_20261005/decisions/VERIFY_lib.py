"""Independent harness for the phase-2 verification (agent C). Re-implements scores, units and statistics.

File summary
- Path: research/astra/mono_pretraining_20261005/decisions/VERIFY_lib.py
- Purpose: load the HD Jaaks outcomes through the frozen builder with E outcomes masked at the moment of loading,
  and provide independent implementations of fold assignment, histories, simple rankings, D_add and the
  line bootstrap. Imports only the frozen campaign engine, the frozen builder and `common.history_draw` (allowed).
- E handling: the builder's `_read` is wrapped so that, immediately after the CSV is parsed and before any
  computation, every outcome column of rows whose SIDM is in the E partition is overwritten by a constant that
  passes QC. The E rows stay in the frame only so that line indices (tie-break) are unchanged; no E outcome value
  survives the read. `assert_e_masked` proves it on the loaded panels.
- Access log: decisions/VERIFY_access_log.jsonl (own file; the study's access_log.jsonl is not written).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from research.astra.confirmation_campaign_20261004.design import campaign as c
from research.astra.feedback_validation_20261003 import jaaks as jk
from tools.datasets.combination_screens import open_vault

ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
PARTITION = ROOT / "research/astra/confirmation_campaign_20261004/protocol/partition.json"
FREEZE = STUDY / "FREEZE.json"
LOG = HERE / "VERIFY_access_log.jsonl"
SEED = 20261005
N_FOLDS = 5
TCODE = {"Breast": 1, "Colon": 2, "Pancreas": 3}
SIMPLE = ("S_both", "L_v", "C_s", "C_v", "C_mean", "C_prod")


def split() -> dict:
    return json.loads(PARTITION.read_text(encoding="utf-8"))["split"]


def my_fold_of(sp: dict) -> dict:
    """Independent re-implementation of the frozen fold rule (hashed permutation of sorted HD lines)."""
    out = {}
    for tissue, parts in sp.items():
        for s in parts["E"]:
            out[s] = (tissue, "E")
        hd = sorted(parts["HD"])
        perm = np.random.default_rng([SEED, TCODE[tissue]]).permutation(len(hd))
        for rank, i in enumerate(perm):
            out[hd[i]] = (tissue, int(rank % N_FOLDS))
    return out


def load_hd(purpose: str):
    """(tissues, report) with E outcomes masked at load time."""
    sp = split()
    e_sidms = {s for t in sp.values() for s in t["E"]}
    ticket = open_vault(FREEZE, LOG, purpose=purpose, source=jk.RELEASE, root=ROOT)
    orig = jk._read

    def masked(path, columns):
        df = orig(path, columns)
        m = df["SIDM"].isin(e_sidms).to_numpy()
        n_e = int(m.sum())
        for col, val in (("SYNERGY_DELTA_EMAX", 0.0), ("SYNERGY_OBS_EMAX", 0.5), ("SYNERGY_RMSE", 0.1),
                         ("LIBRARY_RMSE", 0.1)):
            if col in df.columns:
                df.loc[m, col] = val
        if "Synergy" in df.columns:
            df["Synergy"] = df["Synergy"].astype(object)
            df.loc[m, "Synergy"] = "FALSE"
        masked.n_e_rows = n_e
        return df

    jk._read = masked
    try:
        panels, report, cand = jk.build_panels(ticket, path=jk.RELEASE)
    finally:
        jk._read = orig
    tissues = c.build_tissues(panels, cand)
    report = dict(report, e_rows_masked=masked.n_e_rows)
    return tissues, report, sp, e_sidms


def assert_e_masked(tissues, e_sidms) -> dict:
    """All E rows carry the constant sentinel (y = 0, no hit)."""
    out = {}
    for t, T in tissues.items():
        idx = [T.lines.index(s) for s in e_sidms if s in T.lines]
        m = np.isin(T.c, idx)
        for role in ("SV", "VS"):
            A = T.arrays[role]
            assert np.all(A["y_s"][m] == 0.0) and np.all(A["y_v"][m] == 0.0), "E label survived"
            assert not A["h_s"][m].any() and not A["h_v"][m].any(), "E call survived"
        out[t] = int(m.sum())
    return out


def units(sp, fold, history_draw, n_draws=10, n_hist=4):
    """Independent re-implementation of run_s2.units for the dev phase."""
    out = []
    for tissue in sp:
        hd = sorted(sp[tissue]["HD"]); ev = sorted(sp[tissue]["E"])
        for k in range(N_FOLDS):
            targets = [s for s in hd if fold[s][1] == k]
            allowed = [s for s in hd if fold[s][1] != k]
            forbidden = sorted(set(targets) | set(ev))
            for d in range(n_draws):
                out.append(dict(tissue=tissue, fold=k, draw=d, hist=history_draw(TCODE[tissue], k, d, allowed, n_hist),
                                targets=targets, allowed=allowed, forbidden=forbidden))
    return out


def shrunk(pid_hist: np.ndarray, z: np.ndarray, pid_target: np.ndarray, k0: float = 2.0) -> np.ndarray:
    """Per-pair mean of z over history rows shrunk towards the pooled mean: (sum + k0 mu) / (n + k0)."""
    mu = float(z.mean())
    size = int(max(pid_hist.max(), pid_target.max())) + 1
    s = np.bincount(pid_hist, weights=z, minlength=size)
    n = np.bincount(pid_hist, minlength=size).astype(float)
    return ((s + k0 * mu) / (n + k0))[pid_target]


def my_simple(T, hist_lines, sidm, role, pid_target):
    """Independent scores of the six simple rankings: name -> (screen score, verify score)."""
    idx = [T.lines.index(s) for s in hist_lines]
    m = np.isin(T.c, idx)
    A = T.arrays[role]
    pid = T.pid[m]
    ys, yv = A["y_s"][m], A["y_v"][m]
    hs, hv = A["h_s"][m].astype(float), A["h_v"][m].astype(float)
    sb = shrunk(pid, (ys + yv) / 2.0, pid_target)
    lv = shrunk(pid, yv, pid_target)
    ps = shrunk(pid, hs, pid_target)
    pv = shrunk(pid, hv, pid_target)
    return {"S_both": (sb, sb), "L_v": (lv, lv), "C_s": (ps, ps), "C_v": (pv, pv),
            "C_mean": ((ps + pv) / 2.0, pv), "C_prod": (ps * pv, pv)}


def line_bootstrap(diff_by_line: dict, tissue_of: dict, n=10_000, seed=20261004, base_by_line=None):
    """Registered tissue-stratified line bootstrap of the mean (and ratio of sums when base is given)."""
    rng = np.random.default_rng(seed)
    groups = {}
    for k in sorted(diff_by_line):
        groups.setdefault(tissue_of[k], []).append(k)
    arrs = {t: np.array([diff_by_line[k] for k in ks]) for t, ks in groups.items()}
    bas = None if base_by_line is None else {t: np.array([base_by_line[k] for k in ks]) for t, ks in groups.items()}
    mean_d, rel = [], []
    for _ in range(n):
        d, b = [], []
        for t in ("Breast", "Colon", "Pancreas"):
            if t not in arrs:
                continue
            i = rng.integers(0, len(arrs[t]), len(arrs[t]))
            d.append(arrs[t][i])
            if bas is not None:
                b.append(bas[t][i])
        d = np.concatenate(d)
        mean_d.append(d.mean())
        if bas is not None:
            bb = np.concatenate(b)
            rel.append(d.sum() / bb.sum() if bb.sum() != 0 else np.nan)
    allv = np.concatenate(list(arrs.values()))
    res = {"mean": float(allv.mean()), "ci": [float(x) for x in np.percentile(mean_d, [2.5, 97.5])], "n_lines": int(allv.size)}
    if bas is not None:
        res["rel_ci"] = [float(x) for x in np.nanpercentile(rel, [2.5, 97.5])]
    return res
