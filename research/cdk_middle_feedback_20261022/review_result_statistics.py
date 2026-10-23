"""Independent scalar-only review; no matrices, predictor imports or fits."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261022/cdk_middle_feedback"
result = json.loads((LOG / "RESULT.json").read_text())
summary = json.loads((LOG / "SUMMARY.json").read_text())
prep = json.loads((LOG / "PREPARATION.json").read_text())
mean = lambda values: math.fsum(values) / len(values)
answer = {}
for scheme in ("loo", "index_blocked"):
    rows = result[scheme]["rows"]
    tasks = sorted(set(tuple(r["task"]) for r in rows))
    assert len(tasks) == 12 and len(rows) == 12 * 12
    by_key = {(tuple(r["task"]), r["method"]): r for r in rows}
    assert len(by_key) == len(rows)
    families = sorted(set("_".join(t[:2]) for t in tasks))
    means = {method: {metric: mean([by_key[t, method][metric] for t in tasks])
                      for metric in ("hellinger2", "tv")}
             for method in result[scheme]["means"]}
    for method, values in means.items():
        for metric, value in values.items():
            assert abs(value - result[scheme]["means"][method][metric]) < 1e-12
    family_gains = {}
    for family in families:
        members = [t for t in tasks if "_".join(t[:2]) == family]
        assert len(members) == 3
        for method in means:
            for metric in ("hellinger2", "tv"):
                value = mean([by_key[t, method][metric] for t in members])
                assert abs(value - summary[scheme]["condition_means"][family][method][metric]) < 1e-12
        family_gains[family] = {
            metric: mean([by_key[t, "early_selected"][metric] - by_key[t, "middle_selected"][metric]
                          for t in members]) for metric in ("hellinger2", "tv")}
    gains = {metric: [by_key[t, "early_selected"][metric] - by_key[t, "middle_selected"][metric]
                      for t in tasks] for metric in ("hellinger2", "tv")}
    for metric, label in (("hellinger2", "hellinger_gain"), ("tv", "tv_gain")):
        assert abs(mean(gains[metric]) - summary[scheme]["paired_selected_mean_gain"][label]) < 1e-12
    classes = {family: {metric: means["early_" + family][metric] - means["middle_" + family][metric]
                        for metric in ("hellinger2", "tv")} for family in ("shrink", "kernel", "ridge")}
    for family, values in classes.items():
        for metric, value in values.items():
            assert abs(value - summary[scheme]["paired_class_gain"][family][metric]) < 1e-12
    answer[scheme] = {"means": means, "selected_family_gains": family_gains,
                      "paired_class_gains": classes, "selected_per_task_gains": dict(zip(map(str, tasks), gains["hellinger2"])),
                      "selection_counts": {name: dict(Counter(by_key[t, name]["selected_method"] for t in tasks))
                                           for name in ("early_selected", "middle_selected")},
                      "positive_zero_negative": {metric: {"positive": sum(v > 0 for v in values),
                                                           "zero": sum(v == 0 for v in values),
                                                           "negative": sum(v < 0 for v in values)} for metric, values in gains.items()}}
answer["other_mass"] = {stage: {"mean": mean([r[index] for r in prep["other_mass"]]),
                                     "max": max(r[index] for r in prep["other_mass"])}
                        for stage, index in (("early", 0), ("middle", 1), ("end", 2))}
answer["bindings"] = {name: hashlib.sha256((LOG / name).read_bytes()).hexdigest()
                      for name in ("RESULT.json", "SUMMARY.json", "PREPARATION.json")}
answer["scalar_recomputation_checks"] = "PASS all per-method means, all four-condition means, selected contrasts and paired-class contrasts within 1e-12"
answer["evaluation_wall_seconds"] = result["wall_seconds"]
with (LOG / "review/RESULT_STATISTICS_CHECK.json").open("x", encoding="utf-8") as stream:
    json.dump(answer, stream, indent=2)
    stream.write("\n")
print(json.dumps(answer, indent=2))
