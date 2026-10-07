"""Independent reconstruction of C's signed endpoint from native source rows."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parent.parent
OLD = ROOT / "research/astra/state_dual_core_20261007/world"
OBS = STUDY / "observations"
sys.path.insert(0, str(ROOT / "src"))
from virtual_cell.state_runner import _column

def sha(p):
    with Path(p).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

start = time.perf_counter()
read = lambda p: json.loads(p.read_text())
plan = read(OLD / "metadata_freeze.json")
tech = read(OLD / "technical_screen_freeze.json")
contract = read(OLD / "contract.json")
ep = read(OBS / "ENDPOINT_PROTOCOL.json")
ef = read(OBS / "ENDPOINT_FREEZE.json")
receipt = read(OBS / "EXTRACTION_RECEIPT.json")
table = pd.read_csv(OBS / "bias_corrected_observations.csv")
array = np.load(OBS / "bias_corrected_observations.npz")
protected = [OLD / "metadata_freeze.json", OLD / "technical_screen_freeze.json", OBS / "ENDPOINT_PROTOCOL.json",
             OBS / "ENDPOINT_FREEZE.json", OBS / "bias_corrected_observations.csv", OBS / "bias_corrected_observations.npz"]
before = {str(p): sha(p) for p in protected}
checks = {
    "endpoint_protocol_hash": sha(OBS / "ENDPOINT_PROTOCOL.json") == ef["protocol_sha256"],
    "original_extraction_code_hash": sha(OBS / "extraction_source_original.py.txt") == ep["source_manifest"]["extraction_code"],
    "source_dataset_hash": sha(contract["hashes"]["dataset"]["path"]) == ep["source_manifest"]["source_h5ad"],
    "old_plan_hash": sha(OLD / "metadata_freeze.json") == ep["source_manifest"]["old_plan"],
    "old_technical_split_hash": sha(OLD / "technical_screen_freeze.json") == ep["source_manifest"]["old_technical_split"],
    "npz_receipt_hash": sha(OBS / "bias_corrected_observations.npz") == receipt["arrays_sha256"],
    "csv_receipt_hash": sha(OBS / "bias_corrected_observations.csv") == receipt["table_sha256"],
    "no_duplicate_condition_roles": not table.duplicated(["condition_id", "role"]).any(),
}
lookup = {(str(r.condition_id), r.role): r for r in table.itertuples()}
technical = {r["condition_id"]: r for r in tech["rows"]}
rebuilt = {"full": [], "screen": [], "technical_validation": []}
max_error = {key: 0.0 for key in ("signed_effect", "raw_squared_response", "treated_mean_gene_variance", "control_mean_gene_variance", "treated_noise_term", "control_noise_term", "crossproduct")}
identity_errors, cell_overlap = [], []
with h5py.File(contract["hashes"]["dataset"]["path"], "r") as f:
    labels = _column(f["obs"], "drugname_drugconc")
    plates = _column(f["obs"], "plate")
    contexts = _column(f["obs"], "cell_name")
    ids = _column(f["obs"], f["obs"].attrs["_index"])
    matrix = f["obsm"]["X_hvg"]
    for condition in plan["conditions"]:
        ref_rows = plan["controls"][condition["plate"]]["reference_rows"]
        ctrl = np.asarray(matrix[ref_rows], dtype=np.float64)
        roles = {"full": condition["treated_rows"]}
        if condition["condition_id"] in technical:
            tr = technical[condition["condition_id"]]
            roles.update(screen=tr["screen_rows"], technical_validation=tr["validation_rows"])
            if set(tr["screen_rows"]) & set(tr["validation_rows"]):
                cell_overlap.append(condition["condition_id"])
            assert set(tr["screen_rows"]) | set(tr["validation_rows"]) == set(condition["treated_rows"])
        for role, indices in roles.items():
            recorded = lookup[condition["condition_id"], role]
            x = np.asarray(matrix[indices], dtype=np.float64)
            assert len(x) > 1 and len(ctrl) > 1
            mx, mc = np.add.reduce(x, axis=0) / len(x), np.add.reduce(ctrl, axis=0) / len(ctrl)
            # Independently spell out Bessel-corrected variance via centered sums.
            vx = np.sum((x - mx) ** 2, axis=0) / (len(x) - 1)
            vc = np.sum((ctrl - mc) ** 2, axis=0) / (len(ctrl) - 1)
            raw = np.dot(mx-mc, mx-mc) / x.shape[1]
            tx, tc = np.sum(vx) / x.shape[1] / len(x), np.sum(vc) / x.shape[1] / len(ctrl)
            values = {"signed_effect": raw-tx-tc, "raw_squared_response": raw,
                      "treated_mean_gene_variance": vx.mean(), "control_mean_gene_variance": vc.mean(),
                      "treated_noise_term": tx, "control_noise_term": tc}
            for key, value in values.items():
                max_error[key] = max(max_error[key], abs(value-getattr(recorded, key)))
            identity_ok = (recorded.treated_n == len(x) and recorded.control_n == len(ctrl)
                and all(labels[i] == condition["label"] for i in indices)
                and all(plates[i] == condition["plate"] and contexts[i] == condition["cell"] for i in indices + ref_rows)
                and all(labels[i] == "[('DMSO_TF', 0.0, 'uM')]" for i in ref_rows)
                and recorded.subset_sha256 == hashlib.sha256(json.dumps([str(ids[i]) for i in indices]).encode()).hexdigest()
                and recorded.control_subset_sha256 == hashlib.sha256(json.dumps([str(ids[i]) for i in ref_rows]).encode()).hexdigest()
                and not set(indices) & set(ref_rows))
            if not identity_ok:
                identity_errors.append([condition["condition_id"],role])
            rebuilt[role].append((condition["condition_id"], float(raw-tx-tc)))
            if role == "full":
                order = sorted(range(len(x)), key=lambda i: hashlib.sha256(("corrected-crossproduct-v1:" + str(ids[indices[i]])).encode()).hexdigest())
                cross = np.dot(x[order[::2]].mean(0)-ctrl[::2].mean(0), x[order[1::2]].mean(0)-ctrl[1::2].mean(0)) / x.shape[1]
                position = len(rebuilt["full"]) - 1
                max_error["crossproduct"] = max(max_error["crossproduct"], abs(cross-array["independent_halves_crossproduct"][position]))
checks["all_cell_identity_and_disjoint_reference_checks"] = not identity_errors
checks["technical_halves_disjoint"] = not cell_overlap
checks["all_values_reproduce_at_1e12"] = max(max_error.values()) < 1e-12
for role, key, idkey in (("full", "signed_effect", "condition_id"), ("screen", "screen_signed_effect", "technical_condition_id"), ("technical_validation", "validation_signed_effect", "technical_condition_id")):
    checks[role + "_array_identity"] = array[idkey].tolist() == [x[0] for x in rebuilt[role]]
    checks[role + "_array_values"] = bool(np.allclose(array[key], [x[1] for x in rebuilt[role]], atol=1e-12, rtol=0))
checks["rows_144_48_48"] = {k:len(v) for k,v in rebuilt.items()} == {"full":144,"screen":48,"technical_validation":48}
checks["source_and_outputs_unchanged"] = all(sha(p) == before[str(p)] for p in protected)
orig_code = (OBS / "extraction_source_original.py.txt").read_text()
freeze_write = orig_code.index("write(OUT/'ENDPOINT_FREEZE.json'")
first_h5 = orig_code.index("with h5py.File")
checks["source_orders_endpoint_freeze_before_value_reads"] = freeze_write < first_h5
root_freeze = read(STUDY / "PROTOCOL_FREEZE.json") if (STUDY / "PROTOCOL_FREEZE.json").exists() else {}
report = {"independent_of_extraction_author": True, "verified_by": "workstream A, independently reconstructed native values",
    "created_utc": datetime.now(timezone.utc).isoformat(), "passed": bool(all(checks.values())),
    "checks": {k:bool(v) for k,v in checks.items()}, "max_absolute_errors": max_error,
    "negative_signed_counts": {k:sum(v<0 for _,v in rows) for k,rows in rebuilt.items()},
    "total_rows": {k:len(v) for k,v in rebuilt.items()}, "source_hashes": before,
    "chronology": {"endpoint_freeze_utc": ef["frozen_at_utc"], "root_freeze_receipt": root_freeze,
       "interpretation": "Endpoint source code writes its own freeze before source value reads. Root freeze was later; its wrong-path existence flag is not evidence of absence. Existing raw source exposure remains explicit; no corrected-outcome-dependent design selection is certified by filesystem timing alone."},
    "limitations": "Formula assumes iid cells, shared controls/technical halves are not independent cultures, signed negatives retained; correctness does not prove biological unbiasedness under correlated/QC-selected cells",
    "elapsed_seconds": time.perf_counter()-start, "new_api_calls":0, "new_download_bytes":0, "new_gpu_forwards":0}
(STUDY / "world/corrected_endpoint_independent_verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"passed":report["passed"], "rows":report["total_rows"], "max_error":max(max_error.values()), "negative_signed_counts":report["negative_signed_counts"]}))
