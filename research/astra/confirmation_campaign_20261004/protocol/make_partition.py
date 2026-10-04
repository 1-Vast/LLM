"""Design-only line partition for the confirmation-campaign study (no outcome column is read).

File summary
- Path: research/astra/confirmation_campaign_20261004/protocol/make_partition.py
- Purpose: split each tissue's target lines into a history/development set (HD) and an evaluation
  set (E) before any outcome of this study is read. E lines are never used as history, never used
  for selection, and are scored only after the development selection is frozen.
- Core points: line lists come from the earlier study's design receipt (`candidates.json`); the 14
  repeat lines come from the provenance receipt (Supplementary Table 2); the split is a seeded
  permutation per tissue, E = floor(n / 2).
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.protocol.make_partition`.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CANDIDATES = ROOT / "research/astra/feedback_validation_20261003/results/jaaks_primary/candidates.json"
PROVENANCE = ROOT / "research/astra/reproducible_allocation_20261003/repeats/receipts/provenance.json"
TISSUE_CODE = {"Breast": 1, "Colon": 2, "Pancreas": 3}
SEED = 20261004


def main() -> int:
    out = HERE / "partition.json"
    if out.exists():
        raise SystemExit("partition.json exists; never overwritten")
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    repeat_names = set(provenance["checks"]["supp_table2_replicate_lines"])
    sidm_of = {}
    with open(ROOT / "research/astra/reproducible_allocation_20261003/repeats/receipts/plate_hierarchy.csv",
              encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            sidm_of.setdefault(row.get("line") or row.get("CELL_LINE_NAME"), row.get("SIDM"))
    repeat_sidm = {sidm_of[name] for name in repeat_names if sidm_of.get(name)}
    split = {}
    for tissue, entry in candidates.items():
        lines = sorted(entry["line_sidm"])
        order = np.random.default_rng([SEED, TISSUE_CODE[tissue]]).permutation(len(lines))
        n_eval = len(lines) // 2
        evaluation = sorted(lines[i] for i in order[:n_eval])
        history_dev = sorted(lines[i] for i in order[n_eval:])
        split[tissue] = {"E": evaluation, "HD": history_dev,
                         "repeat_lines_E": sorted(set(evaluation) & repeat_sidm),
                         "repeat_lines_HD": sorted(set(history_dev) & repeat_sidm)}
    record = {"rule": "per tissue: sorted line_sidm permuted with numpy default_rng([20261004, tissue code]); "
                      "first floor(n/2) -> E (evaluation targets), rest -> HD (history library and development targets)",
              "source": str(CANDIDATES.relative_to(ROOT)).replace("\\", "/"), "design_only": True,
              "repeat_lines_found": len(repeat_sidm), "split": split,
              "counts": {t: {"E": len(v["E"]), "HD": len(v["HD"]), "repeat_E": len(v["repeat_lines_E"]),
                             "repeat_HD": len(v["repeat_lines_HD"])} for t, v in split.items()}}
    out.write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(json.dumps(record["counts"], indent=1), record["repeat_lines_found"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
