"""Fresh-process rerun in a temporary directory; never overwrites frozen results."""
import json
import tempfile
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

import compare


def main():
    original = compare.OUT
    with tempfile.TemporaryDirectory(prefix="map_release_repeat_") as temporary:
        compare.OUT = Path(temporary)
        for name in ("FEATURES.npz", "IDENTITIES.json"):
            (compare.OUT / name).write_bytes((original / name).read_bytes())
        with threadpool_limits(limits=1):
            compare.main()
        with np.load(original / "PREDICTIONS.npz") as a, np.load(compare.OUT / "PREDICTIONS.npz") as b:
            assert set(a.files) == set(b.files)
            for key in a.files:
                np.testing.assert_array_equal(a[key], b[key])
            count = len(a.files)
        for name in ("MODEL_CHOICES.json", "RESULTS.json", "DIAGNOSTICS.json"):
            assert json.loads((original / name).read_text()) == json.loads((compare.OUT / name).read_text()), name
        result = {"prediction_arrays_exact": count, "choices_results_diagnostics_exact": True,
                  "fresh_process": True, "production_files_changed": False}
    compare.OUT = original
    (original / "REPEAT_VERIFIED.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
