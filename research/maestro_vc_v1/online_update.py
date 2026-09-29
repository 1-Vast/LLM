"""Closed-loop update test: does appending revealed real outcomes to the memory improve later forecasts?

File summary
- Path: research/maestro_vc_v1/online_update.py
- Purpose: step 9 of the design says the memory and its reliability estimates are updated after real data
  arrive. This test measures whether that update helps: held-out compounds of a fold arrive in a
  seeded order, each is forecast from the memory as it then stands, and its real readings are then
  appended as a new case before the next one arrives.
- Core points:
  - Memory at time j is the fold's training snapshot plus the compounds revealed before j, never one of
    the same independent unit as compound j (same-series analogues would make the update look better
    than it is). Nothing about compound j is in the memory when it is forecast.
  - The forecast is the class layer of the case-memory world (per-class reading distribution against the
    decoy, shrunk to the pooled distribution with strength 4), so the only thing that changes with the
    update is the count of class references; the structure kernel and the modifier terms are not
    involved.
  - A revealed compound's readings against each decoy are the registered validator's readings computed
    against the training templates only, exactly what the replay's outcome tables hold, so the appended
    case is what a real user's compound would be after its experiment.
  - Score: NLL of each held-out compound's realised readings, for the update against the static
    memory, paired over identical items, unit-clustered, by arrival-position bucket. A gain that
    grows with position is evidence that the loop learns; no gain is evidence that class-level counts
    are already saturated.
  - Defined and frozen before it ran (its own addendum). Uses only replay outputs.
- Run: python -m research.maestro_vc_v1.online_update [--replay DIR] [--out FILE]
- Interfaces: `run`, `BUCKETS`
- Depends on: research/scientific_case_memory (index, evaluate_case_retrieval), replay outputs
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from research.scientific_case_memory import case_index as CI
from research.scientific_case_memory import case_store as CS
from research.scientific_case_memory import evaluate_case_retrieval as F

from . import stress as ST

ROOT = Path(__file__).resolve().parents[2]
REPLAY = ROOT / "outputs/maestro_vc_v1/replay"
OUT = ROOT / "outputs/maestro_vc_v1/analysis/online_update.json"
BUCKETS = ((0, 10), (10, 25), (25, 50), (50, 10 ** 6))
SEED = 20260929
OUTCOME_LABEL = {"eliminate_b": "profile_matches_h1", "eliminate_a": "profile_matches_h2", "ambiguous": "profile_unresolved",
                 "undetected": "no_detectable_response", "quality_failed": "quality_failed"}


def _rows(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def run(replay: Path = REPLAY) -> dict:
    manifest = json.loads((replay / "manifest.json").read_text(encoding="utf-8"))
    records = []
    for task, info in sorted(manifest["tasks"].items()):
        dataset, tier, fold = task.split("_")[0], task.split("_")[1], int(task.split("_")[2])
        keys = [tuple(k) for k in manifest["settings"][f"{dataset}_{tier}"]["keys"]]
        store = CS.CaseStore(replay / "snapshots" / f"cases_{dataset}_{tier}_{fold}.jsonl.gz")
        refs = [c for c in store.latest() if c.case_kind.value != "adaptation"]
        index = CI.CaseIndex.from_cases(refs, info["pool"], keys)
        pool = tuple(info["pool"])
        pooled = {k: _pooled_at(index, k) for k in keys}
        qc = {k: 1.0 - len(index.tables[k].names) / max(len(index.cases), 1) for k in keys}
        tables = _rows(replay / "tables" / f"{task}.jsonl.gz")
        by_compound: dict = {}
        for t in tables:
            by_compound.setdefault(t["compound"], []).append(t)
        rng = np.random.default_rng([SEED, fold, int(ST.hashlib.sha256(tier.encode()).hexdigest()[:6], 16)]) \
            if hasattr(ST, "hashlib") else np.random.default_rng([SEED, fold])
        order = sorted(by_compound)
        rng.shuffle(order)
        # counts of the revealed compounds: counts[key][(own, decoy)] -> 4-vector, plus per-unit contributions
        revealed: list[tuple[str, str, dict]] = []  # (compound, unit, {(key, own, decoy): code})
        for position, c in enumerate(order):
            eps = by_compound[c]
            unit = f"{dataset}:{eps[0]['unit']}"
            usable = [r for r in revealed if r[1] != unit]
            extra: dict = {}
            for (_c, _u, codes) in usable:
                for (key, own, decoy), code in codes.items():
                    v = extra.setdefault((key, own, decoy), np.zeros(4))
                    v[code] += 1
            new_codes: dict = {}
            for ep in eps:
                truth = ep["truth"]
                decoy = ep["h2"] if truth == ep["h1"] else ep["h1"]
                for action, o in ep["outcomes"].items():
                    key = tuple(o["key"])
                    label = OUTCOME_LABEL[o["outcome"]]
                    code = ST._code_of(label, truth == ep["h1"])
                    if o["lifecycle"] not in ("measured_valid", "measured_qc_failed"):
                        continue
                    static = ST.class_distribution(index, key, truth, decoy, pooled[key])
                    counts = extra.get((key, truth, decoy), np.zeros(4))
                    t = index.tables[key]
                    oi = index.cidx[decoy]
                    rows_ = np.flatnonzero((t.klass == truth) & (t.code[:, oi] >= 0))
                    base = np.bincount(t.code[rows_, oi], minlength=4).astype(float)
                    online = (base + counts + ST.S_STRENGTH * pooled[key]) / (len(rows_) + counts.sum() + ST.S_STRENGTH)
                    records.append({"task": task, "tier": f"{dataset}:{tier}", "unit": unit, "position": position,
                                    "static": ST._nll(static, qc[key], code), "online": ST._nll(online, qc[key], code)})
                    if code < 4:
                        new_codes[(key, truth, decoy)] = code
            revealed.append((c, unit, new_codes))
    return _aggregate(records)


def _pooled_at(index: CI.CaseIndex, key) -> np.ndarray:
    c = index.tables[key].code
    counts = np.bincount(c[c >= 0], minlength=4).astype(float) + 0.5
    return counts / counts.sum()


def _aggregate(records: list[dict]) -> dict:
    import pandas as pd

    df = pd.DataFrame(records)
    out = {"items": int(len(df)), "units": int(df.unit.nunique()), "buckets": [], "by_tier": []}
    df["delta"] = df.online - df.static
    codes = np.unique(df.unit, return_inverse=True)[1]
    out["overall"] = {"static": float(df.static.mean()), "online": float(df.online.mean()), "difference": float(df.delta.mean()),
                      "ci": F.bootstrap_mean(df.delta.to_numpy(), codes, int(codes.max()) + 1)}
    for lo, hi in BUCKETS:
        g = df[(df.position >= lo) & (df.position < hi)]
        if g.empty:
            continue
        c = np.unique(g.unit, return_inverse=True)[1]
        out["buckets"].append({"positions": [lo, min(hi, int(df.position.max()) + 1)], "items": int(len(g)),
                               "units": int(g.unit.nunique()), "static": float(g.static.mean()), "online": float(g.online.mean()),
                               "difference": float(g.delta.mean()),
                               "ci": F.bootstrap_mean(g.delta.to_numpy(), c, int(c.max()) + 1)})
    for tier, g in df.groupby("tier"):
        c = np.unique(g.unit, return_inverse=True)[1]
        out["by_tier"].append({"tier": tier, "items": int(len(g)), "static": float(g.static.mean()), "online": float(g.online.mean()),
                               "difference": float(g.delta.mean()), "ci": F.bootstrap_mean(g.delta.to_numpy(), c, int(c.max()) + 1)})
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", default=str(REPLAY))
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    result = run(Path(args.replay))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    print("wrote", out, "items", result["items"])


if __name__ == "__main__":
    main()
