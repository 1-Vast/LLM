"""WS1 step 3d: O'Neil 2016 x NCI-ALMANAC 2017 overlap as a cross-laboratory validation source.

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws1_feedback_validation/cross_study_overlap.py
- Purpose: EXPLORATORY (both libraries exposed). Map drugs and cell lines shared by the two
  screens (explicit, hand-checked name map below), count overlapping pair x line triples,
  compare labels (different lab, assay, doses and readout: O'Neil Bliss excess on X/X0 from
  4x4 doses; ALMANAC NCI SCORE mean on 3x3 or 5x3 grids) and hit concordance, then score the
  O'Neil decomposition arms' purchases against the ALMANAC label of the same triple.
- Interfaces: run the file with PYTHONPATH="src;." [ONEIL_DECOMPOSITION_RUN].
- Depends on: numpy, research.certified_discovery.screens (frozen; load_library only).
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from research.certified_discovery.screens import CACHE, load_library  # noqa: E402

THR = 10.0
# O'Neil name -> ALMANAC first listed name (ComboCompoundNames_small.txt); hand-checked
DRUG_MAP = {
    "5-FU": "Fluorouracil", "Bortezomib": "Bortezomib", "Carboplatin": "Carboplatin",
    "Cyclophosphamide": "Cyclophosphamide", "Dasatinib": "Dasatinib", "Doxorubicin": "Doxorubicin hydrochloride",
    "Erlotinib": "Erlotinib hydrochloride", "Etoposide": "Etoposide", "Gemcitabine": "Gemcitabine hydrochloride",
    "Lapatinib": "Lapatinib ditosylate", "Methotrexate": "Methotrexate", "Mitomycine": "Mitomycin",
    "Oxaliplatin": "Oxaliplatin", "Paclitaxel": "Paclitaxel", "SN-38": "7-Ethyl-10-hydroxycamptothecin",
    "Sorafenib": "Sorafenib tosylate", "Sunitinib": "Sunitinib (free base)", "Temozolomide": "Temozolomide",
    "Topotecan": "Topotecan hydrochloride", "Vinblastine": "Vinblastine sulfate", "Vinorelbine": "Vinorelbine tartrate",
    "Zolinza": "Vorinostat",
}


def norm_line(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", name.upper().replace("/ATCC", ""))


def boot(d, seed=20261003, n=10_000):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, d.size, size=(n, d.size))
    m = d[idx].mean(axis=1)
    return [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)]


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    run = argv[0] if argv else "step2_oneil"
    on = load_library(CACHE / "oneil_v1.npz")
    al = load_library(CACHE / "almanac_v1.npz")
    al_drug = {}
    for i, n in enumerate(al.drugs):
        al_drug.setdefault(n, i)
    missing = [k for k, v in DRUG_MAP.items() if v not in al_drug or k not in on.drugs]
    o2a_drug = {on.drugs.index(k): al_drug[v] for k, v in DRUG_MAP.items() if k not in missing}
    al_lines = {norm_line(n): i for i, n in enumerate(al.lines)}
    o2a_line = {i: al_lines[norm_line(n)] for i, n in enumerate(on.lines) if norm_line(n) in al_lines}
    al_index = {(int(a), int(b), int(c)): k for k, (a, b, c) in enumerate(zip(al.a, al.b, al.c))}
    pairs = []
    for k in range(len(on)):
        a, b, c = int(on.a[k]), int(on.b[k]), int(on.c[k])
        if a in o2a_drug and b in o2a_drug and c in o2a_line:
            x, y = sorted((o2a_drug[a], o2a_drug[b]))
            j = al_index.get((x, y, o2a_line[c]))
            if j is not None:
                pairs.append((k, j))
    pairs = np.array(pairs)
    yo, ya = on.y[pairs[:, 0]], al.y[pairs[:, 1]]
    ho, ha = yo > THR, ya > THR
    rank = lambda v: np.argsort(np.argsort(v))
    out = {
        "exposure": "EXPLORATORY: both libraries exposed",
        "drugs_mapped": len(o2a_drug), "drugs_missing": missing,
        "lines_mapped": {on.lines[i]: al.lines[j] for i, j in o2a_line.items()},
        "overlapping_triples": int(len(pairs)),
        "overlapping_pairs": int(np.unique(on.a[pairs[:, 0]] * 100 + on.b[pairs[:, 0]]).size),
        "pearson": float(np.corrcoef(yo, ya)[0, 1]), "spearman": float(np.corrcoef(rank(yo), rank(ya))[0, 1]),
        "hit_rate_oneil": float(ho.mean()), "hit_rate_almanac": float(ha.mean()),
        "almanac_hit_given_oneil_hit": float(ha[ho].mean()) if ho.any() else None,
        "oneil_hit_given_almanac_hit": float(ho[ha].mean()) if ha.any() else None,
        "both_hits": int((ho & ha).sum()), "oneil_hits": int(ho.sum()), "almanac_hits": int(ha.sum()),
    }
    # pair-level (averaged over shared lines) agreement: is cross-study signal pair-generic?
    pair_key = on.a[pairs[:, 0]] * 100 + on.b[pairs[:, 0]]
    pm_o = {p: yo[pair_key == p].mean() for p in np.unique(pair_key)}
    pm_a = {p: ya[pair_key == p].mean() for p in np.unique(pair_key)}
    ks = sorted(pm_o)
    out["pair_mean_pearson"] = float(np.corrcoef([pm_o[p] for p in ks], [pm_a[p] for p in ks])[0, 1])
    ro = yo - np.array([pm_o[p] for p in pair_key])
    ra = ya - np.array([pm_a[p] for p in pair_key])
    out["within_pair_line_specific_pearson"] = float(np.corrcoef(ro, ra)[0, 1])
    # join O'Neil arms' purchases to the ALMANAC label of the same triple
    amap = {int(k): float(al.y[j]) for k, j in pairs}
    lines = [json.loads(x) for x in open(HERE / "receipts" / run / "lines.jsonl", encoding="utf-8")]
    per_line, totals = defaultdict(dict), {}
    for arm in sorted(lines[0]["arms"]):
        tot = defaultdict(float)
        for l in lines:
            rows = np.array(l["rows"])
            entries = l["arms"][arm] if isinstance(l["arms"][arm], list) else [l["arms"][arm]]
            acc = defaultdict(float)
            for ent in entries:
                bought = [int(b) for b in rows[[i for r in ent["purchases"] for i in r]] if int(b) in amap]
                acc["bought_overlap"] += len(bought)
                acc["oneil_hits"] += sum(on.y[b] > THR for b in bought)
                acc["almanac_hits"] += sum(amap[b] > THR for b in bought)
                acc["both_hits"] += sum(on.y[b] > THR and amap[b] > THR for b in bought)
            for k in acc:
                acc[k] = float(acc[k]) / len(entries)
                tot[k] += acc[k]
            per_line[arm][l["line"]] = dict(acc)
        totals[arm] = {k: round(v, 2) for k, v in tot.items()}
    out["arms_on_overlap"] = totals
    names = [on.lines[i] for i in o2a_line]
    contr = {}
    for a, b in (("full_mean", "static_mean"), ("full_mean", "history"), ("full_mean", "gbm_static")):
        for metric in ("oneil_hits", "almanac_hits", "both_hits"):
            d = np.array([per_line[a][n].get(metric, 0) - per_line[b][n].get(metric, 0) for n in names])
            contr[f"{a} - {b} : {metric}"] = {"sum": round(float(d.sum()), 2), "mean": round(float(d.mean()), 3), "ci": boot(d)}
    out["contrasts_on_overlap"] = contr
    (HERE / "receipts" / "step3_cross_study_overlap.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "arms_on_overlap"}, indent=1))
    for k, v in totals.items():
        print(f"{k:24s}", v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
