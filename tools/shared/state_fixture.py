"""Build the smallest virtual-cell fixture the real entry point accepts.

File summary
- Path: tools/shared/state_fixture.py
- Purpose: construct a registered asset, a registered model and a bound query, so an
  admission test tests admission instead of re-deriving plumbing in every module.
- Core points:
  - The asset is synthetic and says so: its registration declares
    `source="synthetic asset built by tools.shared.state_fixture"`, and nothing here
    is a measurement. A fixture can make the entry point *accept* a query; it can
    never make a claim about biology.
  - `adapter` binds a matching coordinate identity by default, because the entry
    point now refuses a model that declares no input basis at all. A caller that
    wants to exercise *that* refusal passes `input_coordinate_names=()`.
  - The asset is written once per directory. Rewriting an asset a caller has already
    registered would change its bytes under the recorded digest, which is the defect
    one of the tests exists to catch.
- Interfaces: `CONTROL`, `DRUG_A`, `DRUG_B`, `SHIFT`, `DEFAULT_BASIS`, `asset_sha256`,
  `write_asset`, `write_model`, `registration`, `adapter`, `request`, `joined`,
  `requires_asset_runtime`
- Depends on: virtual_cell, numpy, pytest
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from virtual_cell import (
    Intervention,
    PredictionRequest,
    QueryAssessment,
    StateAdapterConfig,
    StateCapabilityAdapter,
    SystemContext,
)
from virtual_cell.state_adapter import DatasetRegistration

CONTROL = "[('DMSO_TF', 0.0, 'uM')]"
DRUG_A = "[('drugA', 0.5, 'uM')]"
DRUG_B = "[('drugB', 0.5, 'uM')]"
SHIFT = "x_hvg_perturbation_shift"
DEFAULT_BASIS = tuple(f"g{index}" for index in range(8))
DEFAULT_CONTEXT = "NCI-H596"

HAVE_ASSET_RUNTIME = all(
    importlib.util.find_spec(name) for name in ("anndata", "torch", "h5py")
)
requires_asset_runtime = pytest.mark.skipif(
    not HAVE_ASSET_RUNTIME,
    reason="anndata, torch and h5py are required to build the fixture asset",
)


def asset_sha256(path: Path) -> str:
    """Digest of an asset's bytes, which is what a registration records."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_asset(directory: Path, *, contexts=(DEFAULT_CONTEXT,), features: int = 8) -> Path:
    """Write the synthetic AnnData asset, once per directory."""

    import anndata as ad
    import pandas as pd

    path = directory / "tiny.h5ad"
    if path.is_file():
        return path
    rng = np.random.default_rng(0)
    labels = [CONTROL] * 12 + [DRUG_A] * 10 + [DRUG_B] * 10
    obs = pd.DataFrame(
        {
            "cell_name": [contexts[0]] * len(labels),
            "drugname_drugconc": labels,
            "plate": ["plate1", "plate2"] * (len(labels) // 2),
        },
        index=[f"cell{i}" for i in range(len(labels))],
    )
    data = ad.AnnData(obs=obs)
    data.obsm["X_hvg"] = rng.normal(size=(len(labels), features)).astype(np.float32)
    data.obsm["X_state"] = rng.normal(size=(len(labels), features + 3)).astype(np.float32)
    data.write_h5ad(path)
    return path


def write_model(directory: Path, labels=(CONTROL, DRUG_A, DRUG_B)) -> tuple[Path, Path]:
    """Write the checkpoint placeholder, its config, and the perturbation map."""

    model = directory / "model"
    (model / "checkpoints").mkdir(parents=True, exist_ok=True)
    checkpoint = model / "checkpoints" / "final.ckpt"
    if not checkpoint.is_file():
        checkpoint.write_bytes(b"checkpoint placeholder for admission tests; never loaded")
    config = model / "config.yaml"
    if not config.is_file():
        config.write_text("name: test\n", encoding="utf-8")
    if HAVE_ASSET_RUNTIME:
        import torch

        map_path = model / "pert_onehot_map.pt"
        if not map_path.is_file():
            torch.save(
                {label: torch.eye(len(labels))[index] for index, label in enumerate(labels)},
                map_path,
            )
    return checkpoint, config


def registration(identifier: str, path: Path, *, contexts=(DEFAULT_CONTEXT,),
                 features: int = 8, sha256: str | None = None) -> DatasetRegistration:
    """Register an asset with every field the entry point checks.

    `sha256` overrides the recorded digest, which is how a test asks the entry
    point to reject an asset whose bytes no longer match its registration.
    """

    return DatasetRegistration(
        identifier=identifier,
        path=path,
        sha256=sha256 or asset_sha256(path),
        size_bytes=path.stat().st_size,
        contexts=tuple(contexts),
        context_column="cell_name",
        perturbation_column="drugname_drugconc",
        control_label=CONTROL,
        batch_column="plate",
        embedding_key="X_hvg",
        feature_count=features,
        source="synthetic asset built by tools.shared.state_fixture",
    )


def adapter(directory: Path, **overrides) -> StateCapabilityAdapter:
    """An adapter over a registered synthetic asset, with a matching input basis."""

    import json

    datasets = overrides.pop("datasets", None)
    if datasets is None:
        asset = write_asset(directory)
        identity = directory / "default_identity.json"
        identity.write_text(
            json.dumps(
                {
                    "dataset_sha256": asset_sha256(asset),
                    "feature_count": 8,
                    "names": list(DEFAULT_BASIS),
                }
            ),
            encoding="utf-8",
        )
        datasets = {"tiny": replace(registration("tiny", asset), feature_names_path=identity)}
    checkpoint, config = write_model(directory)
    settings = StateAdapterConfig(
        checkpoint=checkpoint,
        config=config,
        model_version="state-test",
        python_executable=Path(sys.executable),
        datasets=datasets,
        input_dim=8,
        input_coordinate_names=DEFAULT_BASIS,
        output_directory=directory / "out",
    )
    return StateCapabilityAdapter(replace(settings, **overrides))


def request(identifier: str = "req", **overrides) -> PredictionRequest:
    """A query bound to the fixture's context, dataset, control and readout."""

    values = {
        "label": DRUG_A,
        "mode": "drug",
        "context": DEFAULT_CONTEXT,
        "dataset": "tiny",
        "control": "tiny",
        "readouts": (SHIFT,),
        "version": "state-test",
    }
    values.update(overrides)
    return PredictionRequest(
        identifier,
        "case",
        "contrast",
        1,
        Intervention(values["label"], values["mode"], ()),
        SystemContext(
            values["context"],
            "test context",
            dataset_id=values["dataset"],
            control_dataset_id=values["control"],
        ),
        tuple(values["readouts"]),
        values["version"],
    )


def joined(assessment: QueryAssessment) -> str:
    """Every limitation and missing input in one line, for an assertion message."""

    return " | ".join((*assessment.limitations, *assessment.missing_inputs))
