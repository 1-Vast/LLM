"""Review sealed artifacts only; do not open the raw ZIP or fit any model."""
from collections import Counter
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DS = HERE.parent / "deepseek/tasks/DS028"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


freeze = read(HERE / "execution_freeze.json")
for filename, key in [("protocol_hfi_v1.md", "protocol_sha256"),
                      ("protocol_clarifications.md", "clarifications_sha256"),
                      ("menu_roles_frozen.json", "menu_roles_sha256"),
                      ("run_primary.py", "primary_script_sha256"),
                      ("protocol_challenge.md", "protocol_admission_record_sha256")]:
    assert digest(HERE / filename) == freeze[key], filename
ind_freeze = read(HERE / "independent_hfi_implementation_freeze.json")
for filename, key in [("independent_hfi_run.py", "script_sha256"),
                      ("independent_hfi_interpretation.md", "interpretation_sha256"),
                      ("independent_hfi_launch.ps1", "launcher_sha256")]:
    assert digest(HERE / filename) == ind_freeze[key], filename
for filename, expected in ind_freeze["input_sha256"].items():
    assert digest(HERE / filename) == expected, filename
selection_freeze = read(HERE / "independent_hfi_selection_freeze.json")
for filename, expected in selection_freeze["artifact_sha256"].items():
    assert digest(HERE / filename) == expected, filename
assert digest(HERE / "independent_hfi_oof.npz") == selection_freeze["oof_sha256"]
ind = read(HERE / "independent_hfi_result.json")
assert digest(HERE / "independent_hfi_selection_freeze.json") == ind["selection_freeze_sha256"]
primary = read(HERE / "primary_training_selection.json")
summary = read(HERE / "primary_summary.json")
drugs = primary["drugs"]
models = read(HERE / "independent_hfi_model_selection.json")
families = ["constant", "knn5", "knn20", "knn50", "pav_increasing", "pav_decreasing"]
with np.load(HERE / "independent_hfi_oof.npz", allow_pickle=False) as arrays:
    labels = arrays["train_labels"]
    assert labels.shape == (529, 11)
    assert arrays["drugs"].tolist() == drugs
    for model in models:
        j, t = drugs.index(model["input"]), drugs.index(model["target"])
        probabilities = arrays["all_probabilities"][j, t]
        assert np.isfinite(probabilities).all()
        errors = np.count_nonzero((probabilities >= .5) != labels[:, t], axis=1)
        assert errors.tolist() == [model["family_errors"][f] for f in families]
        k = int(np.argmin(errors))
        assert model["selected"] == families[k]
        assert int(primary["choice_matrix"][j][t]) == k
    pairs = read(HERE / "independent_hfi_pair_support.json")
    for pair in pairs:
        a, b = drugs.index(pair["a"]), drugs.index(pair["b"])
        counts = np.bincount(labels[:, a] * 2 + labels[:, b], minlength=4).tolist()
        assert counts == pair["state_counts_00_01_10_11"]
        assert pair["eligible"] == (min(counts) >= 10)
pair_map = {(p["a"], p["b"]): p for p in pairs}
triples = read(HERE / "independent_hfi_candidate_triples.json")
triple_map = {(t["a"], t["b"], t["q"]): t for t in triples}
assert len(primary["candidates"]) == len(triple_map) == 27
for candidate in primary["candidates"]:
    key = tuple(drugs[candidate[k]] for k in ("a", "b", "q"))
    other = triple_map[key]
    assert candidate["errors"] == other["error_totals"]
    assert candidate["minimum_error_count_gain"] == other["minimum_margin_integer"]
    assert candidate["joint_state_counts"] == pair_map[key[:2]]["state_counts_00_01_10_11"]
best = min(triples, key=lambda t: (-t["minimum_margin_integer"], t["a"], t["b"], t["q"]))
assert ind["best"] == best
assert tuple(drugs[primary["candidates"][0][k]] for k in ("a", "b", "q")) == tuple(best[k] for k in ("a", "b", "q"))
assert summary["status"] == ind["status"] == "training_precondition_absent"
assert summary["H_FI"] == "not_evaluated_on_development"
assert not ind["development_effects_evaluated"]
pq, iq = read(HERE / "primary_qc.json"), read(HERE / "independent_hfi_qc.json")
for pk, ik in [("rows", "raw_rows"), ("selected_appearances", "selected_occurrences"),
               ("unique_coordinates", "selected_unique_coordinates"),
               ("finite_outside_zero_one", "out_of_unit_interval")]:
    assert pq[pk] == iq[ik]
assert pq["repeated_appearances"] == iq["selected_occurrences"] - iq["selected_unique_coordinates"]
assert read(HERE / "independent_hfi_process_receipt.json")["status"] == "completed"
assert read(HERE / "independent_hfi_resource_receipt.json")["exit_code"] == 0
assert read(HERE / "primary_execution.json")["exit_code"] == 0
assert not (HERE / "primary_development.json").exists()
assert not (HERE / "independent_hfi_development_policy_log.json").exists()
assert not (HERE / "independent_hfi_bootstrap.npz").exists()
save(HERE / "numeric_comparison.json", {
    "reviewer": "root; artifact comparison after both implementations sealed",
    "raw_data_opened_by_this_review": False, "model_fits_or_effect_replays": 0,
    "independent_implementation_primary_reads_before_seal": ind_freeze["primary_reads"],
    "primary_and_independent_selected_families_equal": len(models),
    "independent_saved_OOF_family_error_counts_recomputed": len(models) * 6,
    "independent_saved_pair_support_counts_recomputed": len(pairs),
    "primary_and_independent_eligible_candidate_counts_equal": len(triples),
    "QC_aggregate_counts_equal": True, "best": best,
    "development_scoring_or_bootstrap": False,
    "comparison_limits": [
        "Primary did not save complete OOF probabilities; no claim of bytewise full-OOF agreement",
        "Primary stopped before final refits; independent saved 110 final models. No development use of either",
        "Independent worker delivered sealed results then hit native usage limit; parent completed comparison",
        "Code/numeric independence is not independent biological evidence or algorithmic novelty"
    ],
    "frozen_sha256_verified": True
})

packet, reply = read(DS / "source_packet.json"), read(DS / "final.md")
assert reply["rows"] == packet["rows"]
for row in reply["rows"]:
    ratio = str((Decimal(row["numerator"]) / Decimal(row["denominator"])).quantize(Decimal(".000001"), rounding=ROUND_HALF_EVEN))
    assert ratio == row["ratio6"]
for key in ("run_status", "H_status"):
    assert reply[key] == packet[key]
assert reply["ambiguities"] == []
receipt, usage = read(DS / "receipt.json"), read(DS / "usage.json")
assert receipt["exit_code"] == 0 and receipt["state"] == "exited"
assert digest(DS / "events.jsonl") == receipt["events_sha256"]
assert digest(DS / "prompt.txt") == receipt["prompt_sha256"]
for filename, expected in packet["source_sha256"].items():
    assert digest(HERE / filename) == expected
events = [json.loads(line) for line in (DS / "events.jsonl").read_text(encoding="utf-8-sig").splitlines()]
counts = Counter((e.get("type"), e.get("phase")) for e in events)
finals = [e for e in events if e["type"] == "final"]
assert len(finals) == 1 and counts["status", "step_end"] == 1
assert json.loads(finals[0]["text"]) == reply
save(DS / "format_checks.json", {
    "rows_exact": 5, "fixed_fields_exact": 35, "status_fields_exact": 2,
    "Decimal_ratios_exact": 5, "final_events": 1, "step_end_events": 1,
    "source_event_prompt_hashes_verified": True,
    "reported_usage": usage["reported_usage"],
    "scope": "Root supplied canonical values; transcription and deterministic arithmetic check only, not independent scientific validation"
})
print(json.dumps({"models_equal": len(models), "candidates_equal": len(triples),
                  "training_stop": summary["status"], "DS028_fixed_fields": 35}))
