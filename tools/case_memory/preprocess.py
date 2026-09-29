"""Build the external evaluation data pack (frozen protocol, reference-side fitting only).

File summary
- Path: tools/case_memory/preprocess.py
- Purpose: thin CLI over `research.case_memory_integration.external_data.build_pack`.
- Run: `python -m tools.case_memory.preprocess`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from research.case_memory_integration.external_data import build_pack

    manifest = build_pack()
    print(json.dumps({"pack_version": manifest["pack_version"], "counts": manifest["counts"],
                      "counts_detail": manifest["counts_detail"]}, indent=1))


if __name__ == "__main__":
    main()
