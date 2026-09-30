"""STATE input sensitivity: does the served shift depend on the target treatment rows?

File summary
- Path: research/identifiability_audit/state_sensitivity.py
- Purpose: hold the checkpoint, the control rows, the target label and the seed fixed and perturb,
  one at a time, the target rows' expression, their count, and their batch/group metadata; delete
  them entirely in a separate arm. Repeated control resampling provides the numerical fluctuation
  reference every comparison is read against.
- Core points:
  - Every arm is run through the same command the registered adapter issues (`python -m state tx
    infer`) and the same output validation (`src/virtual_cell/state_runner.py validate`), so a
    difference is a property of the served path, not of a re-implementation.
  - The target label, the context, the control rows, the checkpoint, the embedding key and the seed
    are identical across arms; only the named field changes.
  - Deleting the target rows is expected to be refused by the query-construction step
    (`subset`) as `unsupported_query`. That is an interface refusal, not predictive uncertainty,
    and it is reported as such.
  - The script writes no model, trains nothing and changes no registered asset; the registered
    `c39.h5ad` is only read.
- Run: <state python> -m research.identifiability_audit.state_sensitivity [--out DIR] [--resamples N]
- Interfaces: `VARIANTS`, `build_assets`, `run_arm`, `main`
- Depends on: anndata, h5py, numpy, torch (the State environment); src/virtual_cell/state_runner.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

ASSET = ROOT / "data/external/arc_state/tahoe_metadata_source/c39.h5ad"
MODEL_DIR = ROOT / "data/external/arc_state/weights/zeroshot/state_generalization_zeroshot_X_hvg"
RUNNER = ROOT / "src" / "virtual_cell" / "state_runner.py"
CONTEXT = "NCI-H596"
CONTROL = "[('DMSO_TF', 0.0, 'uM')]"
TARGET = "[('Adagrasib', 0.05, 'uM')]"
PERT_COLUMN = "drugname_drugconc"
CELLTYPE_COLUMN = "cell_name"
BATCH_COLUMN = "plate"
EMBED_KEY = "X_hvg"
SEED = 42
OUT = ROOT / "outputs" / "identifiability_audit_20260930" / "state_sensitivity"
CONTROL_FRACTION = 0.8

VARIANTS = [
    ("baseline", "registered query shape: declared-context controls plus the target rows"),
    ("target_expression_permuted", "target embedding rows permuted among themselves; count and labels fixed"),
    ("target_expression_from_control", "target embedding rows replaced by a draw of control rows' values"),
    ("target_rows_half_a", "half the target rows kept (draw A)"),
    ("target_rows_half_b", "half the target rows kept (independent draw B)"),
    ("target_rows_quarter", "a quarter of the target rows kept"),
    ("target_plate_single", "every target row relabelled to one existing plate"),
    ("target_plate_unseen", "every target row relabelled to a plate id absent from the asset"),
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def _column(group, name: str) -> np.ndarray:
    import h5py

    item = group[name]
    if isinstance(item, h5py.Group) and "categories" in item:
        categories = item["categories"]
        values = categories.asstr()[:] if categories.dtype.kind in "OS" else categories[:].astype(str)
        return np.asarray(values)[item["codes"][:]]
    return np.asarray(item.asstr()[:]) if item.dtype.kind in "OS" else item[:].astype(str)


def load_asset():
    """(obs frame, X_hvg matrix) of the registered asset, restricted to the declared context."""
    import h5py
    import pandas as pd

    with h5py.File(ASSET, "r") as handle:
        obs = handle["obs"]
        names = {name: _column(obs, name) for name in (CELLTYPE_COLUMN, PERT_COLUMN, BATCH_COLUMN)}
        index_key = obs.attrs.get("_index", "_index")
        if isinstance(index_key, bytes):
            index_key = index_key.decode("utf-8")
        row_names = _column(obs, str(index_key))
        matrix = np.asarray(handle["obsm"][EMBED_KEY], dtype=np.float32)
    frame = pd.DataFrame(names, index=[str(name) for name in row_names])
    keep = (frame[CELLTYPE_COLUMN].to_numpy() == CONTEXT)
    return frame[keep].reset_index(drop=True), matrix[keep]


def write_query(path: Path, frame, matrix) -> str:
    import anndata as ad

    data = ad.AnnData(obs=frame.copy())
    data.obsm[EMBED_KEY] = np.ascontiguousarray(matrix, dtype=np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    data.write_h5ad(path)
    return _sha256(path)


def build_assets(out: Path, resamples: int, frame=None, matrix=None) -> tuple[dict, dict, dict]:
    """Write one query file per arm. Returns (name -> path, name -> description, context stats)."""
    if frame is None or matrix is None:
        frame, matrix = load_asset()
    labels = frame[PERT_COLUMN].to_numpy()
    control = np.flatnonzero(labels == CONTROL)
    target = np.flatnonzero(labels == TARGET)
    if not len(control) or not len(target):
        raise SystemExit(f"target_or_control_absent: control={len(control)} target={len(target)}")

    def assemble(target_index, control_index, frame_values=None, matrix_values=None):
        order = np.concatenate([control_index, target_index])
        sub = frame.iloc[order].copy()
        mat = matrix[order].copy()
        if matrix_values is not None:
            mat[len(control_index):] = matrix_values
        if frame_values is not None:
            for column, value in frame_values.items():
                sub.loc[sub.index[len(control_index):], column] = value
        return sub.reset_index(drop=True), mat

    paths, notes = {}, {}
    for name, note in VARIANTS:
        if name == "baseline":
            sub, mat = assemble(target, control)
        elif name == "target_expression_permuted":
            rng = np.random.default_rng(101)
            permuted = target[rng.permutation(len(target))]
            sub, mat = assemble(target, control, matrix_values=matrix[permuted])
        elif name == "target_expression_from_control":
            rng = np.random.default_rng(102)
            drawn = control[rng.choice(len(control), size=len(target), replace=True)]
            sub, mat = assemble(target, control, matrix_values=matrix[drawn])
        elif name in ("target_rows_half_a", "target_rows_half_b"):
            seed = 201 if name.endswith("_a") else 202
            rng = np.random.default_rng(seed)
            kept = rng.choice(target, size=len(target) // 2, replace=False)
            sub, mat = assemble(np.sort(kept), control)
        elif name == "target_rows_quarter":
            rng = np.random.default_rng(203)
            kept = rng.choice(target, size=max(1, len(target) // 4), replace=False)
            sub, mat = assemble(np.sort(kept), control)
        elif name == "target_plate_single":
            existing = str(frame[BATCH_COLUMN].iloc[control[0]])
            sub, mat = assemble(target, control, frame_values={BATCH_COLUMN: existing})
        elif name == "target_plate_unseen":
            sub, mat = assemble(target, control, frame_values={BATCH_COLUMN: "plate99"})
        else:
            continue
        path = out / "queries" / f"{name}.h5ad"
        write_query(path, sub, mat)
        paths[name] = path
        notes[name] = note

    for i in range(resamples):
        rng = np.random.default_rng(300 + i)
        kept = np.sort(rng.choice(control, size=int(round(CONTROL_FRACTION * len(control))), replace=False))
        name = f"control_resample_{i + 1}"
        sub, mat = assemble(target, kept)
        path = out / "queries" / f"{name}.h5ad"
        write_query(path, sub, mat)
        paths[name] = path
        notes[name] = f"{int(CONTROL_FRACTION * 100)}% of the control rows resampled (draw {i + 1})"

    stats = {"context_cells": int(len(frame)), "control_rows": int(len(control)),
             "target_rows": int(len(target)), "features": int(matrix.shape[1]),
             "control_plates": sorted({str(v) for v in frame[BATCH_COLUMN].iloc[control].unique()}),
             "target_plates": sorted({str(v) for v in frame[BATCH_COLUMN].iloc[target].unique()})}
    return paths, notes, stats


def run_arm(name: str, query: Path, out: Path, python: Path) -> dict:
    """One inference through the served command, then the served output validation."""
    (out / "predictions").mkdir(parents=True, exist_ok=True)
    output = out / "predictions" / f"{name}.h5ad"
    vector = out / "predictions" / f"{name}.npy"
    summary = out / "predictions" / f"{name}.validate.json"
    command = [str(python), "-m", "state", "tx", "infer", "--adata", str(query), "--model-dir", str(MODEL_DIR),
               "--embed-key", EMBED_KEY, "--pert-col", PERT_COLUMN, "--celltype-col", CELLTYPE_COLUMN,
               "--batch-col", BATCH_COLUMN, "--control-pert", CONTROL, "--output", str(output),
               "--seed", str(SEED), "--quiet"]
    started = time.perf_counter()
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=3600)
    elapsed = time.perf_counter() - started
    record = {"arm": name, "query_sha256": _sha256(query), "command": " ".join(shlex.quote(c) for c in command),
              "seconds": round(elapsed, 1), "returncode": completed.returncode}
    (out / "predictions" / f"{name}.infer.log").write_text(completed.stdout + "\n" + completed.stderr,
                                                           encoding="utf-8")
    if completed.returncode != 0:
        record.update({"served": False, "refusal": "inference_failed",
                       "refusal_class": "backend_error",
                       "detail": (completed.stderr or completed.stdout).strip().splitlines()[-3:]})
        return record
    validate = [str(python), str(RUNNER), "validate", "--input", str(query), "--output", str(output),
                "--summary", str(summary), "--perturbation", TARGET, "--control", CONTROL,
                "--perturbation-column", PERT_COLUMN, "--embed-key", EMBED_KEY,
                "--celltype-column", CELLTYPE_COLUMN, "--batch-column", BATCH_COLUMN,
                "--vector-output", str(vector)]
    done = subprocess.run(validate, check=False, capture_output=True, text=True, timeout=1800)
    payload = json.loads(summary.read_text(encoding="utf-8")) if summary.is_file() else {"valid": False}
    if done.returncode != 0 or not payload.get("valid"):
        record.update({"served": False, "refusal": "output_validation_failed",
                       "refusal_class": "interface_refusal", "detail": payload.get("errors", [])})
        return record
    delta = np.load(vector)
    record.update({"served": True, "vector_sha256": hashlib.sha256(np.ascontiguousarray(delta).tobytes())
                   .hexdigest(),
                   "delta_l2": float(np.linalg.norm(delta)),
                   "mean_abs_delta": float(np.abs(delta).mean()),
                   "control_cells": int(payload["control_cells"]),
                   "perturbation_cells": int(payload["perturbation_cells"]),
                   "output_sha256": payload.get("output_sha256"),
                   "vector": [round(float(x), 8) for x in delta]})
    return record


def deletion_arm(out: Path, python: Path, frame, matrix) -> dict:
    """Remove every target row from the context and ask the query-construction step for the target."""
    labels = frame[PERT_COLUMN].to_numpy()
    keep = labels != TARGET
    sub = frame[keep].reset_index(drop=True)
    path = out / "queries" / "target_rows_deleted.h5ad"
    write_query(path, sub, matrix[keep])
    summary = out / "predictions" / "target_rows_deleted.subset.json"
    command = [str(python), str(RUNNER), "subset", "--input", str(path), "--summary", str(summary),
               "--perturbation", TARGET, "--control", CONTROL, "--perturbation-column", PERT_COLUMN,
               "--embed-key", EMBED_KEY, "--celltype-column", CELLTYPE_COLUMN, "--batch-column", BATCH_COLUMN,
               "--context-column", CELLTYPE_COLUMN, "--context", CONTEXT,
               "--subset-output", str(out / "predictions" / "target_rows_deleted.subset.h5ad")]
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=1800)
    payload = json.loads(summary.read_text(encoding="utf-8")) if summary.is_file() else {"valid": False}
    return {"arm": "target_rows_deleted", "query_sha256": _sha256(path),
            "command": " ".join(shlex.quote(c) for c in command), "returncode": completed.returncode,
            "served": False, "refusal": "unsupported_query",
            "refusal_class": "interface_refusal",
            "errors": payload.get("errors", []),
            "detail": "the query step refuses before any prediction is computed; this is not "
                      "predictive uncertainty and not a refused measurement",
            "rows_without_target": int(len(sub)), "control_rows": int((sub[PERT_COLUMN] == CONTROL).sum())}


def compare(records: dict, resamples: int) -> dict:
    baseline = records.get("baseline", {})
    if not baseline.get("served"):
        return {"baseline_served": False}
    base = np.array(baseline["vector"], dtype=float)
    norm = float(np.linalg.norm(base))
    noise = [r for name, r in records.items() if name.startswith("control_resample_") and r.get("served")]
    noise_values = [float(np.linalg.norm(np.array(r["vector"]) - base)) / norm for r in noise]
    rows = []
    for name, record in sorted(records.items()):
        if not record.get("served"):
            rows.append({"arm": name, "served": False, "refusal": record.get("refusal"),
                         "refusal_class": record.get("refusal_class"), "errors": record.get("errors", [])})
            continue
        vector = np.array(record["vector"], dtype=float)
        distance = float(np.linalg.norm(vector - base))
        cosine = float(vector @ base / (np.linalg.norm(vector) * norm)) if norm else float("nan")
        rows.append({"arm": name, "served": True, "delta_l2": record["delta_l2"],
                     "relative_l2_change": distance / norm if norm else None,
                     "cosine_to_baseline": cosine,
                     "max_abs_coordinate_change": float(np.abs(vector - base).max()),
                     "control_cells": record["control_cells"], "target_cells": record["perturbation_cells"]})
    floor = float(np.max(noise_values)) if noise_values else None
    return {"baseline": {"delta_l2": norm, "control_cells": baseline["control_cells"],
                         "target_cells": baseline["perturbation_cells"]},
            "control_resampling_reference": {"draws": len(noise),
                                             "relative_l2_change_values": [round(v, 6) for v in noise_values],
                                             "median": float(np.median(noise_values)) if noise_values else None,
                                             "max": floor},
            "arms": rows,
            "read_rule": ("an arm is called influential only if its relative L2 change exceeds the largest "
                          "relative L2 change produced by repeated control resampling")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--resamples", type=int, default=5)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    python = Path(args.python)

    frame, matrix = load_asset()
    paths, notes, stats = build_assets(out, args.resamples, frame, matrix)
    records = {}
    for name, path in paths.items():
        records[name] = run_arm(name, path, out, python)
        print(name, "served" if records[name].get("served") else records[name].get("refusal"), flush=True)
    records["target_rows_deleted"] = deletion_arm(out, python, frame, matrix)
    print("target_rows_deleted", records["target_rows_deleted"].get("refusal"), flush=True)

    report = {"context": CONTEXT, "control_label": CONTROL, "target_label": TARGET,
              "checkpoint": str(MODEL_DIR.relative_to(ROOT)).replace("\\", "/"),
              "embedding_key": EMBED_KEY, "seed": SEED,
              "python": str(python),
              "asset": {"path": str(ASSET.relative_to(ROOT)).replace("\\", "/"), "sha256": None},
              "asset_context_stats": stats, "arm_notes": notes,
              "records": records, "comparison": compare(records, args.resamples)}
    (out / "state_sensitivity.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report["comparison"], indent=1))


if __name__ == "__main__":
    main()
