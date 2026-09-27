"""Read registered (protocol v1) and protocol-v2 episode records into one frame, streaming.

File summary
- Path: research/protocol_v2/records.py
- Purpose: one loader for the analyses in this package. It reads `.jsonl.gz` record files one
  line at a time, keeps only the requested arms, and derives the endpoint columns the analyses
  share, so the 298,272 registered development records never have to sit in memory as dicts.
- Core points:
  - Endpoints come from the recorded `final` field: correct, wrong (wrong or exhausted),
    decided, deferred. Protocol-v2 records carry the same field inside their `score`.
  - `episode` identifies an episode within a study: tier, fold, compound and contrast.
  - Records are read, never written. Protocol v1 outputs are archived read-only.
- Interfaces: `load`, `ENDPOINTS`
- Depends on: pandas
"""
from __future__ import annotations

import glob
import gzip
import json
from pathlib import Path

import pandas as pd

ENDPOINTS = ("correct", "wrong", "decided", "deferred", "measurements", "days", "wells", "utility")


def _files(path) -> list[Path]:
    path = Path(path)
    return [path] if path.is_file() else sorted(Path(p) for p in glob.glob(str(path / "*.jsonl.gz")))


def load(path, arms=None, *, keep_steps=False, dataset=None) -> pd.DataFrame:
    """Records of `arms` (all when None) from a file or a directory of `.jsonl.gz` files."""
    wanted = None if arms is None else set(arms)
    rows = []
    for f in _files(path):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                arm = r.get("arm") or r.get("policy")
                if wanted is not None and arm not in wanted:
                    continue
                scored = r.get("score") or {}
                final = scored.get("final", r.get("final"))
                steps = r.get("steps") or []
                row = {"arm": arm, "dataset": r.get("dataset", dataset), "tier": str(r.get("tier")),
                       "fold": r.get("fold"), "compound": r["compound"], "h1": r["h1"], "h2": r["h2"],
                       "truth": scored.get("truth", r.get("truth")), "final": final, "stop": r.get("stop"),
                       "measurements": r.get("measurements", len(steps)), "days": r.get("days"),
                       "wells": r.get("wells", 2 * len(steps) + 4 * len({(s["key"][0], s["key"][1]) for s in steps})),
                       "unit": str(r.get("unit", r["compound"])), "used_vc": bool(r.get("used_vc")),
                       "sequence": "|".join(s["action"] for s in steps),
                       "first_action": steps[0]["action"] if steps else None,
                       "second_action": steps[1]["action"] if len(steps) > 1 else None,
                       "first_outcome": steps[0]["outcome"] if steps else None,
                       "scaffold": r.get("scaffold"), "max_train_tanimoto": r.get("max_train_tanimoto")}
                if keep_steps:
                    row["steps"] = steps
                rows.append(row)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["correct"] = (frame.final == "correct").astype(float)
    frame["wrong"] = frame.final.isin(("wrong", "exhausted")).astype(float)
    frame["decided"] = frame.final.isin(("correct", "wrong", "exhausted")).astype(float)
    frame["deferred"] = (frame.final == "deferred").astype(float)
    frame["utility"] = frame.correct - 2.0 * frame.wrong
    frame["episode"] = (frame.tier.astype(str) + "|" + frame.fold.astype(str) + "|" + frame.compound + "|"
                        + frame.h1 + "|" + frame.h2)
    return frame
