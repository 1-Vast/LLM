"""WS1 step 3b: is the in-context drug-in-line effect partly a shared single-agent reference artefact?

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws1_feedback_validation/oneil_reference_artifact.py
- Purpose: O'Neil labels are Bliss excess computed against ONE single-agent curve per drug x line
  (batch 1). Every pair containing drug a in line c shares that curve, so an error in it shifts
  all those labels together, which is exactly the structure the in-context drug-in-line effect
  u_a learns. Batch 3 re-measured the single agents of 18 drugs in 15 lines. This script
  (i) correlates the learned u_a(c) with the batch-1 minus batch-3 single-agent survival
  difference; (ii) re-references every primary (batch 1/2) combination of those 15 lines whose
  two drugs both have batch-3 singles, i.e. recomputes the label from the SAME combination wells
  with the independent batch-3 singles; (iii) scores every decomposition arm's purchases in that
  re-referenceable subset under both labels.
- Interfaces: run the file with PYTHONPATH="src;." [DECOMPOSITION_RUN].
- Depends on: numpy, research.certified_discovery (frozen; private readers reused, nothing edited).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from research.certified_discovery import screens  # noqa: E402
from research.certified_discovery.screens import CACHE, load_library  # noqa: E402
from research.certified_discovery.world import TransferWorld, WorldConfig  # noqa: E402

THR = screens.HIT_THRESHOLD


def boot_lines(values_by_line: dict, fn, seed=20261003, n=5000):
    keys = sorted(values_by_line)
    rng = np.random.default_rng(seed)
    stats = []
    for _ in range(n):
        pick = rng.integers(0, len(keys), len(keys))
        stats.append(fn([values_by_line[keys[i]] for i in pick]))
    return [round(float(np.nanpercentile(stats, 2.5)), 3), round(float(np.nanpercentile(stats, 97.5)), 3)]


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    run = argv[0] if argv else "step2_oneil"
    lib = load_library(CACHE / "oneil_v1.npz")
    singles = screens._read_singles()
    combos = screens._read_combinations()
    b3_keys = {(l, d) for (b, l, d) in singles if b == "3"}
    v_lines = sorted({l for l, _ in b3_keys})
    v_drugs = sorted({d for _, d in b3_keys})
    drug_index = {n: i for i, n in enumerate(lib.drugs)}
    line_index = {n: i for i, n in enumerate(lib.lines)}
    out = {"v_lines": v_lines, "v_drugs": v_drugs, "b3_single_curves": len(b3_keys)}

    # ------------------------------------------------ re-reference primary combinations with batch-3 singles
    reref = {}           # library row -> (orig label recomputed, re-referenced label)
    doses = defaultdict(set)
    for (batch, line, da, db), points in combos.items():
        if batch not in screens.LIBRARY_BATCHES or line not in v_lines:
            continue
        if (line, da) not in b3_keys or (line, db) not in b3_keys:
            continue
        i, j = sorted((drug_index[da], drug_index[db]))
        rows = np.flatnonzero((lib.a == i) & (lib.b == j) & (lib.c == line_index[line]))
        if rows.size != 1:
            continue
        s1a, s1b = singles[(batch, line, da)], singles[(batch, line, db)]
        s3a, s3b = singles[("3", line, da)], singles[("3", line, db)]
        orig, new = [], []
        for ca, cb, obs in points:
            doses[(line, da)].add(ca)
            doses[(line, db)].add(cb)
            e1 = min(screens._interp_log(*s1a, ca), 1.0) * min(screens._interp_log(*s1b, cb), 1.0)
            e3 = min(screens._interp_log(*s3a, ca), 1.0) * min(screens._interp_log(*s3b, cb), 1.0)
            orig.append(100 * (e1 - obs))
            new.append(100 * (e3 - obs))
        reref[int(rows[0])] = (float(np.mean(orig)), float(np.mean(new)))
    rows_r = np.array(sorted(reref))
    y_orig = np.array([reref[r][0] for r in rows_r])
    y_new = np.array([reref[r][1] for r in rows_r])
    out["rereferenced"] = {
        "rows": int(rows_r.size), "max_abs_diff_recomputed_vs_library": float(np.max(np.abs(y_orig - lib.y[rows_r]))),
        "pearson_orig_vs_reref": float(np.corrcoef(y_orig, y_new)[0, 1]),
        "sd_orig": float(y_orig.std()), "sd_reref": float(y_new.std()), "sd_diff": float((y_orig - y_new).std()),
        "hits_orig": int((y_orig > THR).sum()), "hits_reref": int((y_new > THR).sum()),
        "hits_both": int(((y_orig > THR) & (y_new > THR)).sum()),
        "reref_hit_given_orig_hit": float((y_new[y_orig > THR] > THR).mean()),
    }
    # ------------------------------------------------ single-agent survival difference vs learned u
    def mean_survival(curve, ds):
        return float(np.mean([min(screens._interp_log(*curve, d), 1.0) for d in sorted(ds)]))

    recs = []
    by_line = defaultdict(list)
    for line in v_lines:
        c = line_index[line]
        world = TransferWorld(lib, c, WorldConfig())
        truth = lib.y[world.rows]
        Z = world.Z_target
        resid = truth - world.prior_target
        cov = np.linalg.inv(world.A_inv + Z.T @ Z / world.s_noise)
        eff = cov @ (Z.T @ resid) / world.s_noise
        # re-referenced effect on the same rows where available: label change per drug
        pos = {int(r): k for k, r in enumerate(world.rows)}
        for drug in v_drugs:
            if (line, drug) not in b3_keys or ("1", line, drug) not in singles or not doses[(line, drug)]:
                continue
            d = drug_index[drug]
            ds = doses[(line, drug)]
            delta = mean_survival(singles[("1", line, drug)], ds) - mean_survival(singles[("3", line, drug)], ds)
            mine = [r for r in rows_r if lib.c[r] == c and (lib.a[r] == d or lib.b[r] == d)]
            shift = float(np.mean([reref[r][0] - reref[r][1] for r in mine])) if mine else np.nan
            rec = {"line": line, "drug": drug, "u_hat": float(eff[1 + d]), "delta_survival_b1_minus_b3": delta,
                   "mean_label_shift_orig_minus_reref": shift}
            recs.append(rec)
            by_line[line].append(rec)
    u = np.array([r["u_hat"] for r in recs])
    ds = np.array([r["delta_survival_b1_minus_b3"] for r in recs])
    sh = np.array([r["mean_label_shift_orig_minus_reref"] for r in recs])
    ok = np.isfinite(sh)

    def corr(group, x, y):
        xs = np.array([r[x] for g in group for r in g])
        ys = np.array([r[y] for g in group for r in g])
        m = np.isfinite(xs) & np.isfinite(ys)
        return float(np.corrcoef(xs[m], ys[m])[0, 1])

    out["u_vs_reference"] = {
        "n_drug_line": len(recs),
        "corr_u_hat_vs_delta_survival": float(np.corrcoef(u, ds)[0, 1]),
        "ci_lines": boot_lines(by_line, lambda g: corr(g, "u_hat", "delta_survival_b1_minus_b3")),
        "corr_u_hat_vs_label_shift": float(np.corrcoef(u[ok], sh[ok])[0, 1]),
        "ci_lines_shift": boot_lines(by_line, lambda g: corr(g, "u_hat", "mean_label_shift_orig_minus_reref")),
        "var_u_hat": float(u.var()), "var_label_shift": float(np.nanvar(sh)),
        "share_var_u_explained_by_shift_R2": float(np.corrcoef(u[ok], sh[ok])[0, 1] ** 2),
    }
    (HERE / "receipts" / "step3b_drug_line_effects.json").write_text(json.dumps(recs, indent=1), encoding="utf-8")

    # ------------------------------------------------ arms' purchases scored under both labels
    lines = [json.loads(x) for x in open(HERE / "receipts" / run / "lines.jsonl", encoding="utf-8")]
    lab = {int(r): (reref[r][0] > THR, reref[r][1] > THR, reref[r][1]) for r in rows_r}
    per_line = defaultdict(dict)
    totals = {}
    for arm in sorted(lines[0]["arms"]):
        acc_tot = defaultdict(float)
        for l in lines:
            if l["line"] not in v_lines:
                continue
            rows = np.array(l["rows"])
            entries = l["arms"][arm] if isinstance(l["arms"][arm], list) else [l["arms"][arm]]
            acc = defaultdict(float)
            for ent in entries:
                bought = rows[[i for r in ent["purchases"] for i in r]]
                inr = [int(b) for b in bought if int(b) in lab]
                acc["bought_in_R"] += len(inr)
                acc["hits_orig_in_R"] += sum(lab[b][0] for b in inr)
                acc["hits_reref_in_R"] += sum(lab[b][1] for b in inr)
                acc["hits_both_in_R"] += sum(lab[b][0] and lab[b][1] for b in inr)
            for k in acc:
                acc[k] /= len(entries)
                acc_tot[k] += acc[k]
            per_line[arm][l["line"]] = dict(acc)
        totals[arm] = {k: round(v, 2) for k, v in acc_tot.items()}
        totals[arm]["reref_confirmation_rate"] = round(acc_tot["hits_both_in_R"] / max(acc_tot["hits_orig_in_R"], 1e-9), 3)
    out["R_available"] = {"rows": int(rows_r.size), "hits_orig": int(sum(v[0] for v in lab.values())),
                          "hits_reref": int(sum(v[1] for v in lab.values())),
                          "hits_both": int(sum(v[0] and v[1] for v in lab.values()))}
    out["arms_in_R"] = totals
    rng_seed = 20261003
    contr = {}
    for a, b in (("full_mean", "static_mean"), ("full_mean", "history"), ("full_mean", "gbm_static"),
                 ("full_mean", "shufres_mean"), ("full_phit", "static_phit")):
        for metric in ("hits_orig_in_R", "hits_reref_in_R", "hits_both_in_R"):
            d = np.array([per_line[a][n][metric] - per_line[b][n][metric] for n in v_lines])
            rng = np.random.default_rng(rng_seed)
            bs = d[rng.integers(0, d.size, (10_000, d.size))].mean(axis=1)
            contr[f"{a} - {b} : {metric}"] = {"sum": round(float(d.sum()), 2), "mean": round(float(d.mean()), 3),
                                              "ci": [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)]}
    out["contrasts_in_R"] = contr
    (HERE / "receipts" / "step3b_reference_artifact.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("arms_in_R", "contrasts_in_R")}, indent=1))
    for k, v in totals.items():
        print(f"{k:24s}", v)
    for k, v in contr.items():
        print(f"{k:50s}", v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
