"""Development domain: PRISM 19Q4 primary screen as a cell-line x compound matrix.

File summary
- Path: research/context_transfer_20261017/data_prism.py
- Purpose: build (once) and load the development domain used to design the method.
- Core points:
  - Y: replicate-collapsed log2 fold change at 2.5 uM; columns sharing a Broad core are averaged
    (they are dependent releases of one compound, not independent experiments).
  - Contexts: lines with a DepMap ID that passed STR profiling. Groups: primary tissue.
  - X: DepMap 19Q4 CCLE basal expression (log2 TPM+1), a pre-treatment feature only. Lines
    without expression keep NaN rows and fall back to the context-free prior in every arm.
  - The endpoint uses the PRISM absolute gate log2 FC <= -1 and >= 100 measured lines.
- Interfaces: `load()` -> dict(Y, X, events, G, contexts, items, groups, item_names, item_moa).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import CACHE, DEPMAP, PRISM_RAW, selective_events, sha256

ABS_GATE = -1.0
MIN_MEASURED = 100
CACHE_FILE = CACHE / "prism_domain.npz"
INPUTS = [
    PRISM_RAW / "primary-screen-replicate-collapsed-logfold-change.csv",
    PRISM_RAW / "primary-screen-replicate-collapsed-treatment-info.csv",
    PRISM_RAW / "primary-screen-cell-line-info.csv",
    DEPMAP / "CCLE_expression.csv",
]


def build() -> dict:
    lfc = pd.read_csv(INPUTS[0], index_col=0)
    info = pd.read_csv(INPUTS[1])
    cells = pd.read_csv(INPUTS[2])
    cells = cells[cells.depmap_id.notna() & (cells.passed_str_profiling.astype(str).str.upper() == "TRUE")]
    rows = [r for r in cells.row_name.astype(str) if r in lfc.index]
    cells = cells.set_index("row_name").loc[rows]
    lfc = lfc.loc[rows]
    info = info.set_index("column_name").loc[lfc.columns]
    core = info.broad_id.astype(str).str[:13]
    Yc = lfc.T.groupby(core.values).mean().T            # lines x cores
    meta = info.assign(core=core.values).groupby("core").first()
    items = Yc.columns.to_numpy()
    Y = Yc.to_numpy(dtype=float)

    expr = pd.read_csv(INPUTS[3], index_col=0)
    X = np.full((len(rows), expr.shape[1]), np.nan, dtype=np.float32)
    have = [i for i, d in enumerate(cells.depmap_id) if d in expr.index]
    X[have] = expr.loc[cells.depmap_id.iloc[have]].to_numpy(dtype=np.float32)

    events, G = selective_events(Y, ABS_GATE, MIN_MEASURED)
    out = {
        "Y": Y.astype(np.float32),
        "X": X,
        "genes": np.array(expr.columns.astype(str)),
        "events": events,
        "G": G,
        "contexts": np.array(cells.depmap_id.astype(str)),
        "groups": np.array(cells.primary_tissue.astype(str)),
        "items": items.astype(str),
        "item_names": meta.loc[items, "name"].astype(str).to_numpy(),
        "item_moa": meta.loc[items, "moa"].astype(str).to_numpy(),
        "input_sha256": np.array([sha256(p) for p in INPUTS]),
    }
    out = {k: (np.asarray(v).astype(str) if np.asarray(v).dtype == object else v) for k, v in out.items()}
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE_FILE, **out)
    return out


def load() -> dict:
    if not CACHE_FILE.exists():
        return build()
    z = np.load(CACHE_FILE, allow_pickle=False)
    return {k: z[k] for k in z.files}


if __name__ == "__main__":
    d = build()
    Y, ev = d["Y"], d["events"]
    has_x = np.isfinite(d["X"][:, 0])
    print("contexts", Y.shape[0], "items", Y.shape[1], "with expression", int(has_x.sum()))
    print("finite pairs", int(np.isfinite(Y).sum()), "events", int(ev.sum()))
    per = ev.sum(1)
    print("events per context: median", float(np.median(per)), "mean", float(per.mean()),
          "zero-event contexts", int((per == 0).sum()))
    print("groups", len(set(d["groups"].tolist())))
