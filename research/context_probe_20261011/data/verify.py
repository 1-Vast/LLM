"""Independently check prepared arrays against source columns and manifest."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from prepare import SOURCE_PATHS, context_role, identity_groups, sha256


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main() -> None:
    manifest = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
    groups = json.loads((HERE / "drug_groups.json").read_text(encoding="utf-8"))
    eligible = [group for group in groups if group["eligible"]]
    with np.load(HERE / "output.npz", allow_pickle=False) as data:
        assert sha256(HERE / "output.npz") == manifest["output_npz_sha256"]
        assert sha256(HERE / "prepare.py") == manifest["prepare_sha256"]
        for source in manifest["sources"]:
            assert sha256(ROOT / source["path"]) == source["sha256"], source["path"]
        for filename, expected in manifest["derived_file_sha256"].items():
            assert sha256(HERE / filename) == expected, filename
        assert len(set(data["context_id"])) == len(data["context_id"])
        assert len(set(data["identity_key"])) == len(data["identity_key"])
        assert np.array_equal(data["role"], [context_role(key) for key in data["identity_key"]])
        assert np.array_equal(data["available"], np.isfinite(data["y"]))
        assert np.array_equal(data["drug_id"], [group["drug_id"] for group in eligible])
        assert np.isfinite(data["basal"]).all()
        assert all(group["eligible"] == (group["reference_observed_fraction"] >= 0.95) for group in groups)
        fractions = np.isfinite(data["y"][data["role"] == "reference"]).mean(axis=0)
        assert np.array_equal(fractions, [group["reference_observed_fraction"] for group in eligible])

        source = pd.read_csv(ROOT / SOURCE_PATHS["responses"], index_col=0)
        columns = [group["representative_column"] for group in eligible]
        expected = source.loc[data["context_id"], columns].to_numpy()
        assert np.array_equal(data["y"], expected, equal_nan=True)
        treatments = pd.read_csv(ROOT / SOURCE_PATHS["treatments"], keep_default_na=False)
        exact = treatments[(treatments.screen_id == "HTS") & (treatments.dose == 2.5)]
        rebuilt = identity_groups(exact.sample(frac=1, random_state=1826))
        assert [group["source_columns"] for group in rebuilt] == [group["source_columns"] for group in groups]
        assert [group["representative_column"] for group in rebuilt] == [group["representative_column"] for group in groups]
        used = treatments.set_index("column_name").loc[columns]
        assert (used.dose == 2.5).all() and (used.screen_id == "HTS").all()
        result = {
            "status": "PASS",
            "schema": "maestro.context_probe.data_verification.v1",
            "n_source_aligned_outcome_entries": int(data["y"].size),
            "n_contexts": len(data["context_id"]),
            "n_drugs": len(data["drug_id"]),
            "checks": [
                "Source, preparation, output and derived-file hashes match",
                "Every response entry, including NaN, exactly equals its designated source entry",
                "Every designated treatment is HTS at exactly 2.5 uM",
                "Metadata identity components and representatives are stable to row-order permutation",
                "Unique context identities and deterministic metadata-only roles",
                "Reference-only missingness threshold and evaluator availability masks match",
                "Basal inputs are finite; no prepared scaling or response feature fitting",
            ],
            "limitations": "This integrity check is not a model leakage test or an independent biological validation",
            "prepare_sha256": sha256(HERE / "prepare.py"),
            "output_npz_sha256": sha256(HERE / "output.npz"),
            "manifest_sha256": sha256(HERE / "MANIFEST.json"),
            "verify_sha256": sha256(Path(__file__)),
        }
    (HERE / "VERIFICATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
