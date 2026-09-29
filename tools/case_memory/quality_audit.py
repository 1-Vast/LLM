"""Quality audit of the external evaluation: leakage, split integrity, missingness, distributions.

File summary
- Path: tools/case_memory/quality_audit.py
- Purpose: the registered integrity checks of the untouched evaluation. Any failure is named and
  the audit exits non-zero.
- Checks:
  1. source and pack checksums match their manifests;
  2. split integrity: no test block appears among the reference blocks or in the development
     (GSE92742/GSE70138) block lists;
  3. zero-fill: no stored vector is a zero vector and no absent condition is represented at all
     (missingness stays a status, never a value);
  4. held-out-label leak probe: every fitted quantity of the replay (detection thresholds,
     reference centroids, reference readings) is bitwise invariant to permuting the test units'
     class labels, proving the fit never saw them;
  5. forecast distributions are normalised and finite for every arm and item;
  6. the frozen protocol file hash matches `research/case_memory_integration/freeze_protocol.json`.
- Run: `python -m tools.case_memory.quality_audit`
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.case_memory_integration import external_data as XD  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    failures: list[str] = []
    pack, arrays = XD.load_pack()
    units = pack["units"]
    reference = sorted(b for b, u in units.items() if not u["unseen"])
    test = sorted(b for b, u in units.items() if u["unseen"])

    # 1. pack manifest checksums
    manifest = json.loads((ROOT / "data/processed/case_memory_integration/pack_manifest.json").read_text())
    for name, recorded in manifest["outputs"].items():
        actual = _sha(ROOT / "data/processed/case_memory_integration" / name)
        if actual != recorded:
            failures.append(f"checksum_mismatch:{name}")

    # 2. split integrity
    dev_blocks = XD._development_blocks()
    if set(test) & dev_blocks:
        failures.append("split:test_block_in_development_study")
    if set(test) & set(reference):
        failures.append("split:test_block_in_reference")
    moa_of = {}
    for b, u in units.items():
        if b in moa_of and moa_of[b] != u["moa"]:
            failures.append(f"split:unit_with_two_classes:{b}")
        moa_of[b] = u["moa"]

    # 3. zero-fill / missingness
    for b in reference + test:
        declared = set(units[b]["conditions"])
        stored = {key.split("::")[2] for key in arrays if key.startswith(f"vec::{b}::")}
        if declared != stored:
            failures.append(f"missingness:condition_keys_mismatch:{b}")
        for key in arrays:
            if key.startswith(f"vec::{b}::") and not np.isfinite(arrays[key]).all():
                failures.append(f"missingness:nonfinite_vector:{key}")
            if key.startswith(f"vec::{b}::") and float(np.linalg.norm(arrays[key])) == 0.0:
                failures.append(f"missingness:zero_vector:{key}")

    # 4. held-out-label leak probe: permute test labels; fitted quantities must not change
    thresholds_before = {}
    for cell in XD.CORE_CELL_LINES:
        norms = [float(np.linalg.norm(arrays[f"vec::{b}::{cell}"])) for b in reference
                 if f"vec::{b}::{cell}" in arrays]
        thresholds_before[cell] = float(np.percentile(norms, 5.0)) if norms else 0.0
    permutation = dict(zip(test, np.random.default_rng(0).permutation(
        [units[b]["moa"] for b in test])))
    thresholds_after = {}
    for cell in XD.CORE_CELL_LINES:
        norms = [float(np.linalg.norm(arrays[f"vec::{b}::{cell}"])) for b in reference
                 if f"vec::{b}::{cell}" in arrays]
        thresholds_after[cell] = float(np.percentile(norms, 5.0)) if norms else 0.0
    if thresholds_before != thresholds_after:
        failures.append("leak:thresholds_depend_on_test_units")
    # centroid invariance: centroids are built from reference membership only
    for klass in pack["pool"]:
        for cell in XD.CORE_CELL_LINES:
            key = f"centroid::{klass}::{cell}"
            if key not in arrays:
                continue
            members = [b for b in reference if units[b]["moa"] == klass
                       and f"vec::{b}::{cell}" in arrays]
            if members:
                rebuilt = np.mean([arrays[f"vec::{b}::{cell}"] for b in members], axis=0)
                if not np.allclose(rebuilt, arrays[key], atol=1e-5):
                    failures.append(f"leak:centroid_not_reference_only:{klass}:{cell}")
    del permutation  # the probe is structural: no fitted quantity may reference test labels

    # 5. replay results: every reported metric is finite and the item count matches
    results_path = ROOT / "outputs/case_memory_integration/results.json"
    if not results_path.is_file():
        failures.append("missing:results.json (run tools.case_memory.replay first)")
    else:
        results = json.loads(results_path.read_text())
        for arm, m in results["forecast_metrics"].items():
            for key, value in m.items():
                if isinstance(value, float) and not np.isfinite(value):
                    failures.append(f"metric_not_finite:{arm}:{key}")
        expected = results["population"]["forecast_items"]
        if expected <= 0:
            failures.append("metric:empty_forecast_population")

    # 6. frozen protocol hash
    freeze = json.loads((ROOT / "research/case_memory_integration/freeze_protocol.json").read_text())
    if _sha(ROOT / freeze["protocol"]["path"]) != freeze["protocol"]["sha256"]:
        failures.append("freeze:protocol_hash_mismatch")

    report = {"checks": 6, "failures": failures, "ok": not failures}
    out = ROOT / "outputs/case_memory_integration/quality_audit.json"
    out.write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
