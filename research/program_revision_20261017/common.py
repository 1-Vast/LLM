"""Shared paths, data access, endpoint and paired statistics for the program-revision study.

File summary
- Path: research/program_revision_20261017/common.py
- Purpose: one place for what every script of this study must do identically.
- Core points:
  - Domain: PRISM Repurposing 19Q4 secondary screen, screen HTS002, experimental treatments at
    2.5 uM with all three replicate detection plates (X1, X2, X3). One column per Broad core: the
    lexicographically first (broad_id, compound_plate, well) having X1-X3, as in the anchor study.
  - Lines: STR-passing, in the HTS002 pooling table, with a DepMap 19Q4 expression row and a
    mutation record. Cell features (lineage, hotspot panel, expression) are pre-treatment data.
  - Measurement units: one probe = one well = (compound, 2.5 uM, X1 plate, one cell pool) and
    reads every line of that pool; for a single new line a probe is one single-line well. One
    confirmation = the X2 and X3 readouts of one (compound, line) pair = 2 wells.
  - Endpoint (frozen): a qualified hit is a pair whose available confirmation replicates (X2,
    X3; at least one) are all < 0, whose mean m <= -1, and m <= (drug median of m over SOURCE
    lines) - 1. It is a technical criterion for context-specific strong response, not independent
    biological confirmation, selectivity over normal cells or a mechanism. A pair with neither X2
    nor X3 is unknown, never inactive. (Stage A decision: requiring both replicates left 38% of
    pairs unknown; see STAGE_A.json.)
  - Responses are read only by `load_responses`; the split builder never calls it.
- Interfaces: paths, `write_json`, `read_json`, `sha256`, `lf_digest`, `load_treatments`,
  `load_lines`, `load_responses`, `qualified_hits`, `paired`, `holm`, `hash_unit`.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = ROOT / "data" / "external" / "prism_19q4" / "raw"
DEPMAP = ROOT / "data" / "external" / "depmap_19q4"
CACHE = ROOT / "tmp" / "program_revision_20261017"
TREAT = RAW / "secondary-screen-replicate-treatment-info.csv"
LFC = RAW / "secondary-screen-logfold-change.csv"
CELLS = RAW / "secondary-screen-cell-line-info.csv"
POOLS = RAW / "secondary-screen-pooling-info.csv"
EXPR = DEPMAP / "CCLE_expression.csv"
MUT = DEPMAP / "CCLE_mutations.csv"
SAMPLE = DEPMAP / "sample_info.csv"
SEED = 20261017
DOSE = 2.5
SCREEN = "HTS002"


def write_json(path, data) -> None:
    """LF bytes, so a digest does not depend on the platform."""

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes((json.dumps(data, indent=1, default=_plain, allow_nan=False) + "\n").encode("utf-8"))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _plain(x):
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, (set, tuple)):
        return sorted(x) if isinstance(x, set) else list(x)
    raise TypeError(type(x))


def sha256(path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def lf_digest(path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def hash_unit(items, salt: str) -> np.ndarray:
    """Deterministic U(0,1) per item from a salted SHA-256 (platform independent)."""

    out = []
    for item in items:
        h = hashlib.sha256(f"{salt}:{item}".encode("utf-8")).hexdigest()
        out.append(int(h[:13], 16) / float(1 << 52))
    return np.array(out)


def load_treatments():
    """HTS002 2.5 uM experimental treatments with X1-X3, one column triple per Broad core."""

    import pandas as pd

    info = pd.read_csv(TREAT)
    e = info[(info.perturbation_type == "experimental_treatment") & (info.screen_id == SCREEN)
             & np.isclose(info.dose, DOSE, atol=0.01)].copy()
    e["core"] = e.broad_id.str[:13]
    e["rep"] = e.detection_plate.str.extract(r"_(X\d)")[0]
    rows = []
    for core, g in e.groupby("core"):
        g = g.sort_values(["broad_id", "compound_plate", "well", "rep"])
        for (bid, plate, well), h in g.groupby(["broad_id", "compound_plate", "well"], sort=True):
            reps = dict(zip(h.rep, h.column_name))
            if {"X1", "X2", "X3"} <= set(reps):
                first = h.iloc[0]
                rows.append(dict(core=core, broad_id=bid, compound_plate=plate, well=well,
                                 name=first["name"], moa=first.moa, target=first.target,
                                 smiles=first.smiles, phase=first.phase,
                                 x1=reps["X1"], x2=reps["X2"], x3=reps["X3"]))
                break
    return pd.DataFrame(rows).sort_values("core").reset_index(drop=True)


def load_lines():
    """Eligible lines with lineage and pool; feature availability only (no responses)."""

    import pandas as pd

    cells = pd.read_csv(CELLS)
    pools = pd.read_csv(POOLS)
    pools = pools[pools.screen_id == SCREEN][["row_name", "pool_id"]]
    expr_ids = pd.read_csv(EXPR, usecols=[0]).iloc[:, 0].astype(str)
    mut_ids = pd.read_csv(MUT, usecols=["DepMap_ID"]).DepMap_ID.astype(str).unique()
    c = cells[cells.passed_str_profiling.astype(str).str.upper() == "TRUE"].merge(pools, on="row_name")
    c = c[c.depmap_id.isin(set(expr_ids)) & c.depmap_id.isin(set(mut_ids))]
    c = c.drop_duplicates("depmap_id").sort_values("depmap_id").reset_index(drop=True)
    return c[["row_name", "depmap_id", "ccle_name", "primary_tissue", "secondary_tissue", "pool_id"]]


def load_responses(treat, lines, use_cache: bool = True):
    """Replicate log2 fold change arrays X1, X2, X3 with shape (drugs, lines); NaN = unknown."""

    import pandas as pd

    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(("|".join(treat.x1) + "#" + "|".join(lines.row_name)).encode()).hexdigest()[:16]
    path = CACHE / f"responses_{key}.npz"
    if use_cache and path.exists():
        z = np.load(path, allow_pickle=False)
        if z["lfc_sha256"].item() == sha256(LFC):
            return z["X1"], z["X2"], z["X3"]
    cols = set(treat.x1) | set(treat.x2) | set(treat.x3)
    first = pd.read_csv(LFC, nrows=0).columns[0]
    m = pd.read_csv(LFC, usecols=lambda c: c == first or c in cols, index_col=0)
    m = m.reindex(lines.row_name)
    # A treatment column absent from the matrix is a replicate removed upstream: unknown, never inactive.
    X = [m.reindex(columns=list(treat[r])).to_numpy(float).T for r in ("x1", "x2", "x3")]
    np.savez_compressed(path, X1=X[0], X2=X[1], X3=X[2], lfc_sha256=np.array(sha256(LFC)))
    return X[0], X[1], X[2]


def qualified_hits(X2, X3, line_mask=None):
    """Frozen endpoint. Returns (hit, known): boolean arrays (drugs, lines).

    ``known`` is False only where both X2 and X3 are missing. The drug median uses all eligible lines
    (``line_mask`` restricts which lines enter the median; default all).
    """

    known = np.isfinite(X2) | np.isfinite(X3)
    with np.errstate(all="ignore"):
        m = np.where(known, np.nanmean(np.stack([X2, X3]), 0), np.nan)
        cols = np.ones(m.shape[1], bool) if line_mask is None else np.asarray(line_mask, bool)
        med = np.nanmedian(m[:, cols], axis=1)
    neg = np.where(np.isfinite(X2), X2 < 0, True) & np.where(np.isfinite(X3), X3 < 0, True)
    hit = known & neg & (m <= -1.0) & (m <= med[:, None] - 1.0)
    return hit, known


def holm(ps: dict) -> dict:
    keys = sorted(ps, key=lambda k: ps[k])
    m = len(keys)
    adj, running = {}, 0.0
    for i, k in enumerate(keys):
        running = max(running, min(1.0, (m - i) * ps[k]))
        adj[k] = running
    return adj


def paired(diff, groups, draws: int = 10000, boot: int = 2000, seed: int = SEED) -> dict:
    """Paired comparison over units with clusters (same estimator as feedback_attribution).

    Mean of per-unit differences; cluster bootstrap 95% interval (clusters resampled with
    replacement, units kept intact); one-sided sign-flip p over cluster means (mean > 0).
    """

    d = np.asarray(diff, dtype=float)
    groups = np.asarray(groups)
    labels = sorted(set(groups.tolist()))
    index = [np.flatnonzero(groups == g) for g in labels]
    rng = np.random.default_rng(seed)
    sums = np.array([d[i].sum() for i in index])
    sizes = np.array([len(i) for i in index])
    picks = rng.integers(0, len(labels), size=(boot, len(labels)))
    boots = sums[picks].sum(1) / sizes[picks].sum(1)
    cm = sums / sizes
    signs = rng.choice([-1.0, 1.0], size=(draws, len(labels)))
    w = sizes / sizes.sum()
    obs = float((cm * w).sum())
    null = (signs * cm * w).sum(1)
    p = float((1 + (null >= obs - 1e-12).sum()) / (draws + 1))
    return {
        "n_units": int(len(d)),
        "n_clusters": int(len(labels)),
        "mean": float(d.mean()),
        "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
        "p_one_sided": p,
        "positive_units": int((d > 0).sum()),
        "negative_units": int((d < 0).sum()),
    }
