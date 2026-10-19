"""Heavy-tail RSD arena: the frozen RSD arena (compounds, roles, reference purges, replicate roles) with HTS002 reads at a
chosen dose.

File summary
- Compounds, families, clusters, roles and per-block reference purges come unchanged from the frozen
  `replicate_decisions_20261019/rsd_data.build_arena` (metadata only; 2.5 uM compound set).
- Reads at a dose: per core, the first (broad_id, compound_plate, well) with all three detection plates X1-X3 at that dose
  (the frozen rule `rsd_data.load_treatments`, run with the dose swapped in) and the frozen salted-hash permutation of
  (X1, X2, X3) into (A = screening read, B = second read, T = truth read). Cores without a triple at the dose are dropped
  from that dose's queries and references (decided from metadata, before any read value).
- Guard: reads at any dose other than the development dose 2.5 uM are refused unless `FREEZE.json` exists in this folder.
- Cache: `cache/` in this folder (git-ignored, regenerable). Nothing is written into the frozen RSD folder.
No outcome is used to build roles; no LLM or paid call; no sealed tier.
"""
from __future__ import annotations

import contextlib
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RSD = HERE.parent / "replicate_decisions_20261019"
if str(RSD) not in sys.path:
    sys.path.insert(0, str(RSD))
import rsd_data as D  # noqa: E402  (frozen; imported, never modified)

DEV_DOSE = 2.5
TEST_DOSES = (0.625, 10.0)
CACHE = HERE / "cache"
PERMS = [("x1", "x2", "x3"), ("x1", "x3", "x2"), ("x2", "x1", "x3"), ("x2", "x3", "x1"), ("x3", "x1", "x2"), ("x3", "x2", "x1")]
_ARENA = {}


def guard(dose: float) -> None:
    if not np.isclose(dose, DEV_DOSE) and not (HERE / "FREEZE.json").exists():
        raise PermissionError(f"dose {dose} uM is the test arena; refused before FREEZE.json exists")


@contextlib.contextmanager
def _dose(dose: float):
    old = D.DOSE
    D.DOSE = dose
    try:
        yield
    finally:
        D.DOSE = old


def arena():
    """Frozen RSD arena (metadata only), cached per process."""
    if "a" not in _ARENA:
        _ARENA["a"] = D.build_arena()
    return _ARENA["a"]


def columns_at(t: pd.DataFrame, dose: float) -> pd.DataFrame:
    """Per arena compound: (colA, colB, colT) at the dose, or None if the core has no X1-X3 triple there. Metadata only."""
    with _dose(dose):
        tr = D.load_treatments().set_index("core")
    rows = []
    for c in t.core:
        if c not in tr.index:
            rows.append(dict(core=c, colA=None, colB=None, colT=None))
            continue
        p = PERMS[D.hash_int(D.SALT_ROLE, c) % 6]
        r = tr.loc[c]
        rows.append(dict(core=c, colA=r[p[0]], colB=r[p[1]], colT=r[p[2]]))
    return pd.DataFrame(rows)


def load_reads(t: pd.DataFrame, lines: pd.DataFrame, dose: float):
    """A, B, T log2FC (compounds x lines) at the dose; NaN = unknown (absent core or removed upstream), never inactive."""
    guard(dose)
    cols = columns_at(t, dose)
    key_src = f"{dose}#" + "|".join(str(x) for x in cols.colA) + "#" + "|".join(str(x) for x in cols.colB) + "#" + \
        "|".join(str(x) for x in cols.colT) + "#" + "|".join(lines.row_name)
    key = hashlib.sha256(key_src.encode()).hexdigest()[:16]
    CACHE.mkdir(exist_ok=True)
    path = CACHE / f"reads_{str(dose).replace('.', 'p')}uM_{key}.npz"
    present = cols.colA.notna().to_numpy()
    if path.exists():
        z = np.load(path, allow_pickle=False)
        return z["A"], z["B"], z["T"], present
    need = set(cols.colA.dropna()) | set(cols.colB.dropna()) | set(cols.colT.dropna())
    first = pd.read_csv(D.LFC, nrows=0).columns[0]
    m = pd.read_csv(D.LFC, usecols=lambda c: c == first or c in need, index_col=0).reindex(lines.row_name)
    out = []
    for role in ("colA", "colB", "colT"):
        X = np.full((len(t), len(lines)), np.nan)
        for i, c in enumerate(cols[role]):
            if c is not None and c in m.columns:
                X[i] = m[c].to_numpy(np.float64)
        out.append(X)
    np.savez_compressed(path, A=out[0], B=out[1], T=out[2], lfc_sha256=np.array(D.sha256(D.LFC)))
    return out[0], out[1], out[2], present


def setup(blk: str, dose: float, _reads={}):
    """Same structure as the frozen `rsd_run.setup`, at the given dose. P (primary-screen run) is None: no second run exists
    at 0.625 or 10 uM, so no cross-run truth is used in this study."""
    t, lines, Tsim, audit, E = arena()
    if dose not in _reads:
        _reads[dose] = load_reads(t, lines, dose)
    A, B, T, present = _reads[dose]
    purged = set(t.attrs["purged"][blk])
    ref = np.array([i for i in np.where(t.role == "reference")[0] if t.core[i] not in purged and present[i]])
    q = np.array([i for i in np.where(t.role == blk)[0] if present[i]])
    pools = np.unique(lines.pool_id.astype(str), return_inverse=True)[1]
    return dict(t=t, lines=lines, Tsim=Tsim, E=E, A=A, B=B, T=T, P=None, ref=ref, q=q, pools=pools, dose=dose,
                n_absent_queries=int((t.role == blk).sum() - len(q)),
                n_absent_references=int(sum(1 for i in np.where(t.role == "reference")[0]
                                            if t.core[i] not in purged and not present[i])))
