"""Post-result reporting only; no fitting, archive access or reserve conversion."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261022/az_paid_reference_gate"


def read(name):
    return json.loads((LOG / name).read_text(encoding="utf-8"))


def main():
    scores = read("TEST_METRICS.json")
    selection = read("SELECTION.json")
    diag = read("SUPPORT_PLATEAU_DIAGNOSTICS.json")
    plateau = diag["plateau"]
    pairs = sum(row["finite_response_pairs"] for row in plateau)
    summary = {
        "scope": "post-outcome reporting only; descriptive diagnostics, no new tests or selection",
        "scores": {name: {key: value for key, value in values.items()
                            if isinstance(value, (int, float, bool, str))}
                   for name, values in scores.items()},
        "selection": {endpoint: {name: {key: value for key, value in choice.items()
                                          if key != "metrics"}
                                 for name, choice in choices.items()}
                      for endpoint, choices in selection["policies"].items()},
        "selection_other": {key: value for key, value in selection.items()
                            if key != "policies"},
        "support": diag["support"],
        "pairs_absent_from_training": diag["pairs_absent_from_training"],
        "plateau": {
            "episodes_with_flagged_pairs": sum(row["pairs"] > 0 for row in plateau),
            "flagged_pairs": sum(row["pairs"] for row in plateau),
            "finite_response_pairs": pairs,
            "missing_response_pairs": sum(row["missing_response_pairs"] for row in plateau),
            "pair_weighted_mean_absolute_gap": (
                sum(row["mean_absolute_response_gap"] * row["finite_response_pairs"]
                    for row in plateau if row["finite_response_pairs"]) / pairs
                if pairs else None),
            "maximum_absolute_gap": max((row["max_absolute_response_gap"]
                                          for row in plateau
                                          if row["finite_response_pairs"]), default=None),
            "caution": "correlated within-episode diagnostic pairs, not independent samples or a noise floor",
        },
        "costs": read("COSTS.json"),
    }
    output = LOG / "RESULTS_SUMMARY.json"
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
