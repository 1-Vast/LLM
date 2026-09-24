"""Print machine-readable G2 candidate eligibility without loading private outcomes.

File summary
- Path: src/evaluation/screening_cli.py
- Purpose: Validate and print G2 candidate screening records from the command line.
- Core points:
  - Reads only the candidate registry and prints each case's blocking reasons.
  - It never loads hidden replay outcomes or evaluator scoring answers.
- Interfaces: `main`
- Depends on: evaluation.screening
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .screening import assess_registry


def main() -> int:
    """Run the G2 candidate screening CLI and return a process exit code."""

    parser = argparse.ArgumentParser(description="Validate MAESTRO G2 source-screening records.")
    parser.add_argument("--registry", type=Path, default=Path("data/evaluation/candidate_registry.json"))
    arguments = parser.parse_args()
    assessments = assess_registry(arguments.registry)
    print(json.dumps([asdict(item) for item in assessments], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
