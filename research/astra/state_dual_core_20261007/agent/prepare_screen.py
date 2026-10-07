"""Bind actual disjoint technical screen/validation observations to frozen forecasts."""
import argparse
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd

from replay import digest, load_records


def prepare(study, output):
    forecasts = load_records(study / "model_run1/decision_records.csv").set_index("condition_id")
    protocol = json.loads((study / "world/technical_screen_freeze.json").read_text())
    screen = np.load(study / "world/technical_screen_values.npz", allow_pickle=False)
    validation = np.load(study / "world/technical_validation_values.npz", allow_pickle=False)
    assert np.array_equal(screen["condition_id"], validation["condition_id"])
    originals = {row["condition_id"]: row for row in protocol["rows"]}
    rows = []
    provenance = {name: sha256((study / name).read_bytes()).hexdigest() for name in (
        "world/contract.json", "world/state_features.npz", "world/technical_screen_freeze.json",
        "model_run1/model_selection.json", "model_run1/kernels.npz", "model_run1/predictions.npz")}
    for index, identifier in enumerate(screen["condition_id"]):
        source = originals[str(identifier)]
        assert not set(source["screen_cell_ids"]) & set(source["validation_cell_ids"])
        for role, key, values in (("screen", "screen_magnitude", screen),
                                  ("technical_validation", "validation_magnitude", validation)):
            row = forecasts.loc[str(identifier)].to_dict()
            row["condition_id"] = str(identifier) + ("-screen" if role == "screen" else "-validation")
            row["original_condition_id"] = str(identifier)
            row["response_role"] = role
            row["model_provenance_sha256"] = digest(provenance)
            row["subset_sha256"] = digest(source["screen_cell_ids" if role == "screen" else "validation_cell_ids"])
            row["observed_rms"] = float(values[key][index])
            rows.append(row)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    table = pd.DataFrame(rows)
    # Split pseudobulk magnitude has different sampling noise from the full-cell
    # training endpoint. Recenter both world columns using training drugs only.
    corrections = {}
    for role in ("screen", "technical_validation"):
        train = (table.response_role == role) & (table.split == "train")
        selected = table.response_role == role
        for world in ("reference", "state"):
            column = world + "_prediction"
            offset = float((table.loc[train, "observed_rms"] - table.loc[train, column]).mean())
            table.loc[selected, column] += offset
            corrections[role + ":" + world] = offset
    table.to_csv(output, index=False)
    output.with_suffix(".calibration.json").write_text(json.dumps({"training_only_endpoint_offsets": corrections,
        "model_provenance": provenance,
        "basis": "training drug mean residual for each technical subset role; zero tuning"}, indent=2), encoding="utf-8")
    return {"rows": len(rows), "source": protocol["source_sha256"],
            "independence": protocol["independence"], "split_reference_denominator": "shared fixed control mean"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.study, args.output), indent=2))
