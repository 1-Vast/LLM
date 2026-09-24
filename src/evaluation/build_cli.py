"""CLI that materialises the real-data mechanism-contrast case package.

File summary
- Path: src/evaluation/build_cli.py
- Purpose: Build frozen public cases, evaluator-only outcomes, and the case manifest from local releases.
- Core points:
  - It writes cases only from checksum-verified local releases.
  - The manifest is evaluator-owned; it records the archetype, split, and licensed decisions.
  - Rebuilding an existing package requires an explicit overwrite.
- Interfaces: `main`
- Depends on: evaluation.case_builder, evaluation.evidence_base
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .case_builder import build_cases, write_cases
from .evidence_base import build_evidence_base


def main() -> int:
    """Build the real-data case package and return a process exit code."""

    parser = argparse.ArgumentParser(
        description="Build leakage-bounded mechanism-contrast cases from the local DepMap and PRISM releases."
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--public-cases", type=Path, default=Path("data/evaluation/cases/real/public"))
    parser.add_argument("--private-results", type=Path, default=Path("data/evaluation/cases/real/private"))
    parser.add_argument("--manifest", type=Path, default=Path("data/evaluation/derived/real_case_manifest.json"))
    parser.add_argument("--per-archetype", type=int, default=12)
    parser.add_argument("--per-gene", type=int, default=3)
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing case package.")
    arguments = parser.parse_args()
    if arguments.per_archetype < 1 or arguments.per_gene < 1:
        parser.error("--per-archetype and --per-gene must be positive.")

    existing = sorted(arguments.public_cases.glob("*.json")) if arguments.public_cases.is_dir() else []
    if existing and not arguments.overwrite:
        parser.error("A case package already exists; pass --overwrite to rebuild it.")
    for path in existing:
        path.unlink()
    if arguments.private_results.is_dir() and arguments.overwrite:
        for path in arguments.private_results.glob("*.results.json"):
            path.unlink()

    base = build_evidence_base(arguments.workspace)
    payloads = build_cases(base, per_archetype=arguments.per_archetype, per_gene=arguments.per_gene)
    manifest = write_cases(
        payloads,
        public_directory=arguments.public_cases,
        private_directory=arguments.private_results,
        manifest_path=arguments.manifest,
        releases=base.release_manifest(),
    )
    archetypes = Counter(entry["archetype"] for entry in manifest["cases"])
    splits = Counter(entry["split"] for entry in manifest["cases"])
    print(
        json.dumps(
            {
                "cases": len(manifest["cases"]),
                "archetypes": dict(sorted(archetypes.items())),
                "splits": dict(sorted(splits.items())),
                "genes": len({entry["gene"] for entry in manifest["cases"]}),
                "models": len({entry["model_id"] for entry in manifest["cases"]}),
                "manifest": str(arguments.manifest),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
