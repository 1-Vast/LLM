"""Independently recompute recorded decisions and verify current input bytes."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261021/rsi_next_qualification"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def main():
    checks = []
    def check(name, condition):
        checks.append({"check": name, "passed": bool(condition)})
        if not condition:
            raise AssertionError(name)

    inputs = json.loads((OUT / "INPUTS.json").read_text())
    for row in inputs["prediction_files"]:
        check("input:" + row["path"], digest(ROOT / row["path"]) == row["sha256"])
    check("protocol", digest(OUT / "PROTOCOL.md") == inputs["protocol_sha256"])
    check("script", digest(Path(__file__).with_name("blend_qualification.py")) == inputs["script_sha256"])
    before = json.loads((OUT / "INTEGRITY_BEFORE.json").read_text())
    for name, value in before["files"].items():
        check("preserved:" + name, digest(ROOT / name) == value)
    decisions = pd.read_csv(OUT / "decisions.csv")
    result = json.loads((OUT / "RESULTS.json").read_text())
    weights = result["weights"]
    for seed in (0, 1):
        scores = pd.read_csv(OUT / f"exposed_scores_seed{seed}.csv")
        check(f"unique keys seed{seed}", not scores.duplicated(["cell", "perts"]).any())
        check(f"finite truth seed{seed}", scores.y.notna().all())
        check(f"pool constant seed{seed}", set(scores[scores.in_pool].groupby("cell").size()) == {14})
        for row in decisions[decisions.seed == seed].itertuples():
            d = scores[(scores.cell == row.cell) & scores.in_pool]
            # Use Python sorting rather than the experiment's pandas sorting.
            order = sorted(d.to_dict("records"), key=lambda r: (-r[row.arm], r["perts"]))[:5]
            check(f"selected:{seed}/{row.cell}/{row.arm}", "|".join(r["perts"] for r in order) == row.selected_drugs)
            check(f"truth:{seed}/{row.cell}/{row.arm}", int(sum(r["y"] for r in order)) == row.hits5)
        for name, weight in weights.items():
            check(f"mix:{seed}/{name}", np.allclose(scores["selected_" + name], (1 - weight) * scores.b1 + weight * scores[name], rtol=0, atol=1e-14))
    selection = pd.read_csv(OUT / "selection_scores.csv")
    for name in weights:
        trials = []
        for w in (0, 0.25, 0.5, 0.75, 1):
            values = []
            for cell, d in selection[selection.in_pool].groupby("cell"):
                recs = d.to_dict("records")
                order = sorted(recs, key=lambda r: (-((1 - w) * r["b1"] + w * r[name]), r["perts"]))[:5]
                values.append({"lineage": cell.replace("(ATCC)", "").strip(), "p": sum(r["y"] for r in order) / 5})
            value = pd.DataFrame(values).groupby("lineage").p.mean().mean()
            trials.append((value, w))
        selected = sorted(trials, key=lambda t: (-t[0], t[1]))[0][1]
        check("selection:" + name, selected == weights[name])
    check("stopping rule", result["decision"] == ("QUALIFY_MATCHED_SUPERVISION_CONTROL" if all(s["continue_ptv"] for s in result["seeds"]) else "STOP_FURTHER_PTV_SEARCH"))
    resources = json.loads((OUT / "RESOURCES.json").read_text())
    check("memory counter valid", resources["peak_working_set_bytes"] > 1024 * 1024)
    check("8GiB main-process target", resources["peak_working_set_bytes"] < 8 * 1024 ** 3)
    check("no GPU/API expense", resources["gpu_seconds"] == resources["api_requests"] == 0)
    check("ordinary classifiers explicitly accounted", resources["conventional_classifier_fits"] == 26 and resources["world_model_retrains"] == 0)
    source = json.loads((OUT / "SOURCE_AUDIT.json").read_text())
    check("source audit passed", source["status"] == "PASS")
    for row in source["files"] + source["caches"]:
        check("authenticated source:" + row["path"], digest(ROOT / row["path"]) == row["sha256"])
    check("7 independent old-final units per seed", all(s["primary_vs_strongest_nonworld"]["n_lineages"] == 7 for s in result["seeds"]))
    receipt = {"status": "PASS", "checks_passed": len(checks), "checks": checks,
               "scope": "Record/input integrity and arithmetic; no scientific confirmation or RSI validation"}
    (OUT / "VERIFICATION.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "checks_passed": len(checks)}))


if __name__ == "__main__":
    main()
