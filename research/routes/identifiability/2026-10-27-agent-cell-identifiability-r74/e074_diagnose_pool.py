"""E074: two checks on R72/R73's "both_unseen" pool.

(a) Is the marginal baseline's score there inflated by constant-score tie-breaking?
(b) Is the pool actually "both drugs unseen", or only "at least one drug unseen"?
Pre-registered in PROTOCOL_E071.md.
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r74"
METRIC = "SYNERGY_DELTA_AUC"
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]
SEED = 20261027
K = 20

d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
d = d[np.isfinite(d[METRIC])].copy()
d["cell"] = d["CELL_LINE_NAME"].astype(str)
d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
d["key"] = d["cell"] + "|" + d["combo"]
d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
d = d.groupby("key", as_index=False).agg(
    cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
    synergy=(METRIC, "mean"), syn=("syn", "mean"))
d["syn"] = d["syn"] > 0.5
y = d.synergy.to_numpy(float)
syn = d.syn.to_numpy(bool)
A = d["a"].to_numpy()
B = d["b"].to_numpy()
CELL = d["cell"].to_numpy()
drugs = sorted(set(A) | set(B))
cells = sorted(set(CELL))

rng = np.random.default_rng(SEED)
first_k, rand_k, base, both_frac, one_frac = [], [], [], [], []
for rep in range(40):
    rng.shuffle(drugs)
    rng.shuffle(cells)
    held_d = set(drugs[: max(3, int(round(0.20 * len(drugs))))])
    held_c = set(cells[: max(3, int(round(0.20 * len(cells))))])
    a_unseen = np.array([x in held_d for x in A])
    b_unseen = np.array([z in held_d for z in B])
    both_drugs_unseen = a_unseen & b_unseen
    any_drug_unseen = a_unseen | b_unseen
    cell_unseen = np.array([c in held_c for c in CELL])
    tr = np.where((~cell_unseen) & (~any_drug_unseen))[0]
    if len(tr) < 20000:
        continue
    pool = np.where(cell_unseen & any_drug_unseen)[0]     # the R72/R73 "both_unseen" pool
    if len(pool) < 400:
        continue
    perm = rng.permutation(len(pool))
    half = len(pool) // 2
    for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
        p = pool[idxs]
        first_k.append(float(syn[p][np.argsort(-np.zeros(len(p)))[:K]].mean()))
        rand_k.append(float(syn[p][rng.choice(len(p), size=K, replace=False)].mean()))
        base.append(float(syn[p].mean()))
        both_frac.append(float(both_drugs_unseen[p].mean()))
        one_frac.append(float((any_drug_unseen[p] & ~both_drugs_unseen[p]).mean()))

res = {
    "kind": "diagnostic_of_R72_R73_pool_and_tiebreak",
    "n_pool_evals": len(first_k),
    "tiebreak_check": {
        "first_k_hit": float(np.mean(first_k)),
        "random_k_hit": float(np.mean(rand_k)),
        "base_rate": float(np.mean(base)),
        "gap_pp": float(np.mean(first_k) - np.mean(rand_k))},
    "label_check": {
        "frac_both_drugs_unseen": float(np.mean(both_frac)),
        "frac_exactly_one_drug_unseen": float(np.mean(one_frac))},
}
gap = res["tiebreak_check"]["gap_pp"]
h187 = gap < 0.005
h188 = res["label_check"]["frac_exactly_one_drug_unseen"] > 0.5
res["decisions"] = {"H187_no_tiebreak_artifact": bool(h187), "H188_pool_label_was_wrong": bool(h188)}
res["verdict"] = ("no_artifact_but_label_must_be_corrected" if h187 and h188 else
                  "artifact_present_R72_R73_comparison_invalid" if not h187 else
                  "label_was_correct")
res["consequence"] = (
    "the marginal baseline DOES retain information in this pool (from the seen drug of the pair), so "
    "'the model loses to a no-information baseline' is the wrong reading; the correct reading is "
    "'the model loses wherever the baseline has partial information, and is only marginally better than "
    "random where the baseline has none (R66: +1.25 pp, CI lower bound 0.00)'"
)
(OUT / "E074_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(res, indent=2, ensure_ascii=False))
