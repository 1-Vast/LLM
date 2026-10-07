"""Validation helper executed inside MAESTRO's isolated State environment.

File summary
- Path: src/virtual_cell/state_runner.py
- Purpose: inspect, subset and validate State input/output AnnData so the
  controller cannot accept a fallback, a wrong context or a wrong input schema
  as a real prediction.
- Core points:
  - Runs in the State environment, importing nothing from MAESTRO.
  - Rejects a missing perturbation or control, a declared context whose rows do
    not contain both, unmatched groups, and an input dimension the checkpoint
    was not trained on.
  - `subset` writes a query file holding only the declared context's control
    rows and the requested condition's rows, with their original row
    identifiers and digests.
  - `validate` checks the prediction and writes the condition-level shift vector.
- Interfaces: `inspect`, `subset`, `validate`, `main` (CLI: inspect | subset | validate).
- Depends on: anndata, h5py, numpy, pandas, torch
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence


def _write(path: Path, payload: dict[str, object]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, sort_keys=True), encoding="utf-8")
    return 0 if payload.get("valid") else 2


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def _labels(adata, column: str) -> set[str]:
    if column not in adata.obs:
        return set()
    return set(adata.obs[column].astype(str))


def _groups(adata, perturbation: str, pert_column: str, celltype_column: str, batch_column: str, mask=None) -> set[tuple[str, str]]:
    selected = adata.obs[pert_column].astype(str) == perturbation
    if mask is not None:
        selected = selected & mask
    subset = adata.obs[selected]
    return set(zip(subset[celltype_column].astype(str), subset[batch_column].astype(str)))


def _column(group, name: str):
    """Read one obs column from an h5ad group as an array of strings."""

    import h5py
    import numpy as np

    item = group[name]
    if isinstance(item, h5py.Group) and "categories" in item:
        categories = item["categories"]
        values = categories.asstr()[:] if categories.dtype.kind in "OS" else categories[:].astype(str)
        return np.asarray(values)[item["codes"][:]]
    if item.dtype.kind in "OS":
        return np.asarray(item.asstr()[:])
    return item[:].astype(str)


def _numpy_scalar_globals() -> tuple[type, ...]:
    """The NumPy globals State's committed map stores, without a private import path.

    NumPy 2 renamed ``numpy.core`` to ``numpy._core`` and emits a
    DeprecationWarning on the old spelling, so the new private name is used when it
    exists and the older public name is the fallback. Every entry is optional:
    a missing attribute narrows the allow-list instead of breaking the load.
    """

    import numpy as np

    allowed: list[type] = []
    core = getattr(np, "_core", None) or getattr(np, "core", None)
    multiarray = getattr(core, "multiarray", None) if core is not None else None
    scalar = getattr(multiarray, "scalar", None) if multiarray is not None else None
    if scalar is not None:
        allowed.append(scalar)
    dtype = getattr(np, "dtype", None)
    if dtype is not None:
        allowed.append(dtype)
    dtypes = getattr(np, "dtypes", None)
    string_dtype = getattr(dtypes, "StrDType", None) if dtypes is not None else None
    if string_dtype is not None:
        allowed.append(string_dtype)
    return tuple(allowed)


def inspect(arguments: argparse.Namespace) -> int:
    import anndata as ad
    import numpy as np
    import torch

    errors: list[str] = []
    input_path = Path(arguments.input)
    map_path = Path(arguments.perturbation_map)
    if not input_path.is_file():
        errors.append("registered input AnnData file is unavailable")
    if not map_path.is_file():
        errors.append("checkpoint perturbation map is unavailable")
    if errors:
        return _write(Path(arguments.summary), {"valid": False, "errors": errors})

    try:
        # State's committed map stores NumPy scalar labels. Keep weights-only
        # loading and allow only that concrete scalar representation.
        with torch.serialization.safe_globals(list(_numpy_scalar_globals())):
            perturbation_map = torch.load(map_path, map_location="cpu", weights_only=True)
    except Exception as error:
        return _write(Path(arguments.summary), {"valid": False, "errors": [f"cannot load perturbation map: {error}"]})
    if not isinstance(perturbation_map, dict) or arguments.perturbation not in perturbation_map:
        errors.append("perturbation is absent from the checkpoint map; fallback-to-control is forbidden")

    try:
        adata = ad.read_h5ad(input_path, backed="r")
        features = 0
        if arguments.embed_key not in adata.obsm:
            errors.append(f"missing embedding key: {arguments.embed_key}")
        else:
            features = int(adata.obsm[arguments.embed_key].shape[1])
            if arguments.expected_features is not None and features != arguments.expected_features:
                errors.append(
                    f"input feature count {features} does not match the checkpoint input dimension {arguments.expected_features}"
                )
        required = [arguments.perturbation_column, arguments.celltype_column, arguments.batch_column]
        if arguments.context_column:
            required.append(arguments.context_column)
        for column in dict.fromkeys(required):
            if column not in adata.obs:
                errors.append(f"missing required observation column: {column}")
        labels = _labels(adata, arguments.perturbation_column)
        if arguments.control not in labels:
            errors.append("declared control label is absent from the registered dataset")
        if arguments.perturbation not in labels:
            errors.append("declared perturbation label is absent from the registered dataset")
        in_context = None
        if not errors and arguments.context_column:
            in_context = adata.obs[arguments.context_column].astype(str) == arguments.context
            names = adata.obs[arguments.perturbation_column].astype(str)
            if not bool(((names == arguments.perturbation) & in_context).any()):
                errors.append("no rows for the declared context contain the perturbation")
            if not bool(((names == arguments.control) & in_context).any()):
                errors.append("no rows for the declared context contain the control")
        matching_groups: set[tuple[str, str]] = set()
        if not errors:
            matching_groups = _groups(
                adata, arguments.control, arguments.perturbation_column,
                arguments.celltype_column, arguments.batch_column, in_context,
            ) & _groups(
                adata, arguments.perturbation, arguments.perturbation_column,
                arguments.celltype_column, arguments.batch_column, in_context,
            )
            if not matching_groups:
                errors.append("no matched cell-type and batch group contains both control and perturbation")
        payload = {
            "valid": not errors,
            "errors": errors,
            "input_observations": int(adata.n_obs),
            "input_features": features,
            "matching_groups": len(matching_groups),
            "context": arguments.context,
        }
    except Exception as error:
        payload = {"valid": False, "errors": [f"cannot inspect AnnData: {error}"]}
    return _write(Path(arguments.summary), payload)


def subset(arguments: argparse.Namespace) -> int:
    """Write the query file: declared-context controls plus the requested condition."""

    import anndata as ad
    import h5py
    import numpy as np
    import pandas as pd

    errors: list[str] = []
    try:
        with h5py.File(arguments.input, "r") as handle:
            obs = handle["obs"]
            index_key = obs.attrs.get("_index", "_index")
            if isinstance(index_key, bytes):
                index_key = index_key.decode("utf-8")
            row_names = _column(obs, str(index_key))
            labels = _column(obs, arguments.perturbation_column)
            contexts = _column(obs, arguments.context_column)
            batches = _column(obs, arguments.batch_column)
            celltypes = _column(obs, arguments.celltype_column)
            in_context = contexts == arguments.context
            control = in_context & (labels == arguments.control)
            treated = in_context & (labels == arguments.perturbation)
            if not control.any():
                errors.append("no rows for the declared context contain the control")
            if not treated.any():
                errors.append("no rows for the declared context contain the perturbation")
            if errors:
                return _write(Path(arguments.summary), {"valid": False, "errors": errors})
            rows = np.flatnonzero(control | treated)
            matrix = np.asarray(handle["obsm"][arguments.embed_key][rows], dtype=np.float32)
        columns = {
            arguments.perturbation_column: labels[rows],
            arguments.celltype_column: celltypes[rows],
            arguments.batch_column: batches[rows],
            arguments.context_column: contexts[rows],
        }
        frame = pd.DataFrame({name: values for name, values in columns.items()}, index=[str(name) for name in row_names[rows]])
        data = ad.AnnData(obs=frame)
        data.obsm[arguments.embed_key] = matrix
        output = Path(arguments.subset_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        data.write_h5ad(output)
        identifiers = "\n".join(str(name) for name in row_names[rows]).encode("utf-8")
        payload = {
            "valid": True,
            "errors": [],
            "source_rows": int(labels.size),
            "rows": int(rows.size),
            "control_rows": int(control.sum()),
            "perturbation_rows": int(treated.sum()),
            "plates": sorted({str(value) for value in batches[rows]}),
            "row_ids_sha256": hashlib.sha256(identifiers).hexdigest(),
            "subset_sha256": _file_sha256(output),
            "features": int(matrix.shape[1]),
        }
    except Exception as error:
        payload = {"valid": False, "errors": [f"cannot build the query subset: {error}"]}
    return _write(Path(arguments.summary), payload)


def validate(arguments: argparse.Namespace) -> int:
    import anndata as ad
    import numpy as np

    errors: list[str] = []
    try:
        source = ad.read_h5ad(arguments.input, backed="r")
        output = ad.read_h5ad(arguments.output, backed="r")
        if output.n_obs != source.n_obs:
            errors.append("prediction output changed the number of observations")
        if arguments.embed_key not in output.obsm:
            errors.append(f"prediction output lacks {arguments.embed_key}")
        prediction = None
        if not errors:
            prediction = np.asarray(output.obsm[arguments.embed_key])
            if prediction.ndim != 2 or prediction.shape[0] != output.n_obs:
                errors.append("prediction embedding has an invalid shape")
            elif not np.isfinite(prediction).all():
                errors.append("prediction embedding contains non-finite values")
        labels = _labels(output, arguments.perturbation_column)
        if arguments.control not in labels or arguments.perturbation not in labels:
            errors.append("prediction output does not preserve declared control and perturbation labels")
        if errors:
            return _write(Path(arguments.summary), {"valid": False, "errors": errors})

        control_mask = output.obs[arguments.perturbation_column].astype(str) == arguments.control
        perturbation_mask = output.obs[arguments.perturbation_column].astype(str) == arguments.perturbation
        control_mean = prediction[control_mask.to_numpy()].mean(axis=0)
        perturbation_mean = prediction[perturbation_mask.to_numpy()].mean(axis=0)
        delta = perturbation_mean - control_mean
        payload = {
            "valid": True,
            "errors": [],
            "output_observations": int(output.n_obs),
            "output_features": int(prediction.shape[1]),
            "control_cells": int(control_mask.sum()),
            "perturbation_cells": int(perturbation_mask.sum()),
            "mean_absolute_embedding_delta": float(np.abs(delta).mean()),
            "embedding_delta_l2": float(np.linalg.norm(delta)),
            "embedding_delta_std": float(np.std(delta)),
            "output_sha256": _file_sha256(Path(arguments.output)),
        }
        if arguments.vector_output:
            vector = np.ascontiguousarray(delta.astype("<f8"))
            np.save(arguments.vector_output, vector)
            payload["vector_sha256"] = hashlib.sha256(vector.tobytes()).hexdigest()
        return _write(Path(arguments.summary), payload)
    except Exception as error:
        return _write(Path(arguments.summary), {"valid": False, "errors": [f"cannot validate prediction output: {error}"]})


def main(argv: Sequence[str] | None = None) -> int:
    """Parse one runner invocation.

    ``argv`` is optional so a caller that already runs in the configured
    interpreter can invoke the same entry point in process, with the same
    argument parsing and the same checks as the console script.
    """

    parser = argparse.ArgumentParser(description="Inspect, subset and validate State inputs and outputs for MAESTRO.")
    parser.add_argument("mode", choices=("inspect", "subset", "validate"))
    parser.add_argument("--input", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--perturbation", required=True)
    parser.add_argument("--control", required=True)
    parser.add_argument("--perturbation-column", required=True)
    parser.add_argument("--embed-key", required=True)
    parser.add_argument("--celltype-column", required=True)
    parser.add_argument("--batch-column", required=True)
    parser.add_argument("--context-column")
    parser.add_argument("--context")
    parser.add_argument("--expected-features", type=int)
    parser.add_argument("--perturbation-map")
    parser.add_argument("--output")
    parser.add_argument("--subset-output")
    parser.add_argument("--vector-output")
    arguments = parser.parse_args(argv)
    if arguments.context_column and not arguments.context:
        parser.error("--context-column requires --context")
    if arguments.mode == "inspect":
        if not arguments.perturbation_map:
            parser.error("inspect requires --perturbation-map")
        return inspect(arguments)
    if arguments.mode == "subset":
        if not arguments.subset_output or not arguments.context_column:
            parser.error("subset requires --subset-output, --context-column and --context")
        return subset(arguments)
    if not arguments.output:
        parser.error("validate requires --output")
    return validate(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
