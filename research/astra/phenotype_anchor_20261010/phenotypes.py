"""Same-well phenotype tables from obs codes: relative survival and cell-cycle shifts.

Definitions follow the Tahoe-100M Cell (2026) phenotypes, adapted to what this filtered release
identifies (see PROTOCOL.md section 2):

* relative survival  = log2 of a line's share of the spheroid (denominator: reference lines only)
                       minus the same quantity in the same plate's DMSO spheroids. Absolute counts
                       are not identifiable: well totals do not replicate (development check).
* phase log-odds     = logit(p_phase | treated well) - logit(p_phase | same-plate DMSO), for
                       phase in {G1, S, G2M}; positive G1 = accumulation in G1.

Every quantity is keyed by (line file, condition label, plate). No expression value is read.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / "data/external/tahoe_phenotype_20261010/obs"
HELDOUT = ("c12.h5ad", "c20.h5ad", "c26.h5ad", "c27.h5ad", "c31.h5ad")
DMSO = "[('DMSO_TF', 0.0, 'uM')]"
PHASES = ("G1", "S", "G2M")
PSEUDO = 0.5


def load_counts(files):
    """Return {(file, label, plate): {"n": int, "G1": int, "S": int, "G2M": int}} and line names."""
    table, names = {}, {}
    for name in files:
        receipt = json.loads((HERE / "obs" / f"{name}.json").read_text(encoding="utf-8"))
        names[name] = receipt["cell_name"][0]
        z = np.load(CACHE / f"{name}.npz")
        cats = receipt["categories"]
        lab = np.asarray(cats["drugname_drugconc"])
        pla = np.asarray(cats["plate"])
        pha = np.asarray(cats["phase"])
        key = z["drugname_drugconc"].astype(np.int64) * 64 + z["plate"].astype(np.int64)
        phase_idx = {p: int(np.where(pha == p)[0][0]) for p in PHASES}
        uniq, inv = np.unique(key, return_inverse=True)
        n = np.bincount(inv)
        per_phase = {p: np.bincount(inv, weights=(z["phase"] == code)).astype(np.int64) for p, code in phase_idx.items()}
        for i, k in enumerate(uniq):
            table[(name, str(lab[k // 64]), str(pla[k % 64]))] = {"n": int(n[i]), **{p: int(per_phase[p][i]) for p in PHASES}}
    return table, names


def logit(k, n):
    return np.log((k + PSEUDO) / (n - k + PSEUDO))


def phenotype_frame(table, files, denominator_files):
    """Per (file, label, plate) relative survival and phase log-odds shifts versus same-plate DMSO."""
    wells = defaultdict(dict)
    for (f, lab, pl), row in table.items():
        wells[(lab, pl)][f] = row
    denom = {w: sum(v[f]["n"] for f in denominator_files if f in v) for w, v in wells.items()}
    out = {}
    for (lab, pl), v in wells.items():
        if lab == DMSO or (DMSO, pl) not in wells:
            continue
        base = wells[(DMSO, pl)]
        for f in files:
            if f not in v or f not in base:
                continue
            row, b = v[f], base[f]
            share = np.log2((row["n"] + PSEUDO) / denom[(lab, pl)]) - np.log2((b["n"] + PSEUDO) / denom[(DMSO, pl)])
            rec = {"survival": float(share), "n": row["n"], "n_dmso": b["n"]}
            for p in PHASES:
                rec[p] = float(logit(row[p], row["n"]) - logit(b[p], b["n"]))
            out[(f, lab, pl)] = rec
    return out
