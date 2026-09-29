"""Unseen-condition stress test: forecast a condition the memory has never read, by priced adaptation.

File summary
- Path: research/maestro_vc_v1/stress.py
- Purpose: the standard replay gives the adaptation module nothing to do, because every reference was
  read at every condition and a same-condition transfer costs zero. This test removes that: for each
  condition k*, every reference reading at k* is withheld, and the reading of held-out compounds at k* is
  forecast from the class's readings at other conditions.
- Core points:
  - Four forecasts of the held-out compound's reading at k* under its true hypothesis, all built from
    the fold's case snapshot with k* removed:
    - `pooled`: the pooled reading distribution over the other conditions (no class information);
    - `naive_borrow`: the class's reading distribution at the nearest other condition, unpriced;
    - `adapted`: `(1 - cost) x class distribution at the cheapest source + cost x pooled`, the cost
      priced from an `AdaptationTable` estimated only from pairs of other conditions (so no pair
      involves k*), with the declared prior cost where a signature has no support;
    - `full_memory`: the ordinary class forecast with k* present, the upper bound the adaptation is
      trying to approach.
  - The score is the negative log-likelihood of the realised reading (five labels, QC failure
    included), unit-clustered, paired over identical items.
  - Cost validation. For every (fold, k*, source k') the mean NLL of borrowing from k' alone is set
    against the priced cost of k' -> k*; a positive rank correlation says a dearer transfer was in fact
    a worse forecast. The table's success rate per signature is also compared with the success the
    held-out compounds realised (their reading's probability under the source class distribution).
  - Defined and frozen before it ran (its own addendum); it uses only replay outputs and never reads a
    held-out label except to score.
- Run: python -m research.maestro_vc_v1.stress [--replay DIR] [--out FILE]
- Interfaces: `run`, `adaptation_table_from_index`, `class_distribution`
- Depends on: research/scientific_case_memory (index, adaptation), replay outputs
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from research.scientific_case_memory import adaptation_model as AM
from research.scientific_case_memory import case_index as CI
from research.scientific_case_memory import case_store as CS
from research.scientific_case_memory import evaluate_case_retrieval as F

ROOT = Path(__file__).resolve().parents[2]
REPLAY = ROOT / "outputs/maestro_vc_v1/replay"
OUT = ROOT / "outputs/maestro_vc_v1/analysis/stress.json"
S_STRENGTH = 4.0
"""Shrinkage of a class distribution to the pooled one, fixed at the reference world's registered default."""
LABELS = F.LABELS


def _ctx(dataset: str, key) -> AM.Context:
    return AM.Context(dataset, "transcriptome", key[0], float(key[1]), float(key[2]))


def adaptation_table_from_index(index: CI.CaseIndex, keys, dataset: str) -> AM.AdaptationTable:
    """Same-class, other-unit reading agreement over every ordered pair of `keys`, by difference signature."""
    pool = index.pool
    names = sorted(index.cases)
    klass = np.array([index.klass_of[n] for n in names], dtype=object)
    unit = np.array([index.unit_of[n] for n in names], dtype=object)
    codes = {}
    for key in keys:
        t = index.tables[key]
        m = np.full((len(names), len(pool)), -1, dtype=int)
        for i, n in enumerate(names):
            r = t.row.get(n)
            if r is not None:
                m[i] = t.code[r]
        codes[key] = m
    pooled = np.zeros(4)
    for m in codes.values():
        pooled += np.bincount(m[m >= 0], minlength=4)
    p = pooled / max(pooled.sum(), 1.0)
    table = AM.AdaptationTable(chance=float((p ** 2).sum()))
    same_unit = unit[:, None] == unit[None, :]
    for k1 in keys:
        for k2 in keys:
            sig = AM.signature(AM.differences(_ctx(dataset, k1), _ctx(dataset, k2)))
            hits = trials = 0
            for h in pool:
                members = np.flatnonzero(klass == h)
                if len(members) < 2:
                    continue
                for oi, o in enumerate(pool):
                    if o == h:
                        continue
                    s, t = codes[k1][members, oi], codes[k2][members, oi]
                    ok = (s >= 0)[:, None] & (t >= 0)[None, :] & ~same_unit[np.ix_(members, members)]
                    hits += int((ok & (s[:, None] == t[None, :])).sum())
                    trials += int(ok.sum())
            table.add_bulk(sig, hits, trials)
    return table


def class_distribution(index: CI.CaseIndex, key, own: str, other: str, pooled: np.ndarray) -> np.ndarray:
    """Four-code reading distribution of class `own` at `key` against decoy `other`, shrunk to `pooled`."""
    t = index.tables[key]
    oi = index.cidx[other]
    rows = np.flatnonzero((t.klass == own) & (t.code[:, oi] >= 0))
    counts = np.bincount(t.code[rows, oi], minlength=4).astype(float)
    return (counts + S_STRENGTH * pooled) / (len(rows) + S_STRENGTH)


def _pooled(index: CI.CaseIndex, keys) -> np.ndarray:
    counts = np.zeros(4)
    for k in keys:
        c = index.tables[k].code
        counts += np.bincount(c[c >= 0], minlength=4)
    counts += 0.5
    return counts / counts.sum()


def _code_of(label: str, truth_is_h1: bool) -> int:
    """Reading code of the realised label under the truth branch (5 for a QC failure)."""
    if label == "quality_failed":
        return 4
    if label == "profile_unresolved":
        return 2
    if label == "no_detectable_response":
        return 3
    matches_h1 = label == "profile_matches_h1"
    return 0 if matches_h1 == truth_is_h1 else 1


def _nll(p4: np.ndarray, qc: float, code: int) -> float:
    p = qc if code == 4 else (1.0 - qc) * p4[code]
    return -float(np.log(max(p, 1e-9)))


def _load_jsonl(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def run(replay: Path = REPLAY) -> dict:
    manifest = json.loads((replay / "manifest.json").read_text(encoding="utf-8"))
    rows, cost_rows, table_rows = [], [], []
    for task, info in sorted(manifest["tasks"].items()):
        dataset, tier, fold = task.split("_")[0], task.split("_")[1], int(task.split("_")[2])
        keys = [tuple(k) for k in manifest["settings"][f"{dataset}_{tier}"]["keys"]]
        store = CS.CaseStore(replay / "snapshots" / f"cases_{dataset}_{tier}_{fold}.jsonl.gz")
        refs = [c for c in store.latest() if c.case_kind.value != "adaptation"]
        index = CI.CaseIndex.from_cases(refs, info["pool"], keys)
        items = _load_jsonl(replay / "forecasts" / f"{task}.jsonl.gz")
        by_key: dict = {}
        for it in items:
            by_key.setdefault(it["key"], []).append(it)
        for star in keys:
            others = [k for k in keys if k != star]
            table = adaptation_table_from_index(index, others, dataset)
            pooled = _pooled(index, others)
            full_pooled = _pooled(index, keys)
            qc_other = float(np.mean([1.0 - len(index.tables[k].names) / max(len(index.cases), 1) for k in others]))
            costs = {k: table.cost(AM.differences(_ctx(dataset, k), _ctx(dataset, star))) for k in others}
            best = min(others, key=lambda k: (costs[k].cost, abs(k[1] - star[1]), abs(np.log10(k[2] / star[2])) if star[2] else 0))
            nearest = min(others, key=lambda k: (AM.differing_attributes(AM.differences(_ctx(dataset, k), _ctx(dataset, star))),
                                                 costs[k].cost))
            aid = f"{star[0]}|{int(star[1]):03d}h|{int(star[2]):05d}nM"
            per_source_nll = {k: [] for k in others}
            for it in by_key.get(aid, []):
                truth_is_h1 = it["truth"] == it["h1"]
                own, other = it["truth"], (it["h2"] if truth_is_h1 else it["h1"])
                code = _code_of(it["y"], truth_is_h1)
                dist = {k: class_distribution(index, k, own, other, pooled) for k in others}
                adapted = (1.0 - costs[best].cost) * dist[best] + costs[best].cost * pooled
                full = class_distribution(index, star, own, other, full_pooled) if index.tables[star].names else pooled
                qc_full = 1.0 - len(index.tables[star].names) / max(len(index.cases), 1)
                unit = f"{dataset}:{it['unit']}"
                base = {"tier": f"{dataset}:{tier}", "unit": unit, "key": aid, "task": task}
                rows.append({**base, "pooled": _nll(pooled, qc_other, code), "naive_borrow": _nll(dist[nearest], qc_other, code),
                             "adapted": _nll(adapted, qc_other, code), "full_memory": _nll(full, qc_full, code)})
                for k in others:
                    per_source_nll[k].append(_nll(dist[k], qc_other, code))
                if code < 4:
                    sig = AM.signature(AM.differences(_ctx(dataset, best), _ctx(dataset, star)))
                    table_rows.append({"signature": AM._sig_text(sig), "realised": float(dist[best][code]), "unit": unit,
                                       "table_success": table._rate(sig)[0], "trials": table.stats(sig)[1]})
            for k in others:
                if per_source_nll[k]:
                    cost_rows.append({"task": task, "star": aid, "source": f"{k[0]}|{int(k[1]):03d}h|{int(k[2]):05d}nM",
                                      "cost": costs[k].cost, "supported": costs[k].supported, "nll": float(np.mean(per_source_nll[k])),
                                      "signature": AM._sig_text(AM.signature(AM.differences(_ctx(dataset, k), _ctx(dataset, star))))})
    return _aggregate(rows, cost_rows, table_rows)


def _boot(values: np.ndarray, units: np.ndarray) -> tuple[float, list[float]]:
    codes = np.unique(units, return_inverse=True)[1]
    return float(values.mean()), F.bootstrap_mean(values, codes, int(codes.max()) + 1)


def _aggregate(rows, cost_rows, table_rows) -> dict:
    import pandas as pd

    df = pd.DataFrame(rows)
    out = {"items": int(len(df)), "units": int(df.unit.nunique()), "by_tier": [], "paired": []}
    groups = [("pooled_all", df)] + [(t, g) for t, g in df.groupby("tier")]
    for name, g in groups:
        rec = {"tier": name, "items": int(len(g)), "units": int(g.unit.nunique())}
        for w in ("pooled", "naive_borrow", "adapted", "full_memory"):
            est, ci = _boot(g[w].to_numpy(), g.unit.to_numpy())
            rec[w] = {"nll": est, "ci": ci}
        out["by_tier"].append(rec)
        for a, b in (("adapted", "naive_borrow"), ("adapted", "pooled"), ("naive_borrow", "pooled"), ("adapted", "full_memory")):
            est, ci = _boot((g[a] - g[b]).to_numpy(), g.unit.to_numpy())
            out["paired"].append({"tier": name, "a": a, "b": b, "difference": est, "ci": ci})
    cdf = pd.DataFrame(cost_rows)
    if len(cdf) > 3:
        rho = float(cdf[["cost", "nll"]].corr(method="spearman").iloc[0, 1])
        boot = []
        rng = np.random.default_rng(F.SEED)
        for _ in range(500):
            s = cdf.iloc[rng.integers(len(cdf), size=len(cdf))]
            boot.append(float(s[["cost", "nll"]].corr(method="spearman").iloc[0, 1]))
        out["cost_vs_nll"] = {"spearman": rho, "ci": np.nanquantile(boot, [0.025, 0.975]).tolist(), "pairs": int(len(cdf)),
                              "supported_share": float(cdf.supported.mean())}
    tdf = pd.DataFrame(table_rows)
    if len(tdf):
        agg = tdf.groupby("signature").agg(realised=("realised", "mean"), table_success=("table_success", "mean"),
                                           items=("realised", "size"), trials=("trials", "mean")).reset_index()
        out["adaptation_table_heldout"] = agg.round(4).to_dict("records")
    out["cost_rows"] = cdf.round(4).to_dict("records")
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
