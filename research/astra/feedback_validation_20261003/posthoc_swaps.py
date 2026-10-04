"""POST HOC (after the verdict): what did feedback's changed decisions buy?

File summary
- Path: research/astra/feedback_validation_20261003/posthoc_swaps.py
- Purpose: on the registered Jaaks run, compare the experiments feedback bought that a static
  comparator did not (swap-ins) with those the comparator bought that feedback did not
  (swap-outs): screen-call rate, validation-call rate, validated rate and mean validation label.
  This is the selected-action utility of the decisions feedback actually changed.
- Core points: not part of the frozen protocol; reads `results/jaaks_primary/lines.jsonl` and
  rebuilds the panels through a logged vault entry (purpose "post hoc").
- Interfaces: `python -m research.astra.feedback_validation_20261003.posthoc_swaps`.
- Depends on: numpy; jaaks, run.
"""
from __future__ import annotations

import json

import numpy as np

from .jaaks import RELEASE, build_panels
from .run import FREEZE, HERE, ROOT, VAULT_LOG

COMPARATORS = ("history_mean", "history_rate", "ridge_static")


def main() -> int:
    from tools.datasets.combination_screens import open_vault

    ticket = open_vault(FREEZE, VAULT_LOG, purpose="POST HOC swap analysis of the registered run (after verdict)",
                        source=RELEASE, root=ROOT)
    panels, _, _ = build_panels(ticket, RELEASE)
    lines = [json.loads(x) for x in open(HERE / "results/jaaks_primary/lines.jsonl", encoding="utf-8")]
    out: dict = {"status": "POST HOC exploratory; not part of the frozen protocol", "ticket": ticket, "budgets": {}}
    for budget in ("primary", "budget10"):
        out["budgets"][budget] = {}
        for comparator in COMPARATORS:
            tallies = {k: {"n": 0, "screen": 0, "valid": 0, "validated": 0, "vy": 0.0}
                       for k in ("feedback_only", "comparator_only")}
            overlap = []
            for r in lines:
                p = panels[f"{r['stratum']}_{r['replicate']}"]
                rows = np.asarray(r["rows"])
                arms = r["budgets"][budget]["arms"]
                f = set(sum(arms["feedback"]["purchases"], []))
                s = set(sum(arms[comparator]["purchases"], []))
                overlap.append(len(f & s) / len(f))
                for key, chosen in (("feedback_only", f - s), ("comparator_only", s - f)):
                    idx = rows[sorted(chosen)]
                    t = tallies[key]
                    t["n"] += idx.size
                    t["screen"] += int(p.screen_hit[idx].sum())
                    t["valid"] += int(p.valid_hit[idx].sum())
                    t["validated"] += int((p.screen_hit[idx] & p.valid_hit[idx]).sum())
                    t["vy"] += float(p.valid_y[idx].sum())
            entry = {"mean_purchase_overlap": float(np.mean(overlap))}
            for key, t in tallies.items():
                n = t["n"]
                entry[key] = {"n": n, "screen_rate": t["screen"] / n if n else None,
                              "valid_rate": t["valid"] / n if n else None,
                              "validated_rate": t["validated"] / n if n else None,
                              "mean_valid_label": t["vy"] / n if n else None}
            out["budgets"][budget][comparator] = entry
    path = HERE / "results/posthoc_swaps.json"
    path.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps(out["budgets"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
