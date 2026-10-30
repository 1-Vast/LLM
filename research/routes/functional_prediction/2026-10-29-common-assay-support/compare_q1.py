"""Compare saved independent results; never rerun either numerical implementation."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
root = json.loads((HERE / "q1_run/results.json").read_text(encoding="utf-8"))
ind = json.loads((HERE / "independent_q1/result.json").read_text(encoding="utf-8"))
evaluated = json.loads((HERE / "q1_run/evaluated_leaves.json").read_text(encoding="utf-8"))
out = {"comparison_only": True, "numeric_executions_added": 0, "candidates": {},
       "hypotheses_equal": all(root["H"][key] == ind["H"][key] for key in ("H1", "H2", "H3")),
       "note": "Agreement checks implementation, not novelty, biological mechanism or drug benefit."}
for name, iname in (("A", "A"), ("B", "B"), ("Bprime", "B_prime")):
    a, b = root["candidates"][name], ind["candidates"][iname]
    qa, qb = a["Q1"]["value"], b["q1"]["result"]
    diffs = {"raw_mi_lb": a["raw_MI_LB"]["value"] - b["raw_mi_lb"]["result"]["score"],
             "merged_mi_lb": a["merged_MI_LB"]["value"] - b["exact_merged_mi_lb"]["result"]["score"],
             "threshold_bald": a["threshold_BALD"]["value"] - b["tau_bald"]["result"]["score"],
             "reference_mi": a["reference"]["value"]["MI"] - b["reference_mi"]["result"]["value"],
             **{key: qa[key] - qb[key] for key in ("L", "U", "width")}}
    row = {"signed_differences_root_minus_independent": diffs, "max_absolute_scalar_difference": max(map(abs, diffs.values())),
           "root_leaf_count": qa["leaf_count"], "independent_leaf_count": qb["leaf_count"]}
    if name == "A":
        row["guard_difference"] = "root equality guard before leaf construction:0 leaves; independent computes4 initial leaves then equality guard. Both output [0,0]; neither tests adaptive convergence on A."
    else:
        left = [item for item in evaluated if item["candidate"] == name]
        right = qb["computed_leaf_trace"]
        row["computed_leaf_order_equal"] = len(left) == len(right) and all(
            (float(x["lo"]), float(x["hi"])) == (float(y["a"]), float(y["b"])) for x, y in zip(left, right))
        row["computed_leaves"] = len(left)
        row["max_computed_leaf_L_difference"] = max(abs(x["L"] - y["L"]) for x, y in zip(left, right))
        row["max_computed_leaf_d_difference"] = max(abs(x["d"] - y["d"]) for x, y in zip(left, right))
        row["final_partition_equal"] = len(qa["final_partition"]) == len(qb["final_partition"]) and all(
            (float(x["lo"]), float(x["hi"])) == (float(y["a"]), float(y["b"]))
            for x, y in zip(qa["final_partition"], qb["final_partition"]))
        row["iteration_selected_fields_equal"] = len(qa["trace"]) == len(qb["iterations"]) and all(
            (None if "split" not in x else (float(x["split"][0]), float(x["split"][2]))) ==
            (None if y["selected"] is None else tuple(map(float, y["selected"])))
            for x, y in zip(qa["trace"], qb["iterations"]))
        actual_root = [(float(x["split"][0]), float(x["split"][2])) for x in qa["trace"] if "split" in x]
        actual_ind = [tuple(map(float, y["selected"])) for y in qb["iterations"] if y["stop"] is None]
        row["performed_split_sequence_equal"] = actual_root == actual_ind
        row["terminal_trace_difference"] = "Independent logs a potential next selected interval even on the terminal width_reached row; root omits it. No terminal split was performed."
    out["candidates"][name] = row
out["source_hashes"] = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                         for name in ("q1_run/results.json", "q1_run/receipt.json", "independent_q1/result.json", "independent_q1/execution_receipt.json")}
(HERE / "independent_comparison.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
