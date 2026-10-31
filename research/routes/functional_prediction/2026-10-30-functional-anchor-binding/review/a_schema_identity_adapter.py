"""Preserve original artifacts; derive metadata view for frozen verifier only.

This is an output-artifact identity check, not a retrospective input freeze.
The six reused label arrays must exactly match the preexecution pinned source,
and the added annotation flag must exactly match frozen pharmacology column213.
No model implementation is imported and no fits or HTTP requests are made.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    review = Path(__file__).resolve().parent
    repo = review.parents[4]
    original = repo / "data/processed/functional_anchor_binding_20261030/a"
    source = repo / "data/processed/conditional_interventions_20261030/cgi/stage1_corrected/labels.npz"
    pharmacology = review.parent / "pharmacology_features.npz"
    destination = review / "a_metadata_adapter"
    run = json.loads((original / "run.json").read_text(encoding="utf-8"))
    pins = run["freeze"]["sha256"]
    assert digest(source) == pins[str(source)], "preexecution source identity changed"
    assert digest(pharmacology) == pins[str(pharmacology)], "preexecution annotation identity changed"
    assert digest(review / "verify_a_independent.py") == "f9fb62590027c2f4638a1e0eb2d8fa13aa99eba3fc0a9e534d50f21faf63c61b"
    reused = ["compounds", "genes", "calls", "folds", "groups", "rounds"]
    equality = {}
    with np.load(source, allow_pickle=False) as old, np.load(original / "labels.npz", allow_pickle=False) as new, np.load(pharmacology, allow_pickle=False) as features:
        assert set(old.files) == set(reused)
        assert set(new.files) == set(reused + ["annotation_available"])
        for key in reused:
            assert old[key].dtype == new[key].dtype
            assert np.array_equal(old[key], new[key]), f"changed reused labels: {key}"
            equality[key] = {"dtype": str(old[key].dtype), "shape": list(old[key].shape), "exact_equal": True}
        assert np.array_equal(features["compounds"], new["compounds"])
        assert str(features["feature_names"][213]) == "annotation_available"
        assert np.all((features["features"][:, 213] == 0) | (features["features"][:, 213] == 1))
        assert new["annotation_available"].dtype.kind == "b"
        assert np.array_equal(features["features"][:, 213].astype(bool), new["annotation_available"])
    names = ["labels.npz", "ranks.npz", "permutation_assignments.npz", "summary.json",
             "decision.json", "teacher_diagnostics.json", "launcher.json"]
    destination.mkdir(exist_ok=False)
    output_hashes = {}
    for name in names:
        shutil.copy2(original / name, destination / name)
        assert digest(original / name) == digest(destination / name)
        output_hashes[name] = digest(original / name)
    # The only change to derived run metadata is this postrun output-copy hash.
    run["freeze"]["sha256"][str(destination / "labels.npz")] = output_hashes["labels.npz"]
    (destination / "run.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "status": "EXACT_REUSED_ARRAY_AND_ANNOTATION_IDENTITY_VERIFIED",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "reason": "Frozen verifier required output labels path in input pin manifest; original freeze correctly pinned the preexisting source file instead.",
        "original_verifier_failure": str(review / "a_arithmetic_verification.json"),
        "original_verifier_failure_sha256": digest(review / "a_arithmetic_verification.json"),
        "verifier_sha256": digest(review / "verify_a_independent.py"),
        "adapter_script_sha256": digest(__file__),
        "source_path": str(source), "source_sha256": digest(source),
        "pharmacology_path": str(pharmacology), "pharmacology_sha256": digest(pharmacology),
        "reused_arrays": equality, "annotation_available_exact_equal": True,
        "original_run_sha256": digest(original / "run.json"),
        "derived_run_sha256": digest(destination / "run.json"),
        "unchanged_original_output_hashes": output_hashes,
        "derived_data_dir": str(destination),
        "metadata_change": "Only freeze.sha256 adds derived labels.npz current output identity.",
        "interpretation": "Postrun output-artifact identity check; not a retrospective input pin or protocol amendment.",
        "original_outputs_modified": False, "refits": 0, "http_attempts": 0,
    }
    (review / "a_schema_adapter_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
