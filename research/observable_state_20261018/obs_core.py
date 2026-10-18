"""Per-family typed-edit bets: state vocabulary, episode views, search-side statistics and the held-out confirmation test.

File summary
- Path: research/observable_state_20261018/obs_core.py
- State vocabulary (closed, fixed before any proposal): for each gene in DRIVERS and in the PRISM `target` genes of the
  eligible families, `expr:<gene>` (expression above the median over panel lines) and, for DRIVERS, `mut:<gene>` (damaging or
  hotspot mutation). A variable is ADMISSIBLE for the study only if both z levels have >= MIN_LINES lines in the search
  lineages AND in the held-out lineages (line counts are metadata, not outcomes).
- Episode view: `search_view(Y, ...)` blanks every held-out lineage column and the family's own held-out compounds, so no
  proposal can depend on a held-out cell (tested by scrambling).
- Contrast: delta_d = mean(log2FC on z=1 lines) - mean(z=0 lines) per compound (>= MIN_PER_SIDE finite lines per side);
  contrast = mean over family compounds minus mean over comparator compounds F'. F' = other-family compounds of the same fold,
  purged to Tanimoto < 0.5 from every compound of the family.
- Confirmation (`confirm`): registered sign, |contrast| >= max(declared magnitude, MAG_FLOOR), one-sided family-label
  permutation p < 0.05 over F-held-out union F' (10,000 draws, seed 20261018).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import stage0_families as S0  # noqa: E402  (puts feedback_propagation on sys.path)

bench, tc = S0.bench, S0.tc
DEP = ROOT / "data/external/depmap_19q4"
PRISM = ROOT / "data/external/prism_19q4/raw"
MIN_LINES, MIN_PER_SIDE, MIN_COMPOUNDS = 8, 4, 3
MAG_FLOOR = 0.10
PERMS, SEED, ALPHA = 10000, 20261018, 0.05
DRIVERS = ["BRAF", "KRAS", "NRAS", "HRAS", "TP53", "PIK3CA", "PTEN", "EGFR", "ERBB2", "MET", "ALK", "FGFR1", "FGFR2", "FGFR3",
           "CDKN2A", "RB1", "ARID1A", "APC", "CTNNB1", "IDH1", "NF1", "NF2", "SMAD4", "STK11", "KEAP1", "NFE2L2", "MYC", "CCND1",
           "CDK4", "MDM2", "ATM", "BRCA1", "BRCA2", "SMARCA4", "KMT2D", "PIK3R1", "AKT1", "MAP2K1", "GNAS", "FBXW7"]
NONCODING = {"Silent", "Intron", "IGR", "3'UTR", "5'UTR", "5'Flank", "3'Flank", "De_novo_Start_OutOfFrame"}


def target_genes_by_core() -> dict:
    tr = pd.read_csv(PRISM / "primary-screen-replicate-collapsed-treatment-info.csv", usecols=["broad_id", "target"])
    out = {}
    for b, t in zip(tr.broad_id, tr.target):
        if isinstance(t, str):
            out.setdefault(str(b)[:13], set()).update(x.strip() for x in t.split(",") if x.strip())
    return out


@dataclass
class World:
    T: dict
    Y: np.ndarray
    names: list            # variable names
    Z: np.ndarray          # (V, L) bool state
    known: np.ndarray      # (V, L) bool state known
    held_lines: np.ndarray  # (L,) held-out lineage lines
    held_lineages: list
    admissible: np.ndarray  # (V,) bool
    fam_targets: dict      # family -> list of (gene, count)
    episodes: dict         # family -> dict(S=, H=, Fp=)


def build_world() -> World:
    T = bench.load_tables()
    held_l, held_lines = S0.lineage_split(T)
    ach = T["lines"].astype(str)
    info = json.loads((HERE / "STAGE0.json").read_text(encoding="utf-8"))
    elig = [r["family"] for r in info["families"] if r["eligible"]]
    tg = target_genes_by_core()
    # --- DepMap
    expr = pd.read_csv(DEP / "CCLE_expression.csv", index_col=0)
    expr.columns = [re.sub(r" \(.*\)$", "", c) for c in expr.columns]
    expr = expr.loc[:, ~expr.columns.duplicated()].reindex(ach)
    mut = pd.read_csv(DEP / "CCLE_mutations.csv", usecols=["Hugo_Symbol", "Variant_Classification", "DepMap_ID", "isDeleterious", "isCOSMIChotspot", "isTCGAhotspot"], low_memory=False)
    mut = mut[~mut.Variant_Classification.isin(NONCODING) & (mut.isDeleterious.astype(bool) | mut.isCOSMIChotspot.astype(bool) | mut.isTCGAhotspot.astype(bool))]
    mutated = {g: set(d.DepMap_ID) for g, d in mut.groupby("Hugo_Symbol")}
    have_mut = np.isin(ach, np.unique(pd.read_csv(DEP / "CCLE_mutations.csv", usecols=["DepMap_ID"]).DepMap_ID))
    # --- vocabulary
    fam_t, fam_targets = {}, {}
    cores = T["cores"].astype(str)
    for f in elig:
        cnt = {}
        for c in cores[T["family"] == f]:
            for g in tg.get(c, ()):
                cnt[g] = cnt.get(g, 0) + 1
        fam_targets[f] = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))
    genes_expr = sorted(set(DRIVERS) | {g for v in fam_targets.values() for g, _ in v}, key=str)
    names, Z, K = [], [], []
    for g in genes_expr:
        if g in expr.columns:
            v = expr[g].to_numpy(float)
            ok = np.isfinite(v)
            names.append(f"expr:{g}")
            Z.append(ok & (v > np.nanmedian(v)))
            K.append(ok)
    for g in DRIVERS:
        names.append(f"mut:{g}")
        Z.append(np.isin(ach, list(mutated.get(g, ()))))
        K.append(have_mut)
    Z, K = np.array(Z), np.array(K)
    Zm = Z & K
    adm = np.zeros(len(names), bool)
    for v in range(len(names)):
        ok = True
        for lines in (~held_lines, held_lines):
            n1, n0 = int((Zm[v] & lines).sum()), int((~Z[v] & K[v] & lines).sum())
            ok &= n1 >= MIN_LINES and n0 >= MIN_LINES
        adm[v] = ok
    # --- episodes
    episodes = {}
    for f in elig:
        S, H = S0.split_family(T, f)
        fold = int(T["fold"][S[0]])
        members = np.concatenate([S, H])
        pool = np.where((T["fold"] == fold) & (T["family"] != f))[0]
        sim = tc.tanimoto(T["fp"][pool], T["fp"][members]).max(1)
        episodes[f] = {"S": S, "H": H, "Fp": pool[sim < S0.SEP], "fold": fold}
    return World(T, T["Y"].astype(float), names, Z, K, held_lines, held_l, adm, fam_targets, episodes)


# ------------------------------------------------------------------ statistics
def deltas(Y, rows, v, W: World, lines_mask):
    """Per-compound state contrast delta_d for variable index v over `lines_mask`; NaN if a side has < MIN_PER_SIDE finite lines."""

    z1 = W.Z[v] & W.known[v] & lines_mask
    z0 = ~W.Z[v] & W.known[v] & lines_mask
    y = Y[rows]
    fin = np.isfinite(y)
    yz = np.where(fin, y, 0.0)
    n1, n0 = (fin & z1).sum(1), (fin & z0).sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        d = (yz * z1).sum(1) / n1 - (yz * z0).sum(1) / n0
    return np.where((n1 >= MIN_PER_SIDE) & (n0 >= MIN_PER_SIDE), d, np.nan)


def search_view(W: World, fam: str) -> np.ndarray:
    """Outcome matrix a proposer may see for family `fam`: held-out lineage columns and the family's held-out rows are blank."""

    Y = W.Y.copy()
    Y[:, W.held_lines] = np.nan
    Y[W.episodes[fam]["H"], :] = np.nan
    return Y


def delta_matrix(Y, rows, W: World, lines_mask):
    """(len(rows), V) per-compound state contrasts for every variable at once (NaN where a side has < MIN_PER_SIDE finite lines)."""

    y = Y[rows]
    fin = np.isfinite(y)
    yz = np.where(fin, y, 0.0)
    Z1 = (W.Z & W.known & lines_mask[None, :]).astype(float)
    Z0 = (~W.Z & W.known & lines_mask[None, :]).astype(float)
    n1, n0 = fin @ Z1.T, fin @ Z0.T
    with np.errstate(invalid="ignore", divide="ignore"):
        d = (yz @ Z1.T) / n1 - (yz @ Z0.T) / n0
    d = np.where((n1 >= MIN_PER_SIDE) & (n0 >= MIN_PER_SIDE), d, np.nan)
    d[:, ~W.admissible] = np.nan
    return d


def welch(dF, dC):
    """Per-variable contrast estimate, Welch t and valid counts from delta matrices (rows = compounds)."""

    with np.errstate(invalid="ignore", divide="ignore"):
        nF, nC = np.isfinite(dF).sum(0), np.isfinite(dC).sum(0)
        mF, mC = np.nanmean(dF, 0), np.nanmean(dC, 0)
        vF, vC = np.nanvar(dF, 0, ddof=1), np.nanvar(dC, 0, ddof=1)
        est = mF - mC
        t = est / np.sqrt(vF / nF + vC / nC)
    bad = (nF < 3) | (nC < 3)
    est, t = np.where(bad, np.nan, est), np.where(bad, np.nan, t)
    return est, t, nF, nC


def search_stats(W: World, fam: str, Yv=None):
    """Search-side contrast of every admissible variable (est, welch t, nF, nC) plus the delta matrices (for bootstraps)."""

    ep = W.episodes[fam]
    Yv = search_view(W, fam) if Yv is None else Yv
    lines = ~W.held_lines
    dF, dC = delta_matrix(Yv, ep["S"], W, lines), delta_matrix(Yv, ep["Fp"], W, lines)
    return (*welch(dF, dC), dF, dC)


def _oneside_p(obs, perm, sign):
    """sign=-1: evidence is a very negative contrast -> p = P(perm <= obs); sign=+1: p = P(perm >= obs)."""

    return float((perm <= obs + 1e-12).mean()) if sign < 0 else float((perm >= obs - 1e-12).mean())


def confirm(W: World, fam: str, v: int, sign: int, magnitude: float) -> dict:
    """Held-out test of one edit. sign = -1: the family is MORE sensitive (lower log2FC) when the state is on.

    Confirmed = registered sign, |contrast| >= max(magnitude, MAG_FLOOR), one-sided family-label permutation p < ALPHA.
    Fewer than MIN_COMPOUNDS valid compounds on either side -> untestable (counts as not confirmed).
    """

    ep = W.episodes[fam]
    a = deltas(W.Y, ep["H"], v, W, W.held_lines)
    b = deltas(W.Y, ep["Fp"], v, W, W.held_lines)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) < MIN_COMPOUNDS or len(b) < MIN_COMPOUNDS:
        return {"testable": False, "confirmed": False}
    obs = float(a.mean() - b.mean())
    allv = np.concatenate([a, b])
    rng = np.random.default_rng([SEED, int(hashlib.sha256(fam.encode()).hexdigest()[:8], 16)])
    idx = np.argsort(rng.random((PERMS, len(allv))), axis=1)[:, : len(a)]
    sa = allv[idx].sum(1)
    perm = sa / len(a) - (allv.sum() - sa) / len(b)
    p = _oneside_p(obs, perm, sign)
    need = max(float(magnitude), MAG_FLOOR)
    ok = bool(np.sign(obs) == sign and abs(obs) >= need and p < ALPHA)
    return {"testable": True, "contrast": obs, "p": p, "n_family": int(len(a)), "n_comparator": int(len(b)), "confirmed": ok}
