"""Score the decision episodes: per-policy outcomes, regret, lab cost, and the registered contrasts.

File summary
- Path: research/dynamic_world_model/analyze.py
- Purpose: turn `episodes.jsonl` (and any language-model episode files) into the tables the
  protocol names: correct-decision and wrong-elimination rates, utility and regret against the
  oracle, lab cost and days to the first elimination, 72 h choice after an undetected 24 h result,
  and the P1/P2/P4 differences with skeleton-clustered bootstrap intervals.
- Core points:
  - The random policy is averaged over its 20 seeds within each episode before any aggregation.
  - Intervals resample skeleton units (compounds sharing a skeleton move together), 2,000 draws,
    seed 20260926; a difference is always paired on the same episodes.
- Run: python research/dynamic_world_model/analyze.py [extra episode files ...]
- Depends on: common.py, numpy, pandas
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import common as C

FINALS = ("correct", "wrong", "exhausted", "undetermined", "deferred")


def load_episodes(paths) -> pd.DataFrame:
    rows = []
    for path in paths:
        with Path(path).open(encoding="utf-8") as stream:
            for line in stream:
                r = json.loads(line)
                first72 = None
                steps = r.get("steps", [])
                if len(steps) >= 1 and steps[0]["key"][1] == 24.0 and steps[0]["outcome"] == "undetected":
                    first72 = len(steps) >= 2 and steps[1]["key"][1] == 72.0
                rows.append({"tier": r["tier"], "fold": r["fold"], "policy": r["policy"], "seed": r.get("seed"),
                             "compound": r["compound"], "truth": r["truth"], "decoy": r["decoy"],
                             "final": r["final"], "utility": r["utility"], "measurements": r["measurements"],
                             "days": r["days"], "wells": r["wells"], "days_to_elimination": r["days_to_elimination"],
                             "wells_to_elimination": r["wells_to_elimination"], "chose_72h_after_undetected_24h": first72,
                             "chose_72h_ever": any(s["key"][1] == 72.0 for s in steps),
                             "qc_failed_steps": sum(1 for s in steps if s["outcome"] == "quality_failed")})
    frame = pd.DataFrame(rows)
    for f in FINALS:
        frame[f] = (frame.final == f).astype(float)
    frame["wrong_any"] = frame.wrong + frame.exhausted
    frame["eliminated"] = frame.correct + frame.wrong_any
    return frame


def collapse_random(frame: pd.DataFrame) -> pd.DataFrame:
    """Average the random policy's seeds within each episode."""
    keys = ["tier", "fold", "policy", "compound", "truth", "decoy"]
    numeric = ["utility", "measurements", "days", "wells", *FINALS, "wrong_any", "eliminated", "qc_failed_steps"]
    rnd = frame[frame.policy == "random"]
    rest = frame[frame.policy != "random"]
    if rnd.empty:
        return rest
    agg = rnd.groupby(keys, as_index=False)[numeric].mean()
    agg["days_to_elimination"] = rnd.groupby(keys).days_to_elimination.mean().to_numpy()
    agg["wells_to_elimination"] = rnd.groupby(keys).wells_to_elimination.mean().to_numpy()
    agg["chose_72h_after_undetected_24h"] = None
    agg["chose_72h_ever"] = rnd.groupby(keys).chose_72h_ever.mean().to_numpy()
    return pd.concat([rest, agg], ignore_index=True)


def skeleton_map() -> dict:
    comp = pd.read_csv(C.FROZEN / "compounds.csv")
    return dict(zip(comp.compound.astype(str).str.strip(), comp.skeleton))


def bootstrap_mean(values: pd.Series, clusters: pd.Series, draws: int = 2000, seed: int = C.SEED) -> dict:
    frame = pd.DataFrame({"v": values.to_numpy(dtype=float), "c": clusters.to_numpy()})
    frame = frame[np.isfinite(frame.v)]
    if frame.empty:
        return {"mean": None, "low": None, "high": None, "n": 0, "clusters": 0}
    sums = frame.groupby("c").v.agg(["sum", "count"])
    s, n = sums["sum"].to_numpy(), sums["count"].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), size=(draws, len(s)))
    stats = s[idx].sum(1) / n[idx].sum(1)
    return {"mean": float(s.sum() / n.sum()), "low": float(np.quantile(stats, 0.025)),
            "high": float(np.quantile(stats, 0.975)), "n": int(n.sum()), "clusters": int(len(s))}


def paired(frame: pd.DataFrame, tier: str, a: str, b: str, metric: str, skeleton: dict) -> dict:
    """Paired difference a - b on the episodes both policies ran; tier "all" pools the tiers."""
    keys = ["tier", "compound", "truth", "decoy"]
    scope = frame if tier == "all" else frame[frame.tier == tier]
    x = scope[scope.policy == a].set_index(keys)[metric]
    y = scope[scope.policy == b].set_index(keys)[metric]
    joined = pd.concat([x.rename("a"), y.rename("b")], axis=1, join="inner").dropna()
    diff = joined.a - joined.b
    clusters = pd.Series([skeleton[k[1]] for k in joined.index], index=joined.index)
    return {"a": a, "b": b, "metric": metric, "tier": tier, **bootstrap_mean(diff, clusters)}


def table(frame: pd.DataFrame, skeleton: dict) -> list[dict]:
    rows = []
    oracle = frame[frame.policy == "oracle"].set_index(["tier", "compound", "truth", "decoy"]).utility
    for (tier, policy), sub in frame.groupby(["tier", "policy"]):
        clusters = sub.compound.map(skeleton)
        regret = oracle.reindex(pd.MultiIndex.from_frame(sub[["tier", "compound", "truth", "decoy"]])).to_numpy() - sub.utility.to_numpy()
        elim = sub[sub.eliminated > 0]
        after = sub.chose_72h_after_undetected_24h.dropna()
        rows.append({
            "tier": tier, "policy": policy, "episodes": int(len(sub)), "compounds": int(sub.compound.nunique()),
            "correct": bootstrap_mean(sub.correct, clusters), "wrong_elimination": bootstrap_mean(sub.wrong_any, clusters),
            "undetermined": float(sub.undetermined.mean()), "deferred": float(sub.deferred.mean()),
            "utility": bootstrap_mean(sub.utility, clusters),
            "regret": bootstrap_mean(pd.Series(regret, index=sub.index), clusters),
            "mean_measurements": float(sub.measurements.mean()), "mean_days": float(sub.days.mean()),
            "mean_wells": float(sub.wells.mean()),
            "days_to_elimination_when_reached": float(elim.days_to_elimination.mean()) if len(elim) else None,
            "wrong_among_eliminations": float(sub.wrong_any.sum() / sub.eliminated.sum()) if sub.eliminated.sum() else None,
            "qc_failed_steps_per_episode": float(sub.qc_failed_steps.mean()),
            "chose_72h_after_undetected_24h": (float(after.astype(float).mean()) if len(after) else None),
            "episodes_with_undetected_24h_first": int(len(after)),
            "chose_72h_ever": float(sub.chose_72h_ever.astype(float).mean()),
        })
    return rows


def render(rows: list[dict]) -> str:
    def ci(d):
        return "n/a" if d["mean"] is None else f"{d['mean']:.3f} [{d['low']:.3f}, {d['high']:.3f}]"

    lines = ["| Tier | Policy | Episodes | Correct | Wrong elim. | Undetermined | Deferred | Utility | Regret | Days | Days to elim. | 72 h after undetected 24 h |",
             "|---|---|---:|---|---|---:|---:|---|---|---:|---:|---:|"]
    order = ["oracle", "separation", "dyn_ref", "dyn_model", "magnitude", "cost_only", "fixed", "random", "separation_permuted"]
    for r in sorted(rows, key=lambda r: (r["tier"], order.index(r["policy"]) if r["policy"] in order else 99, r["policy"])):
        to_elim = r["days_to_elimination_when_reached"]
        to_elim_text = "" if to_elim is None else f"{to_elim:.1f}"
        after = r["chose_72h_after_undetected_24h"]
        after_text = "" if after is None else f"{after:.2f} (n={r['episodes_with_undetected_24h_first']})"
        lines.append(f"| {r['tier']} | {r['policy']} | {r['episodes']} | {ci(r['correct'])} | {ci(r['wrong_elimination'])} | "
                     f"{r['undetermined']:.3f} | {r['deferred']:.3f} | {ci(r['utility'])} | {ci(r['regret'])} | "
                     f"{r['mean_days']:.1f} | {to_elim_text} | {after_text} |")
    return chr(10).join(lines)


def main(extra: list[str]) -> None:
    paths = [C.OUTPUTS / "episodes" / "episodes.jsonl", *extra]
    frame = collapse_random(load_episodes(paths))
    skeleton = skeleton_map()
    rows = table(frame, skeleton)
    contrasts = [
        paired(frame, "B", "separation", "magnitude", "correct", skeleton),                 # P1
        paired(frame, "A", "dyn_ref", "magnitude", "correct", skeleton),                    # P2
        paired(frame, "A", "dyn_ref", "fixed", "correct", skeleton),                        # P2
        paired(frame, "B", "separation", "magnitude", "wrong_any", skeleton),
        paired(frame, "B", "separation_permuted", "magnitude", "correct", skeleton),
        paired(frame, "B", "separation", "separation_permuted", "correct", skeleton),
        paired(frame, "B", "magnitude", "cost_only", "correct", skeleton),
        paired(frame, "B", "separation", "random", "correct", skeleton),
        paired(frame, "B", "separation", "fixed", "correct", skeleton),
        paired(frame, "B", "separation", "magnitude", "utility", skeleton),
        paired(frame, "A", "separation", "magnitude", "correct", skeleton),
        paired(frame, "A", "dyn_ref", "separation", "correct", skeleton),
        paired(frame, "A", "dyn_ref", "magnitude", "utility", skeleton),
        paired(frame, "A", "dyn_ref", "magnitude", "wrong_any", skeleton),
        paired(frame, "A", "separation_permuted", "magnitude", "correct", skeleton),
    ]
    if {"deepseek_cards", "deepseek_base"} <= set(frame.policy):
        contrasts.append(paired(frame, "all", "deepseek_cards", "deepseek_base", "correct", skeleton))   # P4 as registered
    for policy in ("dyn_model", "deepseek_cards", "deepseek_base", "deepseek_cards_permuted", "jev_cards", "jev_base"):
        if policy in set(frame.policy):
            for tier in sorted(set(frame[frame.policy == policy].tier)):
                for other in ("dyn_ref", "separation", "magnitude", "fixed", "cost_only", "deepseek_base", "deepseek_cards"):
                    if other != policy and other in set(frame[frame.tier == tier].policy):
                        contrasts.append(paired(frame, tier, policy, other, "correct", skeleton))
    out = C.OUTPUTS / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    C.write_json(out / "episode_summary.json", C.clean({"rows": rows, "contrasts": contrasts,
                                                        "protocol_hashes": C.frozen_hashes(), "inputs": [str(p) for p in paths]}))
    (out / "episode_table.md").write_text(render(rows) + "\n", encoding="utf-8")
    print(render(rows))
    for c in contrasts:
        print(f"{c['tier']} {c['metric']}: {c['a']} - {c['b']} = {c['mean']:.3f} [{c['low']:.3f}, {c['high']:.3f}] (n={c['n']}, clusters={c['clusters']})"
              if c["mean"] is not None else f"{c['tier']} {c['a']} - {c['b']}: no paired episodes")


if __name__ == "__main__":
    main(sys.argv[1:])
