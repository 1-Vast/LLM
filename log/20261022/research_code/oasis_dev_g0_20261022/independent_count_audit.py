"""Supplemental count-source and pre-open-freeze audit; no other outcome roles."""
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/oasis_dev_g0"
DEST = OUT / "independent_audit/COUNT_AND_FREEZE.json"


def key(batch, plate, well):
    m = re.fullmatch(r"([A-Za-z]+)0*(\d+)", str(well))
    return str(batch).removeprefix("assayworks_"), str(plate), f"{m[1].upper()}{int(m[2]):02d}"


def main():
    assert not DEST.exists()
    dev = pd.read_parquet(OUT / "dev_wells_all_qc.parquet")
    controls = pd.read_csv(OUT / "plate_controls.csv")
    dev["key"] = [key(*r) for r in dev[["batch", "plate", "well"]].itertuples(index=False, name=None)]
    manifest = json.loads((ROOT / "log/20261021/oasis_identity_qualification/NEW_SOURCE_MANIFEST.json").read_text())
    item = next(x for x in manifest["files"] if x["name"] == "metadata.parquet")
    path = ROOT / item["local_path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    names = sorted(set(dev["compound_name"]) | {"DMSO"})
    meta = pq.read_table(path, columns=["Metadata_source", "Metadata_Plate", "Metadata_Well", "Metadata_Compound", "Metadata_Concentration", "Metadata_Count_Cells"],
                         filters=[("Metadata_Compound", "in", names)]).to_pandas()
    meta["key"] = [key(*r) for r in meta[["Metadata_source", "Metadata_Plate", "Metadata_Well"]].itertuples(index=False, name=None)]
    for _, rows in meta.groupby("key"):
        assert rows[["Metadata_Compound", "Metadata_Concentration", "Metadata_Count_Cells"]].nunique(dropna=False).le(1).all()
    meta = meta.drop_duplicates("key").set_index("key")
    selected = meta.reindex(dev["key"])
    np.testing.assert_allclose(selected["Metadata_Count_Cells"], dev["cell_count"], equal_nan=True, atol=0, rtol=0)
    matched = selected["Metadata_Compound"].notna().to_numpy()
    assert np.array_equal(selected.loc[matched, "Metadata_Compound"].to_numpy(), dev.loc[matched, "compound_name"].to_numpy())
    np.testing.assert_allclose(selected.loc[matched, "Metadata_Concentration"], dev.loc[matched, "dose_um"], atol=0, rtol=0)
    centers = {}
    for ident, rows in meta[meta["Metadata_Compound"].eq("DMSO")].groupby(lambda k: k[:2]):
        centers[ident] = float(np.median(np.log1p(rows["Metadata_Count_Cells"].to_numpy(float))))
    predicted_centers = np.array([centers.get((b, p), np.nan) for b, p in controls[["batch", "plate"]].itertuples(index=False, name=None)])
    np.testing.assert_allclose(predicted_centers, controls["count_log_center"], equal_nan=True, rtol=1e-12, atol=1e-12)
    valid = dev["observation_pass"]
    np.testing.assert_allclose(np.log1p(dev.loc[valid, "cell_count"])-dev.loc[valid, "count_log_center"], dev.loc[valid, "count_input"], atol=1e-12, rtol=1e-12)
    freeze = json.loads((OUT / "PRE_OPEN_FREEZE.json").read_text())
    mismatch = [name for name, expected in freeze["files"].items() if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected]
    assert not mismatch
    result = {"count_source_identity_and_values_exact": True, "count_control_center_and_input_recomputed": True,
              "frozen_input_hashes_match": len(freeze["files"]), "freeze_mismatches": mismatch,
              "missing_count_by_batch_plate": {"/".join(k): int(v) for k, v in dev[dev["cell_count"].isna()].groupby(["batch", "plate"]).size().items()},
              "scope": "Metadata count projection filtered to dev names or exact DMSO; freeze check hashes files without decoding their numerical roles",
              "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    DEST.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
