"""Metadata-only MIX-Seq index and line split (writes MIXSEQ_SPLIT.json once).

Reads obs fields of the scPerturb copy of McFarland et al. 2020 (no expression; no treated-cell
count per line is computed, because treated counts are the abundance outcome).
Experiments are identified by their line pools:
* pool A: 93 lines in two sub-pools (control channels 1 and 10), 24 h, eight drugs;
* pool C: 114 lines, trametinib 24 h with its own 24 h control (replicate experiment);
* pool D: 24 lines, trametinib time course 3/6/12/24/48 h with a DMSO hash at every time.
Strata: STATE-training lines (Tahoe reference lines), STATE zero-shot lines, unseen lines.
Unseen pool-A lines with >= 20 control cells are permuted (seed 20261010): first third development,
rest confirmation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
H5 = ROOT / "data/external/mixseq_scperturb/mcfarland_2020.h5ad"
SEED = 20261010
MIN_CONTROL = 20
TAHOE_ZEROSHOT = {"ACH-000178", "ACH-000164", "ACH-000580", "ACH-001021", "ACH-000861"}


def obs() -> pd.DataFrame:
    a = ad.read_h5ad(H5, backed="r")
    o = a.obs[["DepMap_ID", "cell_line", "cell_quality", "channel", "perturbation", "time", "dose_value", "hash_tag"]].copy()
    a.file.close()
    for c in o.columns:
        o[c] = o[c].astype(str)
    return o[o.cell_quality == "normal"]


def main() -> dict:
    out_path = HERE / "MIXSEQ_SPLIT.json"
    if out_path.exists():
        raise SystemExit("MIXSEQ_SPLIT.json exists; the split is written once")
    o = obs()
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    tahoe = {v["depmap_id"]: f for f, v in split["lines"].items() if v["depmap_id"]}
    ctrl_a = o[(o.perturbation == "control") & (o.time == "24") & o.channel.isin(["1", "10"])]
    sub = ctrl_a.groupby("DepMap_ID").channel.agg(lambda s: s.mode()[0]).to_dict()
    n_ctrl_a = ctrl_a.groupby("DepMap_ID").size().to_dict()
    ctrl_c = o[(o.perturbation == "control") & (o.time == "24") & (o.channel == "nan")]
    n_ctrl_c = ctrl_c.groupby("DepMap_ID").size().to_dict()
    tc = o[o.time == "3, 6, 12, 24, 48"]
    dmso_d = tc[tc.hash_tag.str.startswith("DMSO_")]
    n_ctrl_d = dmso_d.groupby("DepMap_ID").size().to_dict()
    prism = set(pd.read_csv(ROOT / "data/external/prism_19q4/raw/primary-screen-cell-line-info.csv").depmap_id.dropna())
    names = o.drop_duplicates("DepMap_ID").set_index("DepMap_ID").cell_line.to_dict()

    def stratum(d):
        if d in TAHOE_ZEROSHOT:
            return "tahoe_zeroshot"
        return "state_training" if d in tahoe else "unseen"

    lines = {d: {"name": names[d], "stratum": stratum(d), "pool_A_subpool": sub.get(d), "control_A": int(n_ctrl_a.get(d, 0)),
                 "control_C": int(n_ctrl_c.get(d, 0)), "control_D": int(n_ctrl_d.get(d, 0)), "prism_primary": d in prism,
                 "tahoe_file": tahoe.get(d)} for d in sorted(names)}
    pool_a = sorted(d for d, v in lines.items() if v["pool_A_subpool"] is not None)
    eligible = [d for d in pool_a if lines[d]["stratum"] == "unseen" and lines[d]["control_A"] >= MIN_CONTROL]
    perm = np.random.default_rng(SEED).permutation(len(eligible))
    k = len(eligible) // 3
    res = {
        "seed": SEED, "min_control": MIN_CONTROL,
        "pool_A": pool_a,
        "pool_A_development": sorted(eligible[i] for i in perm[:k]),
        "pool_A_confirmation": sorted(eligible[i] for i in perm[k:]),
        "pool_A_state_training": sorted(d for d in pool_a if lines[d]["stratum"] == "state_training"),
        "pool_A_tahoe_zeroshot": sorted(d for d in pool_a if lines[d]["stratum"] == "tahoe_zeroshot"),
        "pool_A_undercounted": sorted(d for d in pool_a if lines[d]["stratum"] == "unseen" and lines[d]["control_A"] < MIN_CONTROL),
        "pool_C": sorted(d for d, v in lines.items() if v["control_C"] > 0),
        "pool_D": sorted(d for d, v in lines.items() if v["control_D"] > 0),
        "lines": lines,
        "source_obs_sha256": hashlib.sha256(pd.util.hash_pandas_object(o, index=True).values.tobytes()).hexdigest(),
    }
    out_path.write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    for k in ("pool_A", "pool_A_development", "pool_A_confirmation", "pool_A_state_training", "pool_A_tahoe_zeroshot", "pool_A_undercounted", "pool_C", "pool_D"):
        print(k, len(r[k]))
    print("pool D strata", pd.Series([r["lines"][d]["stratum"] for d in r["pool_D"]]).value_counts().to_dict(),
          "in pool A:", len(set(r["pool_D"]) & set(r["pool_A"])), "in pool C:", len(set(r["pool_D"]) & set(r["pool_C"])))
    print("pool A x C overlap", len(set(r["pool_A"]) & set(r["pool_C"])), "pool A prism", sum(r["lines"][d]["prism_primary"] for d in r["pool_A"]))
    print("control_A median", int(np.median([r["lines"][d]["control_A"] for d in r["pool_A"]])), "control_D median", int(np.median([r["lines"][d]["control_D"] for d in r["pool_D"]])))
