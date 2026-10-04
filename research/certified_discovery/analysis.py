"""Summarise a replay: discovery, certification, naive claims, price and cost, with unit bootstraps.

File summary
- Path: research/certified_discovery/analysis.py
- Purpose: one deterministic summary per run directory; the unit of resampling is the target
  cell line (the campaign), and audit draws / random seeds are averaged within a line first.
- Core points: paired line-level contrasts with percentile bootstrap intervals (10,000 draws,
  fixed seed); FDR is the mean false-discovery proportion over lines x audit draws (empty
  selections count as 0, the definition the guarantee uses); refusals are counted by name.
- Interfaces: `load`, `summarise`, `main` (python -m research.certified_discovery.analysis RUN).
- Depends on: numpy.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

BOOTSTRAP = 10_000


def load(run: Path) -> list[dict]:
    with open(run / "campaigns.jsonl", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _bootstrap(values: np.ndarray, statistic=np.mean, seed: int = 20261003) -> list[float]:
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, values.size, size=(BOOTSTRAP, values.size))
    stats = statistic(values[draws], axis=1)
    return [float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))]


def _ratio_ci(numerator, denominator, seed: int = 20261003) -> list[float]:
    """Percentile bootstrap over lines for a ratio of sums."""
    num, den = np.asarray(numerator, float), np.asarray(denominator, float)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, num.size, size=(BOOTSTRAP, num.size))
    ratios = num[draws].sum(axis=1) / np.maximum(den[draws].sum(axis=1), 1e-9)
    return [float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))]


def per_line(records: list[dict]) -> dict[str, dict[str, dict]]:
    """arm -> line -> averaged metrics."""
    grouped: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        grouped[record["arm"]][record["line"]].append(record)
    table: dict[str, dict[str, dict]] = defaultdict(dict)
    for arm, lines in grouped.items():
        for line, runs in lines.items():
            certs = [c for run in runs for c in run["certify"]]
            row = {
                "line_hits": runs[0]["line_hits"], "budget": runs[0]["budget"],
                "exploit_hits": float(np.mean([run["exploit"]["hits"] for run in runs])),
                "certify_hits": float(np.mean([c["hits"] for c in certs])),
                "nominated": float(np.mean([c["nominated"] for c in certs])),
                "nominated_true": float(np.mean([c["nominated_true"] for c in certs])),
                "fdp": float(np.mean([c["fdp"] for c in certs])),
                "yield_bound": float(np.mean([c["yield_bound"] for c in certs])),
                "yield_covered": float(np.mean([c["yield_covered"] for c in certs])),
                "remainder_hits": float(np.mean([c["remainder_hits"] for c in certs])),
                "refusals": Counter(c["refusal"] for c in certs),
                "seconds": float(np.mean([run["seconds"] for run in runs])),
                "wells": float(np.mean([run["wells"] for run in runs])),
                "days": runs[0]["days"],
            }
            if "naive_fdp" in certs[0]:
                row.update({
                    "predicted_hits": float(np.mean([c["predicted_hits"] for c in certs])),
                    "predicted_true": float(np.mean([c["predicted_true"] for c in certs])),
                    "predicted_claimed": float(np.mean([(c["predicted_claimed_precision"] or 0.0) * c["predicted_hits"] for c in certs])),
                    "naive_nominated": float(np.mean([c["naive_nominated"] for c in certs])),
                    "naive_fdp": float(np.mean([c["naive_fdp"] for c in certs])),
                    "claimed_remainder_hits": float(np.mean([c["claimed_remainder_hits"] for c in certs])),
                })
            table[arm][line] = row
    return table


def summarise(records: list[dict], reference: str = "history", focus: str = "wm_full") -> dict:
    table = per_line(records)
    lines = sorted(table[next(iter(table))])
    out: dict = {"lines": len(lines), "arms": {}, "contrasts": {}}
    total_hits = sum(table[next(iter(table))][line]["line_hits"] for line in lines)
    for arm, rows in sorted(table.items()):
        exploit = np.array([rows[l]["exploit_hits"] for l in lines])
        certify = np.array([rows[l]["certify_hits"] for l in lines])
        fdp = np.array([rows[l]["fdp"] for l in lines])
        summary = {
            "exploit_hits_total": float(exploit.sum()), "certify_hits_total": float(certify.sum()),
            "recall_exploit": float(exploit.sum() / total_hits),
            "price_of_certification": float((exploit - certify).sum()),
            "price_ci": _bootstrap(exploit - certify, np.sum) if exploit.size > 1 else None,
            "nominated_total": float(sum(rows[l]["nominated"] for l in lines)),
            "nominated_true_total": float(sum(rows[l]["nominated_true"] for l in lines)),
            "fdr": float(fdp.mean()), "fdr_ci": _bootstrap(fdp),
            "lines_with_nominations": int(sum(rows[l]["nominated"] > 0 for l in lines)),
            "yield_bound_total": float(sum(rows[l]["yield_bound"] for l in lines)),
            "remainder_hits_total": float(sum(rows[l]["remainder_hits"] for l in lines)),
            "yield_coverage": float(np.mean([rows[l]["yield_covered"] for l in lines])),
            "refusals": {str(k or "CERTIFIED"): v for k, v in sum((rows[l]["refusals"] for l in lines), Counter()).items()},
            "seconds_per_campaign": float(np.mean([rows[l]["seconds"] for l in lines])),
            "wells_per_campaign": float(np.mean([rows[l]["wells"] for l in lines])),
            "days_per_campaign": float(rows[lines[0]]["days"]),
        }
        if "naive_fdp" in rows[lines[0]]:
            naive = np.array([rows[l]["naive_fdp"] for l in lines])
            claimed = sum(rows[l]["claimed_remainder_hits"] for l in lines)
            summary.update({
                "naive_fdr": float(naive.mean()), "naive_fdr_ci": _bootstrap(naive),
                "naive_nominated_total": float(sum(rows[l]["naive_nominated"] for l in lines)),
                "claimed_remainder_hits_total": float(claimed),
                "claimed_over_realised": float(claimed / max(summary["remainder_hits_total"], 1e-9)),
                "claimed_over_realised_ci": _ratio_ci([rows[l]["claimed_remainder_hits"] for l in lines],
                                                      [rows[l]["remainder_hits"] for l in lines]),
                "predicted_hits_total": float(sum(rows[l]["predicted_hits"] for l in lines)),
                "predicted_true_total": float(sum(rows[l]["predicted_true"] for l in lines)),
                "predicted_claimed_true_total": float(sum(rows[l]["predicted_claimed"] for l in lines)),
            })
        out["arms"][arm] = summary
    out["total_line_hits"] = int(total_hits)
    for arm in table:
        if arm == reference or reference not in table:
            continue
        for variant in ("exploit_hits", "certify_hits"):
            diff = np.array([table[arm][l][variant] - table[reference][l][variant] for l in lines])
            out["contrasts"][f"{arm}-{reference}:{variant}"] = {
                "sum": float(diff.sum()), "mean": float(diff.mean()), "ci_mean": _bootstrap(diff),
                "lines_better": int((diff > 0).sum()), "lines_worse": int((diff < 0).sum()),
            }
    if focus in table:
        for arm in table:
            if arm == focus:
                continue
            diff = np.array([table[focus][l]["certify_hits"] - table[arm][l]["exploit_hits"] for l in lines])
            out["contrasts"][f"{focus}[certify]-{arm}[exploit]"] = {
                "sum": float(diff.sum()), "mean": float(diff.mean()), "ci_mean": _bootstrap(diff),
                "lines_better": int((diff > 0).sum()), "lines_worse": int((diff < 0).sum()),
            }
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run")
    parser.add_argument("--reference", default="history")
    parser.add_argument("--focus", default="wm_full")
    args = parser.parse_args(argv)
    run = Path(args.run)
    summary = summarise(load(run), args.reference, args.focus)
    (run / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True), encoding="utf-8")
    print(f"{'arm':20s} {'exploit':>8s} {'certify':>8s} {'recall':>7s} {'nom':>6s} {'FDR':>6s} {'naiveFDR':>8s} {'claim/real':>10s} {'cover':>6s}")
    for arm, s in summary["arms"].items():
        print(f"{arm:20s} {s['exploit_hits_total']:8.1f} {s['certify_hits_total']:8.1f} {s['recall_exploit']:7.3f} "
              f"{s['nominated_total']:6.1f} {s['fdr']:6.3f} {s.get('naive_fdr', float('nan')):8.3f} "
              f"{s.get('claimed_over_realised', float('nan')):10.2f} {s['yield_coverage']:6.3f}")
    for key, c in summary["contrasts"].items():
        if key.endswith(":exploit_hits") or "[certify]" in key:
            print(f"{key:45s} sum {c['sum']:7.1f}  mean {c['mean']:6.2f} CI [{c['ci_mean'][0]:6.2f}, {c['ci_mean'][1]:6.2f}]  +{c['lines_better']}/-{c['lines_worse']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
