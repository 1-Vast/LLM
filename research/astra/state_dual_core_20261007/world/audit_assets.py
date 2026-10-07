"""Create content-bound STATE source/capability and cache benchmark receipts."""
from pathlib import Path
import hashlib
import json
import time
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

contract = json.loads((OUT / "contract.json").read_text())
source = ROOT / "data/external/arc_state/source"
sources = [{"path": str(p.relative_to(ROOT)), "sha256": sha(p), "bytes": p.stat().st_size}
           for p in sorted(source.rglob("*.py"))]
for name in ("pyproject.toml", "MODEL_LICENSE.md", "MODEL_ACCEPTABLE_USE_POLICY.md", "LICENSE"):
    p = source / name
    sources.append({"path": str(p.relative_to(ROOT)), "sha256": sha(p), "bytes": p.stat().st_size})
write(OUT / "source_manifest.json", {"source_tree_sha256": hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest(),
      "source_version": "arc-state 0.11.3 editable source snapshot", "git_commit": None,
      "git_provenance_limitation": "source directory has no nested .git; parent repository HEAD must not be mistaken for upstream STATE revision", "files": sources})
registry = json.loads((ROOT / "data/virtual_cell/registry.json").read_text())
manifest = {"checkpoint": contract["hashes"], "model": registry["models"]["state_generalization_zeroshot_X_hvg"],
    "corrected_official_repository": {"id": "arcinstitute/ST-HVG-Tahoe",
        "evidence": "tools/datasets/audit_results/20261001_state_response/source_index.json and REPORT.md",
        "historical_registry_attribution": "ST-Tahoe was an older inferred attribution, corrected by official recovery on 2026-10-01"},
    "input": {"key": "X_hvg", "dimensions": 2000, "named_coordinates": 1969, "unresolved_coordinates": contract["unresolved_coordinates"],
              "input_basis": "official pinned c39 matrix only", "new_rna_certified": False,
              "preprocessing": "official processed coordinates; 1969 match log1p(X); full raw normalization and 31 coordinate identities unresolved",
              "controls": "disjoint same-plate basal/reference halves; 32 basal draws with replacement, fixed seed 731"},
    "perturbations": {"encoding": "1138 one-hot complete drug-dose labels including control", "continuous_dose": False,
                      "continuous_time": False, "combination_support": False, "unknown_drug_support": False},
    "conditions": {"registered_context": "NCI-H596", "exposure_hours": 24, "source": "Tahoe-100M",
                   "endpoint": "predicted native X_hvg mean and intervention minus sampled basal mean",
                   "ATP_viability_or_synergy": False, "batch_encoder": False, "batch_match_is_explicit_learned_batch_model": False},
    "interfaces": ["encode_basal_expression", "encode_perturbation", "predict_step(batch,padded=False)", "forward"],
    "inference_window": {"training_cell_set_len": 256, "study_cells": 32,
                         "support": "official CLI uses variable homogeneous windows, padded=False, including short remainder windows",
                         "not_claimed": "equivalence to 256-cell distributional evaluation or complete CLI postprocessing (clip to 14)"},
    "validation": {"registered_receipts": registry.get("receipts", []), "new_unexposed_confirmation": False,
                   "prior_scale_calibration_used": False, "interval_coverage": "no checkpoint-native calibrated uncertainty receipt"},
    "training_overlap": {"training_source": "Tahoe", "checkpoint_split_asset": "/data/tahoe_se/generalization_zeroshot.toml unavailable locally",
                         "recovered_related_split": "tools/datasets/audit_results/20261001_state_response/material/actual_tahoe_split_v2.raw",
                         "related_split_sha256": "83ee774e7e3709d3fa123e279685905dd055c4b900df8155c4c4b1047ef6f37c",
                         "related_split_semantics": "Official zeroshot/generalization.toml does not list NCI-H596 as cell-type holdout; different filename from config prevents exact training exposure proof",
                         "c39_overlap": "unknown, likely training context; previously exposed locally", "held_out_claim": "downstream chemistry-group split only"},
    "license": "Arc State Model Non-Commercial License, 2025-06-23; code separate license",
    "source_manifest": "world/source_manifest.json"}
if (OUT / "runtime_architecture.json").exists():
    manifest["runtime"] = json.loads((OUT / "runtime_architecture.json").read_text())
write(OUT.parent / "state_capability_manifest.json", manifest)
if (OUT / "state_features.npz").exists():
    times, arrays = [], None
    for _ in range(5):
        start = time.perf_counter()
        with np.load(OUT / "state_features.npz") as f:
            fresh = {key: f[key].copy() for key in f.files}
        times.append(time.perf_counter() - start)
        if arrays is not None:
            assert all(np.array_equal(fresh[key], arrays[key]) for key in arrays)
        arrays = fresh
    trace = json.loads((OUT / "forward_trace.json").read_text())
    identity = {"checkpoint": contract["hashes"]["weights"]["sha256"], "config": contract["hashes"]["config"]["sha256"],
                "feature_axis": contract["hashes"]["axis"]["sha256"], "dataset": contract["hashes"]["dataset"]["sha256"],
                "basal": sha(OUT / "basal_controls.npz"), "conditions_with_dose_unit_time_assay_readout": sha(OUT / "conditions.csv"),
                "plan_seed_and_sampling": sha(OUT / "metadata_freeze.json"), "execution_code": sha(OUT / "execution_source.py.txt"),
                "source_tree": hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()}
    write(OUT / "cache_identity.json", {"fields": identity, "key": hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest(),
          "artifact_sha256": sha(OUT / "state_features.npz")})
    write(OUT / "cache_benchmark.json", {"cache_read_seconds": times, "median_cache_read_seconds": float(np.median(times)),
          "sum_forward_seconds_144_conditions": sum(x["seconds"] for x in trace),
          "forward_seconds_median": float(np.median([x["seconds"] for x in trace])),
          "numerical_cache_consistency": "bitwise exact all arrays", "scope": "warm local NPZ cache vs actual completed model forwards; model loading excluded", "financial_cost_usd": None})
print("audited", len(sources), "source files")
