"""Independent dev-only source/normalisation/pair/statistic audit; no model fits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/oasis_dev_g0"
DEST = OUT / "independent_audit"
RAW = ["mtt_lumi", "ldh_abs_signal", "ldh_abs_background", "ldh_abs"]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key(batch, plate, well):
    m = re.fullmatch(r"([A-Za-z]+)0*(\d+)", str(well))
    assert m is not None
    return str(batch).replace("assayworks_", "", 1), str(plate), f"{m[1].upper()}{int(m[2]):02d}"


def rank_correlation(x, y):
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])


def metrics(x, y):
    v = np.stack([x, y])
    return {"n": len(x), "spearman": rank_correlation(x, y),
            "pearson": float(np.corrcoef(x, y)[0, 1]),
            "pooled_variance": float(v.var()), "repeat_mse": float(np.mean((x-y)**2)),
            "repeat_mse_over_pooled_variance": float(np.mean((x-y)**2) / v.var()),
            "mean_difference": float(np.mean(y-x)), "median_abs_difference": float(np.median(np.abs(y-x))),
            "x_quantiles": np.quantile(x, [0, .01, .05, .25, .5, .75, .95, .99, 1]).tolist(),
            "y_quantiles": np.quantile(y, [0, .01, .05, .25, .5, .75, .95, .99, 1]).tolist()}


def main():
    started = time.perf_counter()
    DEST.mkdir(exist_ok=True)
    assert not (DEST / "RESULTS.json").exists(), "Do not overwrite an independent audit"
    dev = pd.read_parquet(OUT / "dev_wells_all_qc.parquet")
    controls_saved = pd.read_csv(OUT / "plate_controls.csv")
    saved_pairs = pd.read_csv(OUT / "technical_repeat_pairs.csv")
    claim = load(OUT / "DEV_QC.json")
    reservation = load(ROOT / "log/20261021/oasis_evaluation_contract/RESERVATION_v2.json")
    roles = {x["compound_id"]: x for x in reservation["mapping"]}
    assert dev["role"].eq("dev").all() and not dev["is_dmso"].any()
    assert all(roles[x]["role"] == "dev" for x in dev["compound_id"])
    assert all(roles[x]["group_id"] == g for x, g in zip(dev["compound_id"], dev["group_id"]))
    names = set(dev["compound_name"]) | {"DMSO"}
    source_manifest = load(ROOT / "log/20261021/oasis_source_qualification/SOURCE_MANIFEST.json")
    sources = []
    for item in source_manifest:
        path = ROOT / item["local_path"]
        assert digest(path) == item["sha256"]
        table = pq.read_table(path, columns=["source", "plate", "well", "compound_name", "compound_concentration_um", *RAW],
                              filters=[("compound_name", "in", sorted(names))])
        sources.append(table.to_pandas())
    raw = pd.concat(sources, ignore_index=True)
    raw["key"] = [key(*r) for r in raw[["source", "plate", "well"]].itertuples(index=False, name=None)]
    for _, group in raw.groupby("key"):
        assert group[["compound_name", "compound_concentration_um", *RAW]].nunique(dropna=False).le(1).all()
    raw = raw.drop_duplicates("key").set_index("key")
    dev["key"] = [key(*r) for r in dev[["batch", "plate", "well"]].itertuples(index=False, name=None)]
    assert dev["key"].is_unique
    raw_dev = raw[raw["compound_name"].ne("DMSO")]
    assert set(raw_dev.index) == set(dev["key"])
    dev_index = dev.set_index("key").loc[raw_dev.index]
    for c in RAW:
        np.testing.assert_array_equal(raw_dev[c], dev_index[c])
    checks = {"dev_only": True, "dev_groups_and_roles_match_reservation": True,
              "raw_dev_keys_and_values_exact": True, "raw_source_files": len(sources),
              "physical_dev_wells": len(dev), "dev_labels": dev["compound_id"].nunique(),
              "dev_groups": dev["group_id"].nunique()}
    controls = []
    for (batch, plate), rows in raw[raw["compound_name"].eq("DMSO")].groupby(lambda k: k[:2]):
        mt = rows["mtt_lumi"].to_numpy()
        ld = rows["ldh_abs"].to_numpy()
        controls.append({"batch": batch, "plate": plate, "dmso_wells": len(rows),
                         "mt_median": np.median(mt), "mt_robust_cv": 1.4826*np.median(abs(mt-np.median(mt)))/np.median(mt),
                         "ldh_median": np.median(ld), "ldh_mad_scale": 1.4826*np.median(abs(ld-np.median(ld)))})
    controls = pd.DataFrame(controls).set_index(["batch", "plate"])
    saved = controls_saved.set_index(["batch", "plate"]).loc[controls.index]
    control_error = {c: float(np.max(np.abs(controls[c]-saved[c]))) for c in controls.columns}
    for c in controls.columns:
        np.testing.assert_allclose(controls[c], saved[c], rtol=1e-12, atol=1e-12)
    checks["control_recompute_max_errors"] = control_error
    mt = np.log2(dev["mtt_lumi"] / dev["mt_median"])
    ld = np.arcsinh((dev["ldh_abs"]-dev["ldh_median"]) / dev["ldh_mad_scale"])
    eligible = (dev[RAW].apply(np.isfinite).all(axis=1) & dev["mtt_lumi"].gt(0) & dev["plate_pass"]
                & dev["cell_count"].ge(0) & np.isfinite(dev["cell_count"]) & np.isfinite(dev["count_log_center"]))
    np.testing.assert_array_equal(eligible, dev["observation_pass"])
    np.testing.assert_allclose(mt[eligible], dev.loc[eligible, "mt_target"], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(ld[eligible], dev.loc[eligible, "ldh_target"], rtol=1e-12, atol=1e-12)
    checks.update({"eligible_dev_wells": int(eligible.sum()), "eligible_fraction": float(eligible.mean()),
                   "missing_count_wells": int(dev["cell_count"].isna().sum()),
                   "raw_ldh_identity_max_error": float(abs(dev["ldh_abs_signal"]-dev["ldh_abs_background"]-dev["ldh_abs"]).max())})
    first = dev.sort_values(["batch", "plate", "well"]).drop_duplicates(["compound_id", "dose_um", "batch", "plate"])
    first["side"] = first.groupby(["compound_id", "dose_um"]).cumcount()
    first = first[first["side"].lt(2)]
    pivot = first.pivot(index=["compound_id", "dose_um", "group_id"], columns="side",
                        values=["mt_target", "ldh_target", "plate", "batch", "observation_pass"])
    reconstructed = pd.DataFrame(index=pivot.index)
    for e in ("mt", "ldh"):
        for i in (0, 1):
            reconstructed[f"{e}_{i+1}"] = pivot[(f"{e}_target", i)].astype(float)
    reconstructed["pair_pass"] = pivot[("observation_pass", 0)] & pivot[("observation_pass", 1)]
    reconstructed = reconstructed.reset_index()
    pairs = saved_pairs.set_index(["compound_id", "dose_um", "group_id"])
    # CSV round trips can change binary concentration representations by <1 ulp.
    rebuilt = reconstructed.set_index(["compound_id", "dose_um", "group_id"])
    compare = saved_pairs.merge(reconstructed, on=["compound_id", "group_id"], suffixes=("_saved", "_rebuilt"))
    compare = compare[np.isclose(compare["dose_um_saved"], compare["dose_um_rebuilt"], rtol=1e-12, atol=0)]
    assert len(compare) == len(saved_pairs) == len(reconstructed)
    for c in ("mt_1", "mt_2", "ldh_1", "ldh_2"):
        np.testing.assert_allclose(compare[f"{c}_saved"], compare[f"{c}_rebuilt"], rtol=1e-12, atol=1e-12, equal_nan=True)
    np.testing.assert_array_equal(compare["pair_pass_saved"], compare["pair_pass_rebuilt"])
    good = reconstructed[reconstructed["pair_pass"]].reset_index(drop=True)
    group_ids = sorted(good["group_id"].unique())
    groups = [np.flatnonzero(good["group_id"].eq(g)) for g in group_ids]
    rng = np.random.default_rng(20261022)
    resamples = [np.concatenate([groups[j] for j in rng.choice(len(groups), size=len(groups), replace=True)]) for _ in range(2000)]
    result = {"checks": checks, "identity_pairs": len(reconstructed), "passing_pairs": len(good),
              "paired_groups": len(group_ids), "pair_values_rebuilt_match_csv": True,
              "batch_pair_counts": saved_pairs[saved_pairs["pair_pass"]].groupby(["batch_1", "batch_2"]).size().to_dict(),
              "endpoints": {}, "diagnostic_status": "All tail/range descriptions below are post hoc and cannot rescue frozen G0a"}
    result["batch_pair_counts"] = {"/".join(k): int(v) for k, v in result["batch_pair_counts"].items()}
    for e in ("mt", "ldh"):
        x, y = good[f"{e}_1"].to_numpy(), good[f"{e}_2"].to_numpy()
        report = metrics(x, y)
        boot = [rank_correlation(x[ix], y[ix]) for ix in resamples]
        report["group_bootstrap_95"] = np.quantile(boot, [.025, .975]).tolist()
        report["frozen_endpoint_pass"] = report["spearman"] >= .6 and report["group_bootstrap_95"][0] > .5
        center = float(np.mean(np.r_[x, y]))
        signal = ((x-center)**2 + (y-center)**2) / 2
        severity = np.maximum(np.abs(x), np.abs(y))
        order = np.argsort(-severity)
        tails = []
        for fraction in (.01, .05, .10):
            k = int(np.ceil(fraction * len(x)))
            central = order[k:]
            tails.append({"removed_extreme_fraction": fraction, "tail_pairs": k,
                "tail_share_of_total_pooled_squared_deviation": float(signal[order[:k]].sum()/signal.sum()),
                "remaining_metrics": metrics(x[central], y[central])})
        report["posthoc_tail_diagnostics"] = tails
        result["endpoints"][e] = report
        np.testing.assert_allclose(report["spearman"], claim["repeat"]["endpoints"][e]["spearman"], atol=1e-12)
        np.testing.assert_allclose(report["group_bootstrap_95"], claim["repeat"]["endpoints"][e]["group_bootstrap_95"], atol=1e-12)
    result["g0a_pass_recomputed"] = bool(checks["eligible_fraction"] >= .9 and len(group_ids) >= 100 and all(x["frozen_endpoint_pass"] for x in result["endpoints"].values()))
    result["input_hashes"] = {p.name: digest(p) for p in [OUT / "dev_wells_all_qc.parquet", OUT / "technical_repeat_pairs.csv", OUT / "plate_controls.csv", OUT / "DEV_QC.json", Path(__file__)]}
    result["wall_seconds"] = time.perf_counter() - started
    result["scope"] = "Dev export plus original raw sources predicate-filtered to frozen dev names and DMSO; no other outcome roles exported"
    (DEST / "RESULTS.json").write_text(json.dumps(result, indent=2, allow_nan=False, default=int), encoding="utf-8")
    print(json.dumps(result, indent=2, allow_nan=False, default=int))


if __name__ == "__main__":
    main()
