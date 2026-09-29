"""CLI entry point for the virtual-cell layer.

File summary
- Path: src/virtual_cell/__main__.py
- Purpose: expose `python -m virtual_cell panel` for a declared condition panel
  behind a registered backend.
- Interfaces: `main` (panel command).
- Depends on: panel.py, world_model.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .world_model import BACKEND_CHOICES, build_backend


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
    from .biology import load_background_pool

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

    if arguments.command == "panel":
        return _panel(arguments)
    parser.error(f"Unknown command: {arguments.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
