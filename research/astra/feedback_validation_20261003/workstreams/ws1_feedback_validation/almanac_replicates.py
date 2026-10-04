"""WS1 step 3c: does NCI-ALMANAC contain independent replicates of drug-pair x line experiments?

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws1_feedback_validation/almanac_replicates.py
- Purpose: EXPLORATORY (ALMANAC was opened once at 2026-10-03T17:58:48 and is exposed). Census of
  how often a pair x line was measured at more than one screening centre, study, test date or
  plate; how those replicates were selected (pairs, lines, centres); agreement of replicate
  labels (mean SCORE per replicate unit) and hit concordance; whether single-agent reference
  wells share the combination plate (so a drug's reference is or is not shared across pairs).
  Finally joins the replicate units to the step-2 arms' purchases.
- Interfaces: run the file with PYTHONPATH="src;." [DECOMPOSITION_RUN].
- Depends on: numpy, pandas, research.certified_discovery.screens (frozen; ALMANAC_ZIP path only).
"""
from __future__ import annotations

import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from research.certified_discovery.screens import ALMANAC_ZIP, CACHE, load_library  # noqa: E402

THR = 10.0
COLS = ["SCREENER", "STUDY", "TESTDATE", "PLATE", "NSC1", "NSC2", "CONCINDEX1", "CONCINDEX2", "CELLNAME", "SCORE"]


def boot(d, seed=20261003, n=10_000):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, d.size, size=(n, d.size))
    m = d[idx].mean(axis=1)
    return [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)]


def agreement(a: np.ndarray, b: np.ndarray) -> dict:
    ha, hb = a > THR, b > THR
    return {"n": int(a.size), "pearson": float(np.corrcoef(a, b)[0, 1]), "sd_diff": float(np.std(a - b, ddof=1)),
            "hit_rate_a": float(ha.mean()), "hit_rate_b": float(hb.mean()),
            "b_hit_given_a_hit": float(hb[ha].mean()) if ha.any() else None,
            "a_hit_given_b_hit": float(ha[hb].mean()) if hb.any() else None,
            "hit_agreement": float((ha == hb).mean())}


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    run = argv[0] if argv else "step2_almanac_exploratory"
    with zipfile.ZipFile(ALMANAC_ZIP) as archive, archive.open("ComboDrugGrowth_Nov2017.csv") as handle:
        f = pd.read_csv(handle, usecols=COLS, low_memory=False,
                        dtype={"NSC1": "Int64", "NSC2": "Int64", "CELLNAME": "string", "PLATE": "string",
                               "STUDY": "string", "SCREENER": "string", "TESTDATE": "string"})
    f["CELLNAME"] = f["CELLNAME"].str.strip()
    out: dict = {"records": int(len(f)), "exposure": "EXPLORATORY: ALMANAC opened 2026-10-03T17:58:48; not confirmation"}
    both = (f["CONCINDEX1"] > 0) & (f["CONCINDEX2"] > 0) & f["NSC2"].notna()
    alone = (f["CONCINDEX1"] > 0) & ~(f["CONCINDEX2"] > 0) & f["NSC2"].isna()
    c = f[both & np.isfinite(f["SCORE"].astype(float))].copy()
    c["lo"] = c[["NSC1", "NSC2"]].min(axis=1)
    c["hi"] = c[["NSC1", "NSC2"]].max(axis=1)
    key = ["lo", "hi", "CELLNAME"]
    g = c.groupby(key)
    per = g.agg(records=("SCORE", "size"), screeners=("SCREENER", "nunique"), studies=("STUDY", "nunique"),
                dates=("TESTDATE", "nunique"), plates=("PLATE", "nunique"), y=("SCORE", "mean")).reset_index()
    out["experiments"] = int(len(per))
    out["records_per_experiment"] = per["records"].value_counts().sort_index().head(20).to_dict()
    for col in ("screeners", "studies", "dates", "plates"):
        out[f"experiments_by_{col}"] = {str(k): int(v) for k, v in per[col].value_counts().sort_index().items()}
    out["screener_record_share"] = {str(k): int(v) for k, v in c["SCREENER"].value_counts().items()}
    # screener assignment: are lines or pairs nested within a screener?
    line_scr = c.groupby("CELLNAME")["SCREENER"].nunique()
    pair_scr = c.groupby(["lo", "hi"])["SCREENER"].nunique()
    out["lines_by_n_screeners"] = {str(k): int(v) for k, v in line_scr.value_counts().sort_index().items()}
    out["pairs_by_n_screeners"] = {str(k): int(v) for k, v in pair_scr.value_counts().sort_index().items()}
    # single-agent reference wells on the combination plate?
    s = f[alone][["PLATE", "NSC1", "CELLNAME"]].copy()
    combo_plates = set(c["PLATE"].dropna().unique())
    single_plates = set(s["PLATE"].dropna().unique())
    out["plates"] = {"combination_plates": len(combo_plates), "single_agent_plates": len(single_plates),
                     "combination_plates_with_single_agent_rows": len(combo_plates & single_plates)}
    s_per = s.groupby(["NSC1", "CELLNAME"])["PLATE"].nunique()
    out["single_agent_plates_per_drug_line"] = {"median": float(s_per.median()), "p10": float(s_per.quantile(0.1)),
                                                "p90": float(s_per.quantile(0.9))}
    # ------------------------------------------------ replicate agreement across independent units
    results = {}
    unit_pairs = {}
    for unit in ("SCREENER", "STUDY", "TESTDATE", "PLATE"):
        u = c.groupby(key + [unit])["SCORE"].mean().reset_index()
        n_units = u.groupby(key)[unit].transform("nunique")
        rep = u[n_units >= 2].copy()
        if rep.empty:
            results[unit] = {"experiments_with_2plus": 0}
            continue
        # first two units in sorted order (deterministic), labels a/b
        rep = rep.sort_values(key + [unit])
        rep["k"] = rep.groupby(key).cumcount()
        a = rep[rep["k"] == 0].set_index(key)["SCORE"]
        b = rep[rep["k"] == 1].set_index(key)["SCORE"]
        joined = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
        res = {"experiments_with_2plus": int(joined.shape[0]), **agreement(joined["a"].to_numpy(), joined["b"].to_numpy())}
        exp_rep = joined.reset_index()
        res["distinct_pairs"] = int(exp_rep[["lo", "hi"]].drop_duplicates().shape[0])
        res["distinct_lines"] = int(exp_rep["CELLNAME"].nunique())
        unit_pairs[unit] = {tuple(map(str, k)): (float(r["a"]), float(r["b"])) for k, r in joined.iterrows()}
        if True:
            combos = u[n_units >= 2].groupby(key)[unit].apply(lambda x: "+".join(sorted(x)))
            res["unit_combinations_top"] = {k: int(v) for k, v in combos.value_counts().head(10).items()}
            # hit rate of replicated vs non-replicated experiments (selection on outcome?)
            merged = per.merge(joined.reset_index()[key].assign(replicated=True), on=key, how="left")
            merged["replicated"] = merged["replicated"].fillna(False).astype(bool)
            res["hit_rate_replicated"] = float((merged.loc[merged["replicated"], "y"] > THR).mean())
            res["hit_rate_not_replicated"] = float((merged.loc[~merged["replicated"], "y"] > THR).mean())
            res["share_of_all_hits_in_replicated"] = float(((merged["y"] > THR) & merged["replicated"]).sum() / (merged["y"] > THR).sum())
            pairs_rep = exp_rep[["lo", "hi"]].drop_duplicates()
            res["replicated_pairs_cover_all_60_lines"] = int((exp_rep.groupby(["lo", "hi"])["CELLNAME"].nunique() >= 55).sum())
            res["replicated_experiments_per_pair_median"] = float(exp_rep.groupby(["lo", "hi"]).size().median())
        results[unit] = res
    out["replicates"] = results
    # ------------------------------------------------ join to arms' purchases (most independent unit available)
    join_unit = next((u_ for u_ in ("SCREENER", "STUDY", "TESTDATE", "PLATE") if unit_pairs.get(u_)), None)
    out["join_unit"] = join_unit
    screener_pair = unit_pairs.get(join_unit, {})
    lib = load_library(CACHE / "almanac_v1.npz")
    nsc = lib.provenance["nsc"]
    keymap = {}
    for i, (a_, b_, c_) in enumerate(zip(lib.a, lib.b, lib.c)):
        keymap[(nsc[a_], nsc[b_], lib.lines[c_])] = i
    rep_rows = {}
    for (lo, hi, line), (ya, yb) in screener_pair.items():
        r = keymap.get((lo, hi, line))
        if r is not None:
            rep_rows[r] = (ya, yb)
    out["screener_replicates_joined_to_library"] = len(rep_rows)
    lines = [json.loads(x) for x in open(HERE / "receipts" / run / "lines.jsonl", encoding="utf-8")]
    arms_out, per_line = {}, defaultdict(dict)
    for arm in sorted(lines[0]["arms"]):
        tot = defaultdict(float)
        for l in lines:
            rows = np.array(l["rows"])
            entries = l["arms"][arm] if isinstance(l["arms"][arm], list) else [l["arms"][arm]]
            acc = defaultdict(float)
            for ent in entries:
                bought = rows[[i for r in ent["purchases"] for i in r]]
                inr = [int(b) for b in bought if int(b) in rep_rows]
                acc["bought_replicated"] += len(inr)
                acc["hits_label_in_rep"] += sum(lib.y[b] > THR for b in inr)
                # cross-centre validation: hit in unit a AND hit in unit b (both centres agree)
                acc["hit_both_centres"] += sum(rep_rows[b][0] > THR and rep_rows[b][1] > THR for b in inr)
            for k in acc:
                acc[k] /= len(entries)
                tot[k] += acc[k]
            per_line[arm][l["line"]] = dict(acc)
        arms_out[arm] = {k: round(v, 2) for k, v in tot.items()}
    out["arms_on_screener_replicates"] = arms_out
    contr = {}
    names = [l["line"] for l in lines]
    for a, b in (("full_mean", "static_mean"), ("full_phit", "static_phit"), ("full_mean", "history"), ("full_mean", "gbm_static")):
        for metric in ("hits_label_in_rep", "hit_both_centres"):
            d = np.array([per_line[a][n].get(metric, 0) - per_line[b][n].get(metric, 0) for n in names])
            contr[f"{a} - {b} : {metric}"] = {"sum": round(float(d.sum()), 2), "mean": round(float(d.mean()), 3), "ci": boot(d)}
    out["contrasts_on_replicates"] = contr
    (HERE / "receipts" / "step3_almanac_replicates.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("arms_on_screener_replicates",)}, indent=1, default=str))
    for k, v in arms_out.items():
        print(f"{k:24s}", v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
