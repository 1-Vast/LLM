"""CLI entry point for the virtual-cell layer.

File summary
- Path: src/virtual_cell/__main__.py
- Purpose: expose `python -m virtual_cell calibrate` for held-out ladder evaluation and
  `python -m virtual_cell panel` for a declared condition panel behind a registered backend.
- Core points: thin dispatcher; the logic lives in `evaluation.py`.
- Interfaces: `main` (subcommands: calibrate, panel).
- Depends on: src/virtual_cell/evaluation.py, panel.py, backends.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backends import BACKEND_CHOICES, build_backend


def _panel(arguments: argparse.Namespace) -> int:
    backend = build_backend(
        arguments.backend,
        workspace=arguments.workspace,
        dataset_id=arguments.dataset_id,
        development_partition=arguments.development_partition,
        artifact_directory=arguments.artifact_directory,
    )
    if backend is None:
        raise SystemExit("A panel needs a backend; 'none' answers no queries.")
    from .panel import execute_spec
    from .pathway_readout import load_background_pool

    pool = load_background_pool(arguments.background_pool) if arguments.background_pool else None
    payload = execute_spec(
        backend, arguments.spec, draws=arguments.draws, seed=arguments.seed, background_pool=pool
    )
    destination = Path(arguments.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=1, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")
    print(destination)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="virtual_cell", description="MAESTRO virtual-cell world model.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    calibrate = subparsers.add_parser("calibrate", help="score the world-model ladder on held-out data")
    calibrate.add_argument("--adata", required=True)
    calibrate.add_argument("--split", choices=("within_domain", "leave_dose_out", "leave_cell_line_out", "leave_drug_out"), default="within_domain")
    calibrate.add_argument("--out", required=True)
    panel = subparsers.add_parser("panel", help="run a declared condition panel behind a registered backend")
    panel.add_argument("--spec", type=Path, required=True, help="JSON panel specification.")
    panel.add_argument("--out", type=Path, required=True, help="Where the JSON panel report is written.")
    panel.add_argument("--workspace", type=Path, default=Path("."), help="Workspace holding data/virtual_cell/registry.json.")
    panel.add_argument("--backend", choices=BACKEND_CHOICES, default="state")
    panel.add_argument("--dataset-id", default="tahoe_c39", help="Registered dataset the computed baseline is fitted on.")
    panel.add_argument("--development-partition", type=Path, help="Declared partition required by the development_mean backend.")
    panel.add_argument("--artifact-directory", type=Path, help="Directory for the backend's prediction artifacts.")
    panel.add_argument("--draws", type=int, default=1000, help="Background draws per gene-set score.")
    panel.add_argument("--seed", type=int, default=0, help="Seed for the gene-set background draws.")
    panel.add_argument(
        "--background-pool",
        type=Path,
        default=None,
        help=(
            "Declared background-pool artefact the gene-set z-scores are drawn against; "
            "without it an expressible endpoint is refused by name."
        ),
    )
    arguments = parser.parse_args()

    if arguments.command == "calibrate":
        from .evaluation import evaluate_ladder

        evaluation = evaluate_ladder(Path(arguments.adata), split=arguments.split)
        destination = Path(arguments.out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(evaluation.to_json(), encoding="utf-8")
        print(destination)
        return 0
    if arguments.command == "panel":
        return _panel(arguments)
    parser.error(f"Unknown command: {arguments.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
