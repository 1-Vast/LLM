"""Run the frozen external replay.

File summary
- Path: tools/case_memory/replay.py
- Purpose: thin CLI over `research.case_memory_integration.external_replay.run_replay`.
- Run: `python -m tools.case_memory.replay`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from research.case_memory_integration.external_replay import run_replay

    results = run_replay()
    print(json.dumps({"population": results["population"],
                      "primary": results["primary_endpoint_full_minus_scalar_nll"],
                      "headroom": results["oracle_headroom_correct"]}, indent=1))


if __name__ == "__main__":
    main()
