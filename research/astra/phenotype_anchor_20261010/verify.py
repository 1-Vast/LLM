"""Independent verification of the held-out evaluation (run after evaluate.py). Writes VERIFIED.json."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]
import analysis as A  # noqa: E402
import evaluate as E  # noqa: E402
from tools.datasets.tahoe_phenotypes import counts_from_codes, phenotype_frame  # noqa: E402

ENDPOINTS = ("E1_survival", "E2_g1")


def check(name, ok, detail):
    print(json.dumps({"check": name, "passed": bool(ok)}), flush=True)
    return {"check": name, "passed": bool(ok), "detail": detail}


def utc(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def freeze_precedence():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    frozen = utc(freeze["frozen_utc"])
    changed = [n for n, h in freeze["files"].items() if hashlib.sha256((HERE / n).read_bytes()).hexdigest() != h]
    earliest = {}
    for f in A.P.HELDOUT:
        for kind, ledger in (("obs", HERE / "obs" / "ledgers" / f"{f}.jsonl"), ("expression", HERE / "expression" / "ledgers" / f"{f}.jsonl")):
            stamps = [utc(json.loads(line)["utc"]) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
            earliest[f"{kind}:{f}"] = min(stamps).isoformat()
    for path in list((HERE / "state_forecasts").glob("*.json")) + list((HERE / "llm").glob("*.json")):
        earliest[path.name] = datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat()
    late = all(datetime.fromisoformat(v) > frozen for v in earliest.values())
    return check("freeze_precedes_heldout_access_and_frozen_files_unchanged", late and not changed,
                 {"frozen_utc": freeze["frozen_utc"], "changed_frozen_files": changed, "earliest_heldout_access": earliest})


def poisoning(canonical):
    with tempfile.TemporaryDirectory() as tmp:
        E.main(out_dir=Path(tmp), poison_seed=7)
        diffs = {}
        for e in ENDPOINTS:
            z = np.load(Path(tmp) / f"PREDICTIONS_{e}.npz")
            for k in z.files:
                if k in ("obs",):
                    continue
                diffs[f"{e}:{k}"] = bool(np.array_equal(z[k], canonical[e][k], equal_nan=k not in ("labels",)))
        obs_changed = not np.allclose(np.load(Path(tmp) / "PREDICTIONS_E1_survival.npz")["obs"], canonical["E1_survival"]["obs"], equal_nan=True)
    return check("predictions_unchanged_when_heldout_outcomes_are_poisoned", all(diffs.values()) and obs_changed,
                 {"identical": diffs, "poisoned_outcome_differs": obs_changed})


def outcome_parity(canonical):
    keep, info = A.qualified_reference()
    table = {}
    for f in list(keep) + list(A.P.HELDOUT):
        receipt = json.loads((HERE / "obs" / f"{f}.json").read_text(encoding="utf-8"))
        z = np.load(A.CACHE / "obs" / f"{f}.npz")
        cats = receipt["categories"]
        table.update(counts_from_codes(f, z["drugname_drugconc"], z["plate"], z["phase"], cats["drugname_drugconc"], cats["plate"], cats["phase"]))
    frame = phenotype_frame(table, list(keep) + list(A.P.HELDOUT), keep)
    labels = list(canonical["E1_survival"]["labels"])
    def plate_mean(f, lab):
        vals = [rec["survival"] for (ff, l, _), rec in frame.items() if ff == f and l == lab]
        return np.mean(vals) if vals else np.nan
    ref_mean = np.array([np.nanmean([plate_mean(f, l) for f in keep]) for l in labels])
    obs = np.array([[plate_mean(f, l) for l in labels] for f in A.P.HELDOUT]) - ref_mean
    diff = float(np.nanmax(np.abs(obs - canonical["E1_survival"]["obs"])))
    same_nan = bool(np.array_equal(np.isnan(obs), np.isnan(canonical["E1_survival"]["obs"])))
    return check("heldout_E1_outcomes_recomputed_with_promoted_tool", diff < 1e-9 and same_nan, {"max_abs_difference": diff})


def metric_arithmetic(canonical, results):
    worst = 0.0
    for e in ENDPOINTS:
        z = canonical[e]
        for arm, rec in results["endpoints"][e]["arms"].items():
            for j in range(len(A.P.HELDOUT)):
                pred, obs, gen = z[arm][j], z["obs"][j], z["generic"][j]
                ok = ~np.isnan(pred) & ~np.isnan(obs)
                r = np.nan if np.std(pred[ok]) == 0 else float(np.sum((pred[ok] - pred[ok].mean()) * (obs[ok] - obs[ok].mean())) / np.sqrt(np.sum((pred[ok] - pred[ok].mean()) ** 2) * np.sum((obs[ok] - obs[ok].mean()) ** 2)))
                stored = rec["r"][j]
                if np.isnan(r) != np.isnan(stored):
                    worst = float("inf")
                elif not np.isnan(r):
                    worst = max(worst, abs(r - stored))
                idx = [i for i in range(len(obs)) if not np.isnan(obs[i])]
                idx.sort(key=lambda i: (pred[i], gen[i]))
                u = -float(np.mean(obs[idx[:A.TOP_K]]))
                worst = max(worst, abs(u - rec["top10_utility"][j]))
    return check("metrics_recomputed_with_independent_arithmetic", worst < 1e-9, {"max_abs_difference": worst})


def exact_rerun(canonical, results):
    with tempfile.TemporaryDirectory() as tmp:
        E.main(out_dir=Path(tmp))
        again = json.loads((Path(tmp) / "RESULTS.json").read_text(encoding="utf-8"))
        same_arrays = all(np.array_equal(np.load(Path(tmp) / f"PREDICTIONS_{e}.npz")[k], canonical[e][k], equal_nan=k != "labels")
                          for e in ENDPOINTS for k in canonical[e].files)
    again.pop("seconds", None)
    base = dict(results)
    base.pop("seconds", None)
    same_json = json.dumps(again, sort_keys=True) == json.dumps(base, sort_keys=True)
    return check("complete_rerun_reproduces_results_and_arrays", same_json and same_arrays, {"arrays_identical": same_arrays, "results_identical": same_json})


def gate_arithmetic():
    gate = json.loads((HERE / "GATE.json").read_text(encoding="utf-8"))
    z = np.load(HERE / "reference_loo.npz")
    worst = 0.0
    for endpoint in ("survival", "g1"):
        obs = z[f"{endpoint}_obs"]
        for arm in ("R", "B", "RK"):
            pred = z[f"{endpoint}_{arm}"]
            rs = []
            for j in range(len(obs)):
                ok = ~np.isnan(obs[j]) & ~np.isnan(pred[j])
                a, b = pred[j][ok] - pred[j][ok].mean(), obs[j][ok] - obs[j][ok].mean()
                rs.append(float(np.sum(a * b) / np.sqrt(np.sum(a * a) * np.sum(b * b))))
            worst = max(worst, abs(float(np.mean(rs)) - gate[endpoint][arm]["mean_r"]))
    s = gate["survival"]
    margin = max(s["R"]["mean_r"], s["RK"]["mean_r"]) - max(s["B"]["mean_r"], s["O"]["mean_r"])
    consistent = abs(margin - gate["gate"]["margin"]) < 1e-12 and gate["gate"]["passes"] == (margin >= gate["mub"])
    return check("reference_gate_recomputed_from_saved_loo_arrays", worst < 1e-9 and consistent, {"max_abs_difference": worst, "margin": margin})


def state_receipts():
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((HERE / "state_forecasts").glob("*.json"))]
    staging = json.loads((HERE / "STATE_STAGING.json").read_text(encoding="utf-8"))[0]["sha256"]
    ok = rows and all(r["native_predict_step_repeat_equal"] and not r["treated_rows_read"] and r["checkpoint_sha256"] == staging for r in rows)
    return check("state_receipts_native_repeatable_no_treated_rows", ok, {"receipts": len(rows), "refused_labels": {r["target"] + "<-" + r["basal_from"]: len(r["refused"]) for r in rows}})


def main():
    results = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    canonical = {e: np.load(HERE / f"PREDICTIONS_{e}.npz") for e in ENDPOINTS}
    checks = [freeze_precedence(), gate_arithmetic(), state_receipts(), outcome_parity(canonical), metric_arithmetic(canonical, results),
              poisoning(canonical), exact_rerun(canonical, results)]
    body = {"checks": checks, "all_passed": all(c["passed"] for c in checks),
            "results_sha256": hashlib.sha256((HERE / "RESULTS.json").read_bytes()).hexdigest()}
    (HERE / "VERIFIED.json").write_text(json.dumps(body, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"all_passed": body["all_passed"]}))


if __name__ == "__main__":
    main()
