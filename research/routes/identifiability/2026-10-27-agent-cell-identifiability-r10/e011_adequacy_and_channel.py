"""E011: is the mechanism/target reference usable (H017/H018), and is the reversal
phenomenon robust to the readout channel (H019)?

Pre-registered in PROTOCOL_E011.md. Reads only files already on disk.

H017: >=50% of the analysed double-drug unit pairs have structured mechanism/target
      annotation for both compounds.
H018: >=20 such pairs share a mechanism family (enough for a same-vs-different test).
H019: switching the sign source from Viability to Raw count leaves the cross-cell
      reversal rate unchanged (|diff| <= 0.005, layout-clustered CI).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
ANN = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG_merged_drugs_with_residuals.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r10"
ANCHORS = {"high control", "low control"}
FLOOR = 0.10
N_BOOT = 1000
SEED = 20261027
SHA_PAIR = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA_PAIR
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["raw"] = pd.to_numeric(df["Raw count"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")

    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], pd.to_numeric(g["Conc 1 (uM)"]).round(9),
                                  g["Drug 2"], pd.to_numeric(g["Conc 2 (uM)"]).round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "combo": {w: (str(d1).lower() != "dmso" and str(d2).lower() != "dmso")
                                 for w, (d1, c1, d2, c2) in
                                 {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}.items()},
                       "qc": float(g["failed_qc"].mean()), "layout": layout}
    groups = {}
    for f, s in meta.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)

    # ---------- H017 / H018: annotation coverage in the analysed layouts ----------
    ann = pd.read_csv(ANN, low_memory=False)
    ann["Drug Name"] = ann["Drug Name"].astype(str).str.strip()
    usable = ann[ann["moa"].notna() & (ann["moa"].astype(str).str.lower() != "unknown")]
    moa_map = usable.drop_duplicates("Drug Name").set_index("Drug Name")["moa"].to_dict()

    def family(x: str) -> str:
        return str(x).split(";")[0].strip().lower()

    analysed, pairs = [], set()
    for (it, h), cells in groups.items():
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        analysed.append({"iteration": it, "hash": h[:12], "cells": good})
        f0 = cells[good[0]][0]
        for w, d1, c1, d2, c2 in meta[f0]["layout"]:
            if str(d1).lower() != "dmso" and str(d2).lower() != "dmso":
                pairs.add((d1, d2))
    comps = {c for p in pairs for c in p}
    both = [p for p in pairs if p[0] in moa_map and p[1] in moa_map]
    same_fam = [p for p in both if family(moa_map[p[0]]) == family(moa_map[p[1]])]
    h017 = (len(both) / max(len(pairs), 1)) >= 0.50
    h018 = len(same_fam) >= 20

    # ---------- H019: readout-channel robustness ----------
    def unit_vectors(cell: str, units: list[str], col: str):
        vs = []
        for f in groups_key[cell]:
            sub = df[(df["file"] == f) & (~df["failed_qc"]) & df[col].notna() & (~df["anchor"])]
            s = sub.drop_duplicates("Well").set_index("Well")[col]
            vs.append(s.reindex(units).to_numpy(dtype=float))
        return np.nanmean(np.vstack(vs), axis=0)

    rows = []
    for lay in analysed:
        key = (lay["iteration"], lay["hash"]) if (lay["iteration"], lay["hash"]) in groups else None
        # recover the full hash key
        full = [k for k in groups if k[1][:12] == lay["hash"] and k[0] == lay["iteration"]]
        if not full:
            continue
        groups_key = groups[full[0]]
        cells = lay["cells"]
        units = [u for u in sorted(meta[groups_key[cells[0]][0]]["combo"])
                 if meta[groups_key[cells[0]][0]]["combo"][u]]
        Yy = {c: unit_vectors(c, units, "y") for c in cells}
        Yr = {c: unit_vectors(c, units, "raw") for c in cells}
        nu = len(units)
        iu, ju = np.triu_indices(nu, 1)
        for a in range(len(cells)):
            for b in range(a + 1, len(cells)):
                ca, cb = cells[a], cells[b]
                gap = np.minimum(np.abs(Yy[ca][iu] - Yy[ca][ju]), np.abs(Yy[cb][iu] - Yy[cb][ju]))
                ok = (gap >= FLOOR) & np.isfinite(gap) & np.isfinite(Yr[ca][iu] - Yr[ca][ju]) \
                    & np.isfinite(Yr[cb][iu] - Yr[cb][ju])
                if ok.sum() < 50:
                    continue
                rev_y = (np.sign(Yy[ca][iu] - Yy[ca][ju]) != np.sign(Yy[cb][iu] - Yy[cb][ju]))[ok]
                rev_r = (np.sign(Yr[ca][iu] - Yr[ca][ju]) != np.sign(Yr[cb][iu] - Yr[cb][ju]))[ok]
                rows.append({"layout": "%s/%s" % (lay["iteration"], lay["hash"]), "cells": "%s|%s" % (ca, cb),
                             "n": int(ok.sum()), "rev_y": int(rev_y.sum()), "rev_r": int(rev_r.sum())})

    rr = pd.DataFrame(rows)
    rate_y = float(rr["rev_y"].sum() / rr["n"].sum()) if len(rr) else None
    rate_r = float(rr["rev_r"].sum() / rr["n"].sum()) if len(rr) else None
    lays = sorted(rr["layout"].unique()) if len(rr) else []
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(N_BOOT):
        pick = rng.choice(lays, size=len(lays), replace=True) if lays else []
        sel = pd.concat([rr[rr["layout"] == p] for p in pick]) if lays else rr
        if len(sel) and sel["n"].sum() > 0:
            boots.append(float(sel["rev_r"].sum() / sel["n"].sum() - sel["rev_y"].sum() / sel["n"].sum()))
    ci = [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None
    diff = (rate_r - rate_y) if (rate_r is not None and rate_y is not None) else None
    h019 = bool(diff is not None and abs(diff) <= 0.005 and ci and ci[0] <= 0.005 and ci[1] >= -0.005)

    res = {
        "kind": "data_adequacy_verdict_and_readout_channel_robustness",
        "input_sha256": {"PAIR_SCREEN.csv": sha256(CSV), "MAPKG_drugs": sha256(ANN)},
        "audit": {"analysed_layouts": len(analysed), "distinct_double_drug_pairs": len(pairs),
                  "distinct_compounds": len(comps),
                  "compounds_with_mechanism_text": len(comps & set(moa_map)),
                  "compound_coverage": (len(comps & set(moa_map)) / len(comps)) if comps else None,
                  "pairs_with_both_annotated": len(both),
                  "pairs_sharing_mechanism_family": len(same_fam),
                  "annotation_total_rows": int(len(ann)),
                  "annotation_usable_moa_rows": int(len(usable)),
                  "annotation_usable_fraction": float(len(usable) / len(ann))},
        "H017_target_reference_available": h017,
        "H018_enough_same_mechanism_pairs": h018,
        "H019_readout_channel_robust": h019,
        "readout_channel": {"n_cellpairs": int(len(rr)), "n_pairs": int(rr["n"].sum()) if len(rr) else 0,
                            "reversal_rate_viability": rate_y, "reversal_rate_rawcount": rate_r,
                            "difference_raw_minus_viability": diff,
                            "ci95_layout_clustered": ci},
        "adequacy_verdict": {
            "drug_x_cell_crossing": "met (18 multi-cell layouts, 54,642 comparable unit pairs, R6/E005)",
            "target_engagement_or_genetic_reference": "NOT met",
            "independent_functional_endpoint": "NOT met (single normalised viability readout)",
            "replication": "NOT met beyond duplicate plates (no batch key, 0/2457 identity overlap across layouts)",
        },
        "consequence": ("mechanism-conditional analysis is not addressable with this resource; the program's "
                        "claims stay functional/descriptive, and any 'mechanism' wording is unsupported"),
        "limits": [
            "The third-party annotation source is not independently authenticated here; 'moa' is free text, not a target ID.",
            "H019 compares two channels of the SAME wells, so it tests normalisation, not an independent endpoint.",
            "Exploratory: validation plates were used as scoring endpoints in an earlier round.",
        ],
    }
    for rel in ("research/2026-10-27-agent-cell-identifiability-r10/PROTOCOL_E011.md",
                "research/2026-10-27-agent-cell-identifiability-r10/e011_adequacy_and_channel.py"):
        p = ROOT / rel
        if p.exists():
            res.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E011_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    a = res["audit"]
    print("analysed layouts=%d pairs=%d compounds=%d" % (a["analysed_layouts"], a["distinct_double_drug_pairs"], a["distinct_compounds"]))
    print("compounds with mechanism text: %d (%.1f%%) | pairs both-annotated: %d | same-family: %d" % (
        a["compounds_with_mechanism_text"], 100 * (a["compound_coverage"] or 0), a["pairs_with_both_annotated"],
        a["pairs_sharing_mechanism_family"]))
    print("H017 available:", h017, "| H018 testable:", h018)
    print("channel: n_pairs=%d | viability %.4f | rawcount %.4f | diff %+.4f CI=%s" % (
        res["readout_channel"]["n_pairs"], rate_y or float("nan"), rate_r or float("nan"),
        diff if diff is not None else float("nan"), ci))
    print("H019 robust:", h019)


if __name__ == "__main__":
    main()
