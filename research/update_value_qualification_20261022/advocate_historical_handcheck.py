"""Hand-check directions from the exported audit utility vectors, never raw records."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261022/update_value_qualification"


def main():
    target = LOG / "advocate/HISTORICAL_HANDCHECK.json"
    if target.exists():
        raise RuntimeError("Do not overwrite the hand-check")
    source = LOG / "HISTORICAL_CHOICE_AUDIT.json"
    original = source.read_bytes()
    audit = json.loads(original)
    utilities = np.asarray(audit["utilities"], dtype=float)
    if utilities.shape != (2, 36, 2) or audit["arms"] != ["ridge", "R1"]:
        raise ValueError("Unexpected published audit utility schema")
    result = {"utc": datetime.now(timezone.utc).isoformat(), "scope": "Exported audit vectors only; no raw/source/fold joins, fit or new feedback",
              "source_sha256": hashlib.sha256(original).hexdigest(), "directions": {}}
    for selection, evaluation in ((0, 1), (1, 0)):
        name = f"{selection + 1}_to_{evaluation + 1}"
        chosen = np.argmax(utilities[selection], axis=1)
        mean = float(utilities[evaluation, np.arange(36), chosen].mean())
        fixed = utilities[evaluation].mean(axis=0)
        gain = mean - float(fixed.max())
        saved = audit["directions"][name]
        result["directions"][name] = {"chosen_mean": mean, "evaluation_fixed_means": fixed.tolist(),
                                      "gain_vs_hindsight_fixed": gain,
                                      "mean_matches": mean == saved["cross_selected_mean"],
                                      "gain_matches": gain == saved["gain_vs_hindsight_evaluation_best_fixed"]}
    a, b = [v["gain_vs_hindsight_fixed"] for v in result["directions"].values()]
    result["symmetric_gain"] = (a + b) / 2
    result["screen"] = a >= audit["historical_practical_scale"] and b >= audit["historical_practical_scale"]
    result["matches_frozen_descriptive_screen"] = result["screen"] == audit["descriptive_both_direction_screen"]
    result["unchanged"] = source.read_bytes() == original
    result["all_checks_pass"] = (result["unchanged"] and result["matches_frozen_descriptive_screen"]
                                  and all(d["mean_matches"] and d["gain_matches"] for d in result["directions"].values()))
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
