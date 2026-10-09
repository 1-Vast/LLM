"""Exact fresh-process response rerun in a temporary output; preserve the trial."""
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time

import numpy as np
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT/"outputs/map_module_replacement_20261009/response"
ARTIFACTS = ("MODELS.npz", "PREDICTIONS.npz", "MODEL_CHOICES.json", "KERNEL_METADATA.json", "RESULTS.json", "SUMMARY.json")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(original, repeated):
    verified = {}
    for name in ARTIFACTS:
        if name.endswith(".npz"):
            with np.load(original/name) as a, np.load(repeated/name) as b:
                if a.files != b.files:
                    raise AssertionError("rerun_array_keys:"+name)
                for key in a.files:
                    np.testing.assert_array_equal(a[key], b[key], err_msg=name+":"+key)
                verified[name] = dict(exact_arrays=len(a.files))
        else:
            a, b = json.loads((original/name).read_text()), json.loads((repeated/name).read_text())
            if name == "SUMMARY.json":
                a.pop("seconds"); b.pop("seconds")
            if a != b:
                raise AssertionError("rerun_json_difference:"+name)
            verified[name] = dict(exact_scientific_content=True)
    return verified


def main():
    receipt = OUT/"REPEAT_VERIFIED.json"
    if receipt.exists():
        raise RuntimeError("Refuse to overwrite repeat verification")
    repeat_freeze = json.loads((HERE/"REPEAT_FREEZE.json").read_text())
    for name, expected in repeat_freeze["inputs"].items():
        if digest(ROOT/name) != expected:
            raise ValueError("repeat_freeze_mismatch:"+name)
    before = {name: digest(OUT/name) for name in ARTIFACTS}
    started = time.perf_counter()
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location("exact_response_repeat", HERE/"run.py")
    study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)
    with tempfile.TemporaryDirectory(prefix="map_response_exact_repeat_") as temporary:
        target = Path(temporary)/"response"
        study.OUT = target  # Non-existing temporary child; all scientific inputs unchanged.
        with (Path(temporary)/"rerun.log").open("w", encoding="utf-8") as log:
            with contextlib.redirect_stdout(log), threadpool_limits(limits=1):
                study.main()
        verified = compare(OUT, target)
    after = {name: digest(OUT/name) for name in ARTIFACTS}
    if after != before:
        raise AssertionError("original_trial_artifacts_changed")
    result = dict(status="EXACT_FRESH_RESPONSE_RERUN_VERIFIED", frozen_at_utc=repeat_freeze["frozen_at_utc"],
                  completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  verified=verified, original_artifact_sha256=after, original_trial_preserved=True,
                  original_input_freeze_checked_by_frozen_run=True, seconds=time.perf_counter()-started,
                  exclusions="Only nondeterministic runtime seconds excluded from SUMMARY comparison; no scientific field excluded.")
    with receipt.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
