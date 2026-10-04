"""WS1 step 3a: O'Neil 2016 repeat batch (batch 3) as an independent-validation source.

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws1_feedback_validation/oneil_validation_inventory.py
- Purpose: describe the repeat batch's design (which experiments, how chosen, single-agent
  re-measurement, overlap with the 22,737-row library), then join it to every decomposition
  arm's purchases: validated hits found, validation coverage, validation rate among purchased
  primary hits; and test whether the in-context drug-in-line effect learned from the primary
  screen predicts the repeat-batch label (a shared-single-agent artefact would predict the
  primary label but not an independently re-measured one).
- Interfaces: run the file with PYTHONPATH="src;." [DECOMPOSITION_RUN].
- Depends on: numpy, research.certified_discovery.screens (frozen; private readers reused).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from research.certified_discovery import screens  # noqa: E402
from research.certified_discovery.screens import CACHE, load_library  # noqa: E402
from research.certified_discovery.world import TransferWorld, WorldConfig  # noqa: E402

THR = screens.HIT_THRESHOLD


def boot(d, seed=20261003, n=10_000):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, d.size, size=(n, d.size))
    m = d[idx].mean(axis=1)
    return [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)]


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    run = argv[0] if argv else "step2_oneil"
    lib = load_library(CACHE / "oneil_v1.npz")
    singles, experiments = screens._oneil_experiments()
    out: dict = {}
    # ---------------------------------------------------------------- design of the batches
    by_batch = defaultdict(list)
    for e in experiments:
        by_batch[e["batch"]].append(e)
    out["batches"] = {b: {"experiments": len(v), "usable": sum(e["y"] is not None for e in v),
                          "lines": len({e["line"] for e in v}), "pairs": len({tuple(sorted((e["a"], e["b"]))) for e in v}),
                          "drugs": len({e["a"] for e in v} | {e["b"] for e in v})}
                      for b, v in sorted(by_batch.items())}
    single_batches = Counter(k[0] for k in singles)
    out["single_agent_curves_by_batch"] = dict(sorted(single_batches.items()))
    b3 = [e for e in by_batch.get("3", []) if e["y"] is not None]
    out["batch3_single_fallback"] = int(sum(e.get("single_batch_fallback", False) for e in b3))
    out["batch3_lines"] = dict(Counter(e["line"] for e in b3))
    out["batch3_pairs"] = dict(Counter("+".join(sorted((e["a"], e["b"]))) for e in b3).most_common(40))
    out["batch3_drugs"] = dict(Counter([e["a"] for e in b3] + [e["b"] for e in b3]).most_common())
    # ---------------------------------------------------------------- join to the library
    drug_index = {n: i for i, n in enumerate(lib.drugs)}
    line_index = {n: i for i, n in enumerate(lib.lines)}
    key_to_row = {(int(a), int(b), int(c)): i for i, (a, b, c) in enumerate(zip(lib.a, lib.b, lib.c))}
    repeat = defaultdict(list)
    unmatched = Counter()
    for e in b3:
        if e["a"] not in drug_index or e["b"] not in drug_index or e["line"] not in line_index:
            unmatched["name_not_in_library"] += 1
            continue
        i, j = sorted((drug_index[e["a"]], drug_index[e["b"]]))
        row = key_to_row.get((i, j, line_index[e["line"]]))
        if row is None:
            unmatched["triple_not_in_library"] += 1
            continue
        repeat[row].append(e["y"])
    rows_v = np.array(sorted(repeat))
    y_rep = np.array([np.mean(repeat[r]) for r in rows_v])
    y_pri = lib.y[rows_v]
    out["batch3_join"] = {"matched_library_rows": int(rows_v.size), "unmatched": dict(unmatched),
                          "pearson": float(np.corrcoef(y_pri, y_rep)[0, 1]),
                          "primary_hit_rate_in_V": float((y_pri > THR).mean()),
                          "repeat_hit_rate_in_V": float((y_rep > THR).mean()),
                          "library_hit_rate": float((lib.y > THR).mean()),
                          "repeat_hit_given_primary_hit": float((y_rep[y_pri > THR] > THR).mean()),
                          "repeat_hit_given_primary_nonhit": float((y_rep[y_pri <= THR] > THR).mean()),
                          "primary_hits_in_V": int((y_pri > THR).sum()),
                          "primary_hits_in_library": int((lib.y > THR).sum()),
                          "share_of_library_hits_in_V": float((y_pri > THR).sum() / (lib.y > THR).sum()),
                          "V_lines": int(np.unique(lib.c[rows_v]).size),
                          "V_pairs": int(np.unique(lib.a[rows_v] * 100 + lib.b[rows_v]).size)}
    # selection model: is V explained by pair identity (whole pairs x all lines) or by the label?
    pair_all = lib.a.astype(int) * 100 + lib.b
    v_pairs = np.unique(pair_all[rows_v])
    in_v_pair = np.isin(pair_all, v_pairs)
    in_v = np.zeros(lib.y.size, bool)
    in_v[rows_v] = True
    out["batch3_selection"] = {
        "library_rows_with_a_V_pair": int(in_v_pair.sum()),
        "coverage_of_V_pairs_across_lines": float(in_v.sum() / max(in_v_pair.sum(), 1)),
        "primary_hit_rate_rows_with_V_pair_not_in_V": float((lib.y[in_v_pair & ~in_v] > THR).mean()) if (in_v_pair & ~in_v).any() else None,
        "primary_label_mean_V": float(y_pri.mean()), "primary_label_mean_library": float(lib.y.mean()),
        "primary_label_quantiles_V": [float(q) for q in np.percentile(y_pri, [10, 25, 50, 75, 90])],
    }
    # within V-pair rows: does the primary label predict membership (selection on outcome)?
    sub = in_v_pair
    if sub.sum() > 0:
        lab = lib.y[sub]
        mem = in_v[sub]
        order = np.argsort(lab)
        ranks = np.empty(lab.size)
        ranks[order] = np.arange(lab.size)
        n1, n0 = mem.sum(), (~mem).sum()
        auc = (ranks[mem].sum() - n1 * (n1 - 1) / 2) / max(n1 * n0, 1)
        out["batch3_selection"]["auc_primary_label_predicts_membership_within_V_pairs"] = float(auc)
    per_line_v = Counter(lib.lines[c] for c in lib.c[rows_v])
    out["batch3_selection"]["V_rows_per_line"] = dict(sorted(per_line_v.items()))
    # ---------------------------------------------------------------- does in-context drug effect replicate?
    # For each V experiment, fit the frozen world for its line with feedback on ALL OTHER primary rows of
    # that line (a leave-one-out in-context estimate), and compare prediction with primary vs repeat labels.
    loo = []
    for line in np.unique(lib.c[rows_v]):
        world = TransferWorld(lib, int(line), WorldConfig())
        pos = {int(r): k for k, r in enumerate(world.rows)}
        truth = lib.y[world.rows]
        for r in rows_v[lib.c[rows_v] == line]:
            k = pos[int(r)]
            others = np.array([i for i in range(world.rows.size) if i != k])
            mean, _ = world.posterior(others, truth[others])
            loo.append((float(world.prior_target[k]), float(mean[k]), float(lib.y[r]), float(np.mean(repeat[int(r)]))))
    loo = np.array(loo)
    prior, post, prim, rep = loo.T
    ic = post - prior                               # in-context (offset + drug-in-line) component
    out["incontext_replication"] = {
        "n": int(loo.shape[0]),
        "corr_prior_primary": float(np.corrcoef(prior, prim)[0, 1]),
        "corr_prior_repeat": float(np.corrcoef(prior, rep)[0, 1]),
        "corr_posterior_primary": float(np.corrcoef(post, prim)[0, 1]),
        "corr_posterior_repeat": float(np.corrcoef(post, rep)[0, 1]),
        "corr_incontext_component_vs_primary_residual": float(np.corrcoef(ic, prim - prior)[0, 1]),
        "corr_incontext_component_vs_repeat_residual": float(np.corrcoef(ic, rep - prior)[0, 1]),
        "slope_repeat_residual_on_incontext": float(np.polyfit(ic, rep - prior, 1)[0]),
        "slope_primary_residual_on_incontext": float(np.polyfit(ic, prim - prior, 1)[0]),
        "note": "LOO in-context estimate uses all other primary rows of the line (far more than a campaign buys); "
                "V is outcome-selected, so correlations are within a truncated, synergy-enriched sample",
    }
    # ---------------------------------------------------------------- join arms' purchases to V
    lines = [json.loads(x) for x in open(HERE / "receipts" / run / "lines.jsonl", encoding="utf-8")]
    rep_hit = {int(r): float(np.mean(repeat[int(r)])) > THR for r in rows_v}
    arms = sorted(lines[0]["arms"])
    per_arm = {}
    per_line_metric = defaultdict(dict)
    for arm in arms:
        tot = Counter()
        for l in lines:
            rows = np.array(l["rows"])
            entries = l["arms"][arm] if isinstance(l["arms"][arm], list) else [l["arms"][arm]]
            acc = Counter()
            for ent in entries:
                bought = rows[[i for r in ent["purchases"] for i in r]]
                pri_hit = lib.y[bought] > THR
                in_val = np.array([int(b) in rep_hit for b in bought])
                val_hit = np.array([rep_hit.get(int(b), False) for b in bought])
                acc["bought"] += bought.size
                acc["primary_hits"] += int(pri_hit.sum())
                acc["in_V"] += int(in_val.sum())
                acc["primary_hits_in_V"] += int((pri_hit & in_val).sum())
                acc["validated_hits"] += int((pri_hit & val_hit).sum())
                acc["repeat_hits_any"] += int(val_hit.sum())
            for k, v in acc.items():
                acc[k] = v / len(entries)
            per_line_metric[arm][l["line"]] = dict(acc)
            tot.update(acc)
        per_arm[arm] = {k: round(v, 2) for k, v in tot.items()}
        per_arm[arm]["validation_rate_among_tested_primary_hits"] = round(
            tot["validated_hits"] / max(tot["primary_hits_in_V"], 1e-9), 3)
        per_arm[arm]["coverage_primary_hits_in_V"] = round(tot["primary_hits_in_V"] / max(tot["primary_hits"], 1e-9), 3)
    out["arms_joined_to_V"] = per_arm
    contr = {}
    names = [l["line"] for l in lines]
    for a, b in (("full_mean", "static_mean"), ("full_phit", "static_phit"), ("full_mean", "history"),
                 ("full_mean", "gbm_static"), ("full_mean", "shufres_mean"), ("static_mean", "history")):
        for metric in ("validated_hits", "primary_hits_in_V", "primary_hits"):
            d = np.array([per_line_metric[a][n][metric] - per_line_metric[b][n][metric] for n in names])
            contr[f"{a} - {b} : {metric}"] = {"sum": round(float(d.sum()), 2), "mean": round(float(d.mean()), 3), "ci": boot(d)}
    out["contrasts_validated"] = contr
    # common-menu restricted comparison: oracle on V ceilings
    out["V_ceiling"] = {"validated_hits_available": int(sum(rep_hit[r] and lib.y[r] > THR for r in rep_hit)),
                        "repeat_hits_available": int(sum(rep_hit.values()))}
    dest = HERE / "receipts" / "step3_oneil_validation.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("batches", "single_agent_curves_by_batch", "batch3_single_fallback", "batch3_join",
                                         "batch3_selection", "incontext_replication", "V_ceiling")}, indent=1))
    for arm, v in per_arm.items():
        print(f"{arm:24s}", v)
    for k, v in contr.items():
        print(f"{k:55s}", v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
