"""One place that decides which registered backends a caller may select.

File summary
- Path: src/virtual_cell/backends.py
- Purpose: build the requested world-model backend from the workspace registry so the
  agent CLI and the panel CLI name the same backends in the same way.
- Core points:
  - ``none`` is the only choice that returns no backend; every other choice either
    returns a backend or raises, so a request never silently degrades to "no model".
  - ``composite`` orders the rungs as they are assembled and leaves eligibility to the
    composite, which asks each rung about the actual request.
- Interfaces: `BACKEND_CHOICES`, `build_backend`
  - ``sciplex_response`` is the SciPlex3 response rung; it stands alone, needs declared
    structures and its library, and serves only readouts that beat the average response.
- Depends on: state_adapter.py, ladder.py, transcript_baselines.py, world_model.py, response_rung.py
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .state_adapter import DEFAULT_MODEL_VERSION, StateAdapterConfig, StateCapabilityAdapter
from .world_model import CompositeWorldModel

BACKEND_CHOICES = ("none", "state", "development_mean", "composite", "sciplex_response")
SCIPLEX_LIBRARY = Path("data/virtual_cell/sciplex3_signature_library")


def build_backend(
    choice: str,
    *,
    workspace: Path,
    dataset_id: str = "tahoe_c39",
    development_partition: Path | None = None,
    artifact_directory: Path | None = None,
    model_version: str = DEFAULT_MODEL_VERSION,
    structures: dict[str, str] | None = None,
):
    """Return the requested backend, or ``None`` for the declared ``none`` choice."""

    if choice not in BACKEND_CHOICES:
        raise ValueError(f"Unknown backend '{choice}'; choose one of {', '.join(BACKEND_CHOICES)}.")
    if choice == "none":
        return None
    if choice == "sciplex_response":
        if not structures:
            raise ValueError("The sciplex_response backend requires declared structures (identifier to SMILES).")
        from .response_rung import ResponseRungConfig, SciPlexResponseRung

        directory = Path(workspace) / SCIPLEX_LIBRARY
        if not (directory / "calibration.json").is_file():
            raise ValueError(f"The sciplex_response backend needs its library and calibration under {SCIPLEX_LIBRARY}.")
        return SciPlexResponseRung(ResponseRungConfig(directory, directory / "calibration.json",
                                                      {str(k): str(v) for k, v in structures.items()}))
    backends = []
    if choice in ("state", "composite"):
        config = StateAdapterConfig.from_workspace(workspace, model_version=model_version)
        if artifact_directory is not None:
            config = replace(config, output_directory=artifact_directory)
        backends.append(StateCapabilityAdapter(config))
    if choice in ("development_mean", "composite"):
        if development_partition is None:
            raise ValueError("The development_mean backend requires a declared development partition.")
        from .transcript_baselines import fit_development_mean_baseline, load_partition
        from .state_adapter import load_registry

        registration = load_registry(workspace).datasets.get(dataset_id)
        if registration is None:
            raise ValueError(f"Dataset '{dataset_id}' is not registered.")
        backends.append(
            fit_development_mean_baseline(
                registration,
                load_partition(development_partition),
                artifact_directory=artifact_directory,
            )
        )
    return backends[0] if len(backends) == 1 else CompositeWorldModel(backends)
