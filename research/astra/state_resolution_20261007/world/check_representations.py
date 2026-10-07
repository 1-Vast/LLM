"""No-label identity, pairing and numerical checks for native representations."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parents[1] / "state_dual_core_20261007/world"
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
plan = json.loads((HERE / "PROTOCOL.json").read_text())
freeze = json.loads((HERE / "FREEZE.json").read_text())
with np.load(HERE / "representations.npz") as f:
    a = {k: f[k] for k in f.files}
with np.load(PRIOR / "state_features.npz") as f:
    old_prediction = f["predicted_mean"]
trace = json.loads((HERE / "forward_trace.json").read_text())
samples = {(r["set_length"], r["plate"]): r for r in plan["samples"]}
roundoff = a["raw_delta"] - (a["counterfactual_delta"] + a["dmso_mean"] - a["basal_mean"])
checks = {"protocol_hash": digest(HERE / "PROTOCOL.json") == freeze["protocol_sha256"],
    "all_frozen_source_hashes": all(digest(HERE.parents[3] / p) == h for p, h in plan["source_files"].items()),
    "all_native_shapes": all(a[k].shape == (2, 144, 2000) for k in ("predicted_mean", "basal_mean", "dmso_mean", "raw_delta", "counterfactual_delta", "pre_relu_counterfactual_delta")),
    "conditions_exact": a["condition_id"].tolist() == [r["condition_id"] for r in plan["conditions"]],
    "all_forwards_same_paired_basal": all(t["basal_sha256"] == samples[t["set_length"],t["plate"]]["sha256"] for t in trace),
    "raw_definition_exact": np.array_equal(a["raw_delta"], a["predicted_mean"] - a["basal_mean"]),
    "counterfactual_definition_exact": np.array_equal(a["counterfactual_delta"], a["predicted_mean"] - a["dmso_mean"]),
    "decomposition_with_float32_roundoff": np.allclose(roundoff, 0, atol=1e-6, rtol=0),
    "all_values_finite": all(np.isfinite(v).all() for k,v in a.items() if k != "condition_id")}
summary = {"checks": {k:bool(v) for k,v in checks.items()}, "passed": bool(all(checks.values())),
    "prior32_prediction_max_abs": float(np.max(np.abs(a["predicted_mean"][0] - old_prediction))),
    "prior32_prediction_allclose_1e6": bool(np.allclose(a["predicted_mean"][0], old_prediction, atol=1e-6, rtol=1e-6)),
    "decomposition_max_abs_roundoff": float(np.abs(roundoff).max()),
    "raw32_vs256_rms": float(np.sqrt(np.mean((a["raw_delta"][0]-a["raw_delta"][1]) ** 2))),
    "counterfactual32_vs256_rms": float(np.sqrt(np.mean((a["counterfactual_delta"][0]-a["counterfactual_delta"][1]) ** 2))),
    "roundoff_note": "identity_checks raw_delta_algebra uses bitwise associativity and can be false for normal float32 arithmetic; direct definitions are checked exactly here",
    "independent": False}
(HERE / "representation_checks.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary))
