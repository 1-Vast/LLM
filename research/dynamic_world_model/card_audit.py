"""Calibration of scenario cards over the whole menu, applicability refusals, and T5 (branches vs single mean).

File summary
- Path: research/dynamic_world_model/card_audit.py
- Purpose: a policy only reveals the outcome of the action it chose. This audit scores every card
  against the outcome the held-out compound's real measurement would have produced for *every*
  menu action, so calibration is measured on the whole served domain, refusals can be compared
  with what an unrefused estimate would have said, and T5 compares three predictive
  distributions of the validator outcome under the true hypothesis.
- Core points:
  - T5 arms: `multi_branch` (each measured reference compound of the true class is a branch;
    Jeffreys smoothing over four outcomes), `single_mean` (the class centroid read by the validator
    after adding sampled replicate noise, 50 draws), `pooled_marginal` (outcomes of all pool-class
    references at that condition, ignoring mechanism).
  - Epistemic uncertainty of a branch estimate is its Dirichlet posterior variance from the
    reference count; aleatoric variation is the spread of outcomes among references.
- Run: python research/dynamic_world_model/card_audit.py
- Depends on: common.py, episodes.py
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

import common as C
import episodes as E

CATEGORIES = ("correct", "wrong", "ambiguous", "undetected")
DRAWS = 50


def realised(outcome: str, h1: str, h2: str, truth: str) -> str | None:
    if outcome == "quality_failed":
        return None
    if outcome in ("undetected", "ambiguous"):
        return outcome
    eliminated = h2 if outcome == "eliminate_b" else h1
    return "wrong" if eliminated == truth else "correct"


def branch_distribution(counts: dict) -> np.ndarray:
    n = np.array([counts[c] for c in CATEGORIES], dtype=float)
    return (n + 0.5) / (n.sum() + 0.5 * len(CATEGORIES))


def noise_pool(data: C.Data, key_line_time, train: set) -> np.ndarray:
    rows = [r for (line, t, _), comp in data.index.items() if (line, t) == key_line_time
            for c, r in comp.items() if c in train and C.qc_passed(data, r)]
    return ((data.rep1[rows] - data.rep2[rows]) / math.sqrt(2.0)).astype(np.float64)


def single_mean_distribution(ctx: E.FoldContext, key, truth: str, other: str, pool: np.ndarray, threshold: float,
                             rng) -> np.ndarray | None:
    t = ctx.ft.tables[key]
    members = np.flatnonzero(t.klass == truth)
    if len(members) < 2:
        return None
    centroid = t.Y[members].mean(0)
    counts = dict.fromkeys(CATEGORIES, 0)
    for _ in range(DRAWS):
        e1, e2 = pool[rng.integers(len(pool))], pool[rng.integers(len(pool))]
        r1, r2 = centroid + e1, centroid + e2
        detected = C._pearson(r1, r2) >= threshold
        reading = C.read_profile(ctx.ft, key, 0.5 * (r1 + r2), detected, truth, other, ctx.params)
        counts[realised(reading["outcome"], truth, other, truth)] += 1
    return branch_distribution(counts)


def pooled_marginal(ctx: E.FoldContext, key, other: str) -> np.ndarray:
    outcomes = C.loo_outcomes(ctx.ft, key, ctx.params["floor"], ctx.params["margin"])
    counts = dict.fromkeys(CATEGORIES, 0)
    for (compound, versus), outcome in outcomes.items():
        if versus != other:
            continue
        counts[{"eliminate_b": "correct", "eliminate_a": "wrong", "ambiguous": "ambiguous",
                "undetected": "undetected"}[outcome]] += 1
    return branch_distribution(counts)


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= edges[i + 1])
        if m.any():
            total += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(total)


def main() -> None:
    started = time.time()
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    magnitude = E.Magnitude(data, detected)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    rows, t5 = [], []
    for ctx, fold in E.contexts(data, protocol, detected, magnitude):
        rng = np.random.default_rng([C.SEED, fold, ord(ctx.tier.name), 5])
        train = {c for c in comp.index if comp.fold[c] != fold}
        pools = {}
        loose = dict(ctx.params)
        for compound, truth, decoy, h1, h2 in E.episode_list(ctx, fold):
            for key in ctx.tier.keys:
                result = E.execute(ctx, compound, key, h1, h2)
                outcome = realised(result["outcome"], h1, h2, truth)
                card = E.card_for(ctx, key, h1, h2)
                shadow = C.card(ctx.ft, key, h1, h2, loose, minimum_references=1) if not card.get("served") else card
                truth_label = "H1" if truth == h1 else "H2"
                rows.append({"tier": ctx.tier.name, "fold": fold, "compound": compound, "skeleton": comp.skeleton[compound],
                             "truth": truth, "decoy": decoy, "action": C.action_id(key), "served": bool(card.get("served")),
                             "refusal": card.get("reason"), "p_correct": card.get("p_correct"),
                             "shadow_p_correct": shadow.get("p_correct") if shadow.get("served") else None,
                             "branch_p_correct_truth": (card["branches"][truth_label]["p_correct"] if card.get("served") else None),
                             "references_truth": (card["branches"][truth_label]["references"] if card.get("served") else None),
                             "outcome": outcome, "correct": None if outcome is None else float(outcome == "correct")})
                if outcome is None or not card.get("served"):
                    continue
                branch = card["branches"][truth_label]
                n = branch["references"]
                multi = branch_distribution({c: round(branch[f"p_{c}"] * n) for c in CATEGORIES})
                line_time = (key[0], key[1])
                if line_time not in pools:
                    pools[line_time] = noise_pool(data, line_time, train)
                threshold = null[f"{key[0]}|{key[1]:g}"]["threshold"]
                single = single_mean_distribution(ctx, key, truth, decoy, pools[line_time], threshold, rng)
                marginal = pooled_marginal(ctx, key, decoy)
                j = CATEGORIES.index(outcome)
                record = {"tier": ctx.tier.name, "compound": compound, "skeleton": comp.skeleton[compound], "action": C.action_id(key),
                          "truth": truth, "decoy": decoy, "outcome": outcome, "references": n,
                          "epistemic_var_correct": float(multi[0] * (1 - multi[0]) / (n + 2 + 1))}
                for name, dist in (("multi_branch", multi), ("single_mean", single), ("pooled_marginal", marginal)):
                    if dist is None:
                        record[f"logloss:{name}"] = None
                        record[f"brier:{name}"] = None
                        continue
                    onehot = np.zeros(len(CATEGORIES)); onehot[j] = 1.0
                    record[f"logloss:{name}"] = float(-math.log(max(dist[j], 1e-9)))
                    record[f"brier:{name}"] = float(((dist - onehot) ** 2).sum())
                t5.append(record)
        print(f"{ctx.tier.name} fold {fold} {time.time() - started:.0f}s", flush=True)
    audit = pd.DataFrame(rows)
    branches = pd.DataFrame(t5)
    out = C.OUTPUTS / "card_audit"
    out.mkdir(parents=True, exist_ok=True)
    audit.to_csv(out / "card_outcomes.csv", index=False)
    branches.to_csv(out / "t5_branches.csv", index=False)
    summary = {"protocol_hashes": C.frozen_hashes(), "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    for tier, sub in audit.groupby("tier"):
        served = sub[sub.served & sub.correct.notna()]
        refused = sub[~sub.served & sub.correct.notna()]
        shadow = refused[refused.shadow_p_correct.notna()]
        summary[tier] = {
            "menu_actions_scored": int(sub.correct.notna().sum()), "served_fraction": float(sub.served.mean()),
            "served": {"n": int(len(served)), "mean_predicted": float(served.p_correct.mean()), "mean_realised": float(served.correct.mean()),
                       "ece": ece(served.p_correct.to_numpy(float), served.correct.to_numpy(float)),
                       "brier": float(((served.p_correct - served.correct) ** 2).mean()),
                       "branch_truth_ece": ece(served.branch_p_correct_truth.to_numpy(float), served.correct.to_numpy(float))},
            "refused": {"n": int(len(refused)), "realised_correct_rate": float(refused.correct.mean()) if len(refused) else None,
                        "reasons": refused.refusal.str.split(":").str[0].value_counts().to_dict(),
                        "shadow_n": int(len(shadow)),
                        "shadow_ece": ece(shadow.shadow_p_correct.to_numpy(float), shadow.correct.to_numpy(float)) if len(shadow) else None,
                        "shadow_brier": float(((shadow.shadow_p_correct - shadow.correct) ** 2).mean()) if len(shadow) else None},
        }
        b = branches[branches.tier == tier]
        both = b.dropna(subset=["logloss:single_mean"])
        summary[tier]["T5"] = {
            "n": int(len(b)), "n_with_single_mean": int(len(both)),
            **{f"logloss:{name}": float(both[f"logloss:{name}"].mean()) for name in ("multi_branch", "single_mean", "pooled_marginal")},
            **{f"brier:{name}": float(both[f"brier:{name}"].mean()) for name in ("multi_branch", "single_mean", "pooled_marginal")},
            "P5_multi_minus_single_logloss": _bootstrap(both["logloss:multi_branch"] - both["logloss:single_mean"], both.skeleton),
            "multi_minus_marginal_logloss": _bootstrap(both["logloss:multi_branch"] - both["logloss:pooled_marginal"], both.skeleton),
            "logloss_by_reference_count": b.groupby(pd.cut(b.references, [0, 2, 4, 8, 1000])).agg(
                n=("references", "size"), logloss=("logloss:multi_branch", "mean"),
                epistemic_var=("epistemic_var_correct", "mean")).reset_index().astype({"references": str}).to_dict("records"),
            "outcome_mix": b.outcome.value_counts(normalize=True).round(3).to_dict(),
        }
    C.write_json(out / "summary.json", C.clean(summary))
    print(json.dumps(C.clean(summary), indent=1, default=str)[:6000])


def _bootstrap(values: pd.Series, clusters: pd.Series) -> dict:
    import analyze as A
    return A.bootstrap_mean(values.reset_index(drop=True), clusters.reset_index(drop=True))


if __name__ == "__main__":
    main()
