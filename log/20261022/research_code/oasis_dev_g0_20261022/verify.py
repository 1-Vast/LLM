"""Replay integrity, scope and arithmetic checks, without opening non-dev values."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/oasis_dev_g0"


def main():
    checks = []
    def check(name, passed):
        checks.append({"name": name, "passed": bool(passed)})
    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))
    freeze = read(OUT / "PRE_OPEN_FREEZE.json")
    for name, expected in freeze["files"].items():
        path = ROOT / name
        check(f"frozen:{name}", path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected)
    check("pre-opening freeze", not freeze["dev_numeric_export_exists"])
    mapping = {x["compound_id"]: x for x in read(ROOT / "log/20261021/oasis_evaluation_contract/RESERVATION_v2.json")["mapping"]}
    frame = pd.read_parquet(OUT / "dev_wells_all_qc.parquet")
    eligible = pd.read_parquet(OUT / "dev_wells.parquet")
    report = read(OUT / "DEV_QC.json")
    pairs = pd.read_csv(OUT / "technical_repeat_pairs.csv", float_precision="round_trip")
    controls = pd.read_csv(OUT / "plate_controls.csv")
    check("all exported compounds dev", all(mapping[x]["role"] == "dev" for x in frame["compound_id"]))
    check("no control outcome exported as task target", not frame["is_dmso"].any())
    check("unique physical well export", not frame.duplicated(["batch", "plate", "well"]).any())
    check("reservation groups intact", all(mapping[c]["group_id"] == g for c, g in zip(frame["compound_id"], frame["group_id"])))
    check("all dev labels retained before QC", set(frame["compound_id"]) == {c for c, x in mapping.items() if x["role"] == "dev"})
    check("all QC failures retained", len(frame) - len(eligible) == report["failed_observations"])
    check("coverage arithmetic", np.isclose(len(eligible) / len(frame), report["eligible_fraction"]))
    check("no failed observation in eligible export", eligible["observation_pass"].all())
    check("fold/group isolation", eligible.groupby("group_id")["fold"].nunique().max() == 1)
    check("all five folds populated", set(eligible["fold"]) == set(range(5)))
    check("controls finite and all passed", controls["plate_pass"].all() and np.isfinite(controls["mt_median"]).all())
    for endpoint in ("mt", "ldh"):
        subset = pairs[pairs["pair_pass"]]
        correlation = spearmanr(subset[f"{endpoint}_1"], subset[f"{endpoint}_2"]).statistic
        check(f"{endpoint} correlation", np.isclose(correlation, report["repeat"]["endpoints"][endpoint]["spearman"], rtol=1e-12))
        check(f"{endpoint} transformation finite", np.isfinite(eligible[f"{endpoint}_target"]).all())
    lookup = {(c, d): rows for (c, d), rows in frame.groupby(["compound_id", "dose_um"])}
    expected_pair_count = 0
    for _, pair in pairs.iterrows():
        rows = lookup[(pair["compound_id"], pair["dose_um"])].sort_values(["batch", "plate", "well"]).drop_duplicates(["batch", "plate"])
        first, second = rows.iloc[0], rows.iloc[1]
        check(f"pair pre-QC identity:{pair.name}", first["plate"] == pair["plate_1"] and second["plate"] == pair["plate_2"]
              and first["batch"] == pair["batch_1"] and second["batch"] == pair["batch_2"])
        expected_pair_count += bool(first["observation_pass"] and second["observation_pass"])
    check("identity pair denominator", len(pairs) == report["repeat"]["identity_pair_actions"])
    check("complete pair denominator", expected_pair_count == report["repeat"]["paired_actions"])
    check("G0a decision reproduced", report["g0a_pass"] == (report["eligible_fraction"] >= .90 and report["repeat"]["pass"]))
    check("downstream gate honoured", not (OUT / "cpcnn_raw.parquet").exists()
          and not (OUT / "predictions.parquet").exists())
    result = {"status": "PASS" if all(x["passed"] for x in checks) else "FAIL", "checks": checks,
              "count": len(checks), "scope": "Integrity/arithmetic, not biological efficacy or innovation"}
    (OUT / "VERIFICATION.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "count": len(checks),
                      "failed": [x["name"] for x in checks if not x["passed"]]}))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
