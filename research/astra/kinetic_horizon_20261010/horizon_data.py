"""Early (Tahoe 24 h, same spheroid) and late (PRISM 5 day) panels for the kinetic-horizon study.

Early readouts per (line, 5 uM drug), plate-mean over the label's plates, each relative to the
same plate's DMSO spheroid of that line:
* ``s24``  relative survival (log2 spheroid share; denominator = 40 count-qualified reference lines)
* ``k24``  kinetic slowdown log2(rho): phase fractions -> phase-duration shares u_k = T_k / T_c of an
           asynchronous exponentially growing population (age density ~ 2^(-a/T_c)); with
           lengthening-only drug action the minimal cycle slowdown is rho = min_k u'_k / u_k
* ``g24``  signed G1 log-odds shift (the readout of phenotype_anchor_20261010)
Selectivity = value minus the mean over the 40 reference lines (Tahoe panel, as before).

Late readout: PRISM primary log2 fold change at 2.5 uM (5 days), from ``prism_<tier>.npz``.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PA = ROOT / "research/astra/phenotype_anchor_20261010"
sys.path.insert(0, str(PA))
import analysis as A  # noqa: E402
import phenotypes as P  # noqa: E402

DATA = ROOT / "data/external/kinetic_horizon_20261010"
PS = 0.5
DOSE = 5.0


def duration_shares(g1, s, g2m):
    """Phase counts -> (u_G1, u_S, u_G2M), the phase-duration shares of the cycle."""
    g1, s, g2m = (np.asarray(x, dtype=float) for x in (g1, s, g2m))
    n = g1 + s + g2m + 3 * PS
    f1, f2 = (g1 + PS) / n, (s + PS) / n
    u1 = -np.log2(1 - f1 / 2)
    u12 = -np.log2(1 - (f1 + f2) / 2)
    return np.stack([u1, u12 - u1, 1 - u12], -1)


def log_rho_from_fractions(ft: np.ndarray, fb: np.ndarray) -> np.ndarray:
    """Fractions (..., 3) for treated and DMSO -> log2 minimal slowdown (<= 0 up to noise)."""
    def u(f):
        f1, f2 = f[..., 0], f[..., 1]
        u1 = -np.log2(1 - f1 / 2)
        u12 = -np.log2(1 - (f1 + f2) / 2)
        return np.stack([u1, u12 - u1, 1 - u12], -1)
    return np.log2((u(ft) / u(fb)).min(-1))


def kinetic(t: dict, b: dict) -> float:
    ut = duration_shares(t["G1"], t["S"], t["G2M"])
    ub = duration_shares(b["G1"], b["S"], b["G2M"])
    return float(np.log2((ut / ub).min()))


@dataclass
class Early:
    files: list
    names: dict
    drugs: list          # Tahoe drug names (5 uM labels)
    s24: np.ndarray      # lines x drugs, raw (not centred)
    k24: np.ndarray
    g24: np.ndarray
    n: np.ndarray        # treated cells summed over plates


def early_panel(files: list, reference: list | None = None) -> Early:
    """Raw early readouts for ``files``; the survival denominator uses the 40 qualified references."""
    keep, info = A.qualified_reference()
    reference = reference or keep
    table, names = P.load_counts(sorted(set(files) | set(reference)))
    frame = P.phenotype_frame(table, files, reference)
    labels = sorted({k[1] for k in frame if A.dose_of(k[1]) == DOSE})
    drugs = [A.drug_of(l) for l in labels]
    li = {l: i for i, l in enumerate(labels)}
    fi = {f: i for i, f in enumerate(files)}
    shape = (len(files), len(labels))
    acc = {}
    for (f, lab, pl), rec in frame.items():
        if lab in li:
            k = kinetic(table[(f, lab, pl)], table[(f, P.DMSO, pl)])
            acc.setdefault((f, lab), []).append((rec["survival"], k, rec["G1"], rec["n"]))
    s24, k24, g24, n = (np.full(shape, np.nan) for _ in range(4))
    for (f, lab), v in acc.items():
        v = np.array(v)
        i, j = fi[f], li[lab]
        s24[i, j], k24[i, j], g24[i, j], n[i, j] = v[:, 0].mean(), v[:, 1].mean(), v[:, 2].mean(), v[:, 3].sum()
    return Early(files, {f: names[f] for f in files}, drugs, s24, k24, g24, n)


def load_late(tier: str) -> dict:
    z = np.load(DATA / f"prism_{tier}.npz", allow_pickle=False)
    out = {k: z[k] for k in z.files}
    z.close()
    return out


def split() -> dict:
    return json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
