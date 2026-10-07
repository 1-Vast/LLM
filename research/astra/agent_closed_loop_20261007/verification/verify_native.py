"""Check fresh STATE output vectors and input lineage without study imports."""
from pathlib import Path
import argparse
import hashlib
import json
from datetime import datetime, timezone

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
STUDY = ROOT / "research/astra/agent_closed_loop_20261007"
PRIOR = ROOT / "research/astra/zeroshot_context_20261007"
CACHE = ROOT / "data/external/tahoe_zeroshot_20261007"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = read(STUDY / "native_state_check.json")
    assert sha(STUDY / "native_state_check.npz") == receipt["arrays_sha256"]
    assert sha(receipt["checkpoint"]["path"]) == receipt["checkpoint"]["sha256"]
    protocol = read(STUDY / "PROTOCOL.json")
    expected = [(case["context"], case["file"], case["label"], plate) for case in protocol["cases"]
                for plate in (case["first_plate"], case["independent_plate"])]
    assert receipt["native_drug_forwards"] == len(expected) == 8
    assert receipt["native_control_forwards"] == len({(file, plate) for _, file, _, plate in expected}) == 6
    native = np.load(STUDY / "native_state_check.npz", allow_pickle=False)["paired_delta"]
    assert native.shape == (8, 2000) and np.isfinite(native).all()
    for index, (context, file, label, plate) in enumerate(expected):
        row = receipt["cases"][index]
        assert (row["context"], row["label"], row["plate"]) == (context, label, plate)
        with np.load(CACHE / "state_forecasts" / f"{file}.npz", allow_pickle=False) as cached:
            match = np.flatnonzero((cached["label"] == label) & (cached["plate"] == plate))
            assert len(match) == 1
            difference = float(np.max(np.abs(native[index] - cached["paired_delta"][match[0]])))
            assert difference == row["max_abs_difference_from_cached"] == 0.0
        plan = read(CACHE / "extract/plans" / f"{file}.plan.json")
        control = next(group for group in plan["groups"] if group["control"] and group["plate"] == plate)
        eligible = [i for i, (role, full) in enumerate(zip(control["control_role"], control["full"]))
                    if role == "basal" and full]
        seed = int(hashlib.sha256(f"basal256:{file}:{plate}".encode()).hexdigest()[:8], 16)
        pick = np.random.RandomState(seed).choice(len(eligible), 256, replace=len(eligible) < 256)
        with np.load(CACHE / "extract" / file / "slots.npz", allow_pickle=False) as slots:
            start = dict(zip(slots["group"].tolist(), slots["start"].tolist()))
        stored = np.load(CACHE / "extract" / file / "rows.npy", mmap_mode="r")
        inputs = np.asarray(stored[[start[control["group"]] + eligible[i] for i in pick]], dtype=np.float32)
        assert hashlib.sha256(inputs.tobytes()).hexdigest() == row["basal_input_sha256"]
        source_rows = [int(control["rows"][eligible[i]]) for i in pick]
        previous = read(PRIOR / "state_forecasts" / f"{file}.receipt.json")["basal"][plate]
        assert source_rows == previous["source_rows"]
        assert row["basal_cells"] == 256
    result = dict(verdict="PASS", created_utc=datetime.now(timezone.utc).isoformat(),
        native_vectors_checked=8, native_coordinate_count=2000, basal_inputs_checked=8,
        native_drug_forwards=8, native_control_forwards=6, max_abs_difference=0.0,
        checkpoint_sha256=receipt["checkpoint"]["sha256"],
        scope="Independent saved-output and raw-basal-input verification; did not repeat GPU inference.",
        scientific_boundary="Exposed development model reproduction, not independent biological utility.")
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2); handle.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
