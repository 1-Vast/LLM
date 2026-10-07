"""Reconcile the immutable review with audit-only pre-freeze source edits."""
from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "boundary_acquisition_20261007"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    review = read(HERE / "FINAL_DRAFT_REVIEW.json")
    freeze = read(STUDY / "FREEZE.json")
    provided = read(STUDY / "REVIEW_DELTA_RECONSTRUCTION.json")
    restored, checks = {}, {}
    for name, row in provided["results"].items():
        raw = (STUDY / name).read_bytes()
        assert sha(raw) == row["frozen_current_sha256"]
        text = raw.decode("utf-8")
        for current, previous in row["reverse_substitutions"]:
            if "\r\n" in text:
                current, previous = current.replace("\n", "\r\n"), previous.replace("\n", "\r\n")
            assert text.count(current) == 1, name
            text = text.replace(current, previous)
        assert sha(text.encode()) == review["source_hashes"][name]
        restored[name] = text
        checks[name] = {"reviewed_sha256": sha(text.encode()), "frozen_sha256": sha(raw)}

    # Execute only the byte-exact reviewed protocol generator with its write
    # replaced by an in-memory capture. No reviewed or canonical file is changed.
    namespace = {"__file__": str(STUDY / "register.py"), "__name__": "review_generator_audit"}
    exec(compile(restored["register.py"], str(STUDY / "register.py"), "exec"), namespace)
    captured = []
    namespace["write"] = lambda path, obj: captured.append(obj)
    with contextlib.redirect_stdout(io.StringIO()):
        namespace["draft"]()
    reviewed_draft, canonical_draft = captured[0], read(STUDY / "DRAFT_PROTOCOL.json")
    altered_keys = [key for key in reviewed_draft if reviewed_draft[key] != canonical_draft[key]]
    assert altered_keys == ["created_utc", "permutation"]
    assert review["created_utc"] < freeze["created_utc"]

    duplicate_arrays = {}
    for name in ("training_arrays.npz", "fitted_models.npz", "nested_reference_diagnostic.npz",
                 "public_prior.npz", "evaluator_private.npz"):
        with np.load(STUDY / "packet1" / name) as first, np.load(STUDY / "packet2" / name) as second:
            assert first.files == second.files
            duplicate_arrays[name] = all(np.array_equal(first[key], second[key], equal_nan=True)
                                         for key in first.files)
            assert duplicate_arrays[name]

    receipt = {"created_utc": datetime.now(timezone.utc).isoformat(), "verdict": "PASS",
               "source_reconstruction": checks, "reviewed_generator_draft_changed_keys": altered_keys,
               "review_source_delta": "Permutation wording, finite/PSD audit output and elapsed time only; no fit, threshold, model or acquisition change.",
               "reviewed_draft_byte_identity_claimed": False,
               "canonical_protocol_sha256": freeze["protocol_sha256"],
               "canonical_execute_sha256": sha((STUDY / "execute.py").read_bytes()),
               "canonical": "Direct original frozen execute.py build packet2 and replay run1",
               "superseded": "Audit wrapper packet1 retained; no policy replay; array-identical to canonical packet2",
               "duplicate_array_equality": duplicate_arrays,
               "source_ordering_audit": "All training models, nested diagnostics and M0-derived tau are constructed and saved before build's target-context loop. Target outcomes enter only evaluator_private; no training refit occurs after that loop.",
               "target_freshness": "All five whole profiles were previously exposed; no fresh blindness claim."}
    with (HERE / "PROVENANCE_RECONCILIATION.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
