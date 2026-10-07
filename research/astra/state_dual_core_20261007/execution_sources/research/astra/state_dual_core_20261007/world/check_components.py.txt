"""Author-side array and identity checks; independent review is separate."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

p = Path(__file__).resolve().parent
d = pd.read_csv(p / "conditions.csv")
a = np.load(p / "state_features.npz")
b = np.load(p / "sealed_outcomes.npz")
f = json.loads((p / "metadata_freeze.json").read_text())
checks = {
    "prediction_identity": a["condition_id"].tolist() == d.condition_id.tolist(),
    "outcome_identity": b["condition_id"].tolist() == d.condition_id.tolist(),
    "controls_disjoint": all(not set(x["basal_rows"]) & set(x["reference_rows"]) for x in f["controls"].values()),
    "chemical_groups_48": d.chemical_group.nunique() == 48,
    "split_isolation": d.groupby("chemical_group").split.nunique().max() == 1,
    "finite_arrays": all(np.isfinite(a[k]).all() for k in ["predicted_mean", "basal_mean", "state_delta"]) and np.isfinite(b["observed_delta"]).all(),
    "representation_definition": np.array_equal(a["state_delta"], a["predicted_mean"] - a["basal_mean"]),
    "response_definition": np.allclose(b["observed_delta"], b["observed_mean"] - b["reference_mean"]),
}
checks = {k: bool(v) for k, v in checks.items()}
(p / "component_checks.json").write_text(json.dumps({"checks": checks, "passed": all(checks.values()), "independent": False}, indent=2))
print(checks)
