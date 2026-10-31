"""Authorized postaccess B audit with one declared roundoff-check change.

Neither the frozen source nor any numerical array is modified. Execute its
checks in a separate namespace with only the pooled bit-identity assertion
replaced by the explicitly authorized absolute bound plus exact action check.
The original freeze-review drift remains a separate, recorded exception.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    review = Path(__file__).resolve().parent
    frozen = review / "verify_b_independent.py"
    expected_sha = "82fd45c61ceae21162c3f65227dd1a4b3e8f1e490198eeb5159a18cea0aceec1"
    assert digest(frozen) == expected_sha
    source = frozen.read_text(encoding="utf-8")
    old = 'require(np.array_equal(predictions[4:6, :, 0], predictions[4:6, :, 1]), "pooled predictors identical across cells")'
    new = 'require(np.all(np.abs(predictions[4:6, :, 0] - predictions[4:6, :, 1]) <= 1e-12) and np.array_equal(np.sign(predictions[4:6, :, 0]), np.sign(predictions[4:6, :, 1])), "pooled predictors bounded roundoff and exactly identical actions across cells")'
    assert source.count(old) == 1, "unexpected frozen assertion source"
    derived = source.replace(old, new, 1)
    namespace = {"__file__": str(frozen), "__name__": "b_supplemental_derived_checks"}
    exec(compile(derived, str(frozen) + " [single declared postaccess assertion change]", "exec"), namespace)
    data = review / "b_review_metadata_adapter"
    original_data = review.parents[4] / "data/processed/functional_anchor_binding_20261030/b"
    pooled = {}
    with np.load(data / "predictions.npz", allow_pickle=False) as saved:
        for method in (4, 5):
            left, right = saved["predictions"][method, :, 0], saved["predictions"][method, :, 1]
            pooled[str(saved["methods"][method])] = {
                "nonidentical_IDs": int(np.sum(left != right)),
                "max_absolute_difference": float(np.max(np.abs(left - right))),
                "exact_signs_identical": bool(np.array_equal(np.sign(left), np.sign(right))),
            }
    try:
        result = namespace["verify"](data)
        result["status"] = "SUPPLEMENTAL_ARITHMETIC_PASS"
    except (namespace["ContractError"], OSError, KeyError, TypeError, ValueError) as exc:
        result = {"status": "SUPPLEMENTAL_ARITHMETIC_FAIL", "verification_pass": False, "error": str(exc)}
    result.update({
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "postaccess_supplemental_audit": True,
        "frozen_verifier_pass": False,
        "original_freeze_integrity_pass": False,
        "frozen_verifier_sha256": expected_sha,
        "supplemental_script_sha256": digest(__file__),
        "in_memory_derived_source_sha256": hashlib.sha256(derived.encode()).hexdigest(),
        "only_arithmetic_check_change": {"original": old, "replacement": new},
        "pooled_roundoff_diagnostics": pooled,
        "unchanged_checks": "All other frozen source checks executed without alteration using the isolated administrative-review metadata view.",
        "selection_and_gate_tolerance_changes": False,
        "numerical_arrays_modified": False, "refits": 0, "raw_profile_files_opened": 0,
        "exceptions": [
            "Original preexecution administrative-review document hash drift; first FAIL retained.",
            "Original exact pooled bit-identity assertion fails on <=4.45e-16 action-invariant roundoff; adapter FAIL retained.",
        ],
        "prior_reports_sha256": {
            name: digest(review / name) for name in (
                "b_arithmetic_verification.json", "b_arithmetic_verification_review_adapter.json",
                "b_review_pin_adapter_receipt.json", "b_verifier_freeze_receipt.json")
        },
        "original_output_sha256": {
            str(path): digest(path) for path in sorted(original_data.iterdir())
            if path.is_file() and path.suffix in {".json", ".npz"}
        },
        "limitations": [
            "This postaccess supplement is not a PASS of the unchanged frozen verifier or original full freeze chain.",
            "No raw-profile preprocessing, aggregation or byte-hash recertification; loader/source review owns those checks.",
            "Saved assay geometry does not establish causality, nuisance removal, independent biological replication or practical benefit.",
            "Bootstrap conditions on this dataset, saved predictions and selected comparator without refitting or shared-reference error.",
        ],
    })
    (review / "b_arithmetic_verification_supplemental.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result.get("verification_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
