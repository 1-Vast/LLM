"""Independent arithmetic on three already-exposed historical score exports.

No imports of the historical pipeline or root's audit; no raw/ZIP/reserve reads,
model fitting, new observations, stochastic simulation, or provider requests.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261022/update_value_qualification/skeptic"
RECORDS = ROOT / "research/feedback_propagation_20261018/records"
SECTIONS = ("A_B3", "C_noise_seed2")
ARMS = ("ridge", "R1")
DELTA = .1875


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def integer_vector(value, length, name):
    a = np.asarray(value)
    check(a.shape == (length,) and np.issubdtype(a.dtype, np.integer) and np.all(a >= 0), name)
    return a


def extract(record):
    n, fold = record["compounds"], record["fold"]
    check(isinstance(n, int) and n > 0, "Invalid compound count")
    sizes = integer_vector(record["campaign_sizes"], len(record["campaign_index"]), "Bad sizes")
    indices = record["campaign_index"]
    check(len(record["family"]) == n and int(sizes.sum()) == n, "Family/size length mismatch")
    flattened = []
    for size, ix in zip(sizes, indices):
        check(isinstance(ix, list) and len(ix) == size, "Campaign index size mismatch")
        check(all(isinstance(i, int) for i in ix), "Noninteger compound index")
        flattened.extend(ix)
    check(sorted(flattened) == list(range(n)), "Campaign indices do not partition compounds")
    values = np.zeros((2, len(sizes), 2), dtype=int)
    checks = []
    for draw, section in enumerate(SECTIONS):
        for arm_index, arm in enumerate(ARMS):
            leaf = record[section][arm]["unmeasured"]
            cc = integer_vector(leaf["campaign_compounds"], len(sizes), "Campaign compounds")
            check(np.array_equal(cc, sizes), "Campaign compound keys mismatch")
            hc = integer_vector(leaf["hits_c"], n, "Per-compound hit shape")
            campaign_hits = integer_vector(leaf["campaign_hits"], len(sizes), "Campaign hit shape")
            sums = np.asarray([hc[ix].sum() for ix in indices])
            check(np.array_equal(sums, campaign_hits), "Saved campaign hit sums differ")
            check(int(hc.sum()) == leaf["hits"], "Total hits differ from compound sums")
            values[draw, :, arm_index] = campaign_hits
            checks.append({"fold": fold, "section": section, "arm": arm,
                           "campaign_compounds_equal": True, "compound_and_campaign_hit_sums_equal": True})
    keep = sizes == 64
    rows = [{"fold": fold, "campaign_index": i, "compound_indices": indices[i],
             "family_count": len({record["family"][j] for j in indices[i]}),
             "u1": values[0, i].tolist(), "u2": values[1, i].tolist()}
            for i in np.flatnonzero(keep)]
    # Cast np.int64 index for JSON serialization.
    for row in rows:
        row["campaign_index"] = int(row["campaign_index"])
    excluded = [{"fold": fold, "campaign_index": i, "compounds": int(size),
                 "reason": "not originally complete64"} for i, size in enumerate(sizes) if size != 64]
    return rows, excluded, checks


def summarize(rows):
    check(len(rows) > 0, "No complete campaigns")
    keys = [(r["fold"], r["campaign_index"]) for r in rows]
    check(len(keys) == len(set(keys)), "Duplicate campaign key")
    values = np.asarray([[r["u1"] for r in rows], [r["u2"] for r in rows]], dtype=int)
    check(values.shape == (2, len(rows), 2), "Unaligned update table")
    folds = np.asarray([r["fold"] for r in rows])
    require_folds = sorted(set(folds.tolist()))
    check(len(require_folds) >= 2, "LOFO needs at least two folds")
    differences = values[:, :, 1] - values[:, :, 0]
    non_ties = np.all(differences != 0, axis=0)
    same_sign = int(np.sum((differences[0] * differences[1] > 0) & non_ties))
    strict_n = int(non_ties.sum())
    correlation = float(np.corrcoef(differences)[0, 1]) if np.all(np.std(differences, axis=1) > 0) else None
    directions = {}
    for select, evaluate in ((0, 1), (1, 0)):
        choose = (values[select, :, 1] > values[select, :, 0]).astype(int)
        realized = values[evaluate, np.arange(len(rows)), choose]
        fixed_means = values[evaluate].mean(axis=0)
        hindsight_fixed = int(fixed_means[1] > fixed_means[0])
        lofo = np.empty(len(rows), dtype=int)
        per_fold = {}
        for fold in require_folds:
            test = folds == fold
            train = ~test
            means = values[select, train].mean(axis=0)
            fixed = int(means[1] > means[0])
            lofo[test] = fixed
            per_fold[str(fold)] = {"campaigns": int(test.sum()), "fixed_selected_on_other_folds": ARMS[fixed],
                "training_selection_draw_means": dict(zip(ARMS, means.tolist())),
                "chosen_mean": float(realized[test].mean()),
                "evaluation_fixed_means": dict(zip(ARMS, values[evaluate, test].mean(axis=0).tolist())),
                "gain_vs_lofo": float(np.mean(realized[test] - values[evaluate, test, fixed]))}
        lofo_values = values[evaluate, np.arange(len(rows)), lofo]
        directions[f"{select + 1}_to_{evaluate + 1}"] = {
            "chosen_mean": float(realized.mean()), "chosen_total": int(realized.sum()),
            "choices": [ARMS[i] for i in choose], "chosen_values": realized.tolist(),
            "fixed_means": dict(zip(ARMS, fixed_means.tolist())),
            "gain_vs_each_fixed": dict(zip(ARMS, (realized.mean() - fixed_means).tolist())),
            "hindsight_evaluation_fixed": ARMS[hindsight_fixed],
            "gain_vs_hindsight_fixed": float(np.mean(realized - values[evaluate, :, hindsight_fixed])),
            "lofo_choices": [ARMS[i] for i in lofo], "lofo_values": lofo_values.tolist(),
            "lofo_mean": float(lofo_values.mean()), "gain_vs_lofo": float(np.mean(realized - lofo_values)),
            "per_campaign_gain_vs_lofo": (realized - lofo_values).tolist(), "per_fold": per_fold,
            "selection_draw_ties": int(np.sum(differences[select] == 0)),
            "selection_draw_hindsight_best_mean": float(np.max(values[select], axis=1).mean()),
            "evaluation_draw_hindsight_best_mean": float(np.max(values[evaluate], axis=1).mean())}
    symmetric = {key: float(np.mean([d[key] for d in directions.values()]))
                 for key in ("chosen_mean", "gain_vs_hindsight_fixed", "gain_vs_lofo")}
    gate = all(d["gain_vs_hindsight_fixed"] >= DELTA for d in directions.values())
    return {"complete_campaigns": len(rows), "complete_compounds": len(rows) * 64,
            "fold_campaign_counts": {str(f): int(np.sum(folds == f)) for f in require_folds},
            "differences_R1_minus_ridge": differences.tolist(),
            "ties_per_draw": [int(np.sum(d == 0)) for d in differences],
            "strict_non_tie_campaigns": strict_n, "strict_sign_agreement_count": same_sign,
            "strict_sign_agreement_rate": same_sign / strict_n if strict_n else None,
            "strict_sign_reversals": strict_n - same_sign, "difference_pearson": correlation,
            "directions": directions, "symmetric": symmetric,
            "within_draw_hindsight_best_means": np.max(values, axis=2).mean(axis=1).tolist(),
            "fixed_means_by_draw": [dict(zip(ARMS, values[d].mean(axis=0).tolist())) for d in range(2)],
            "delta_hits_per_complete64": DELTA, "descriptive_continuation_pass": gate,
            "decision": "CONDITIONAL_QUALIFICATION_ONLY" if gate else "STOP_THIS_EXACT_TWO_DRAW_CHOOSER_EXPANSION"}


def run():
    output = LOG / "HISTORICAL_INDEPENDENT_RECOMPUTE.json"
    check(not output.exists(), "Refuse to overwrite independent evidence")
    paths = [RECORDS / f"E_fold{f}.json" for f in (2, 3, 4)]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    freeze = json.loads((LOG.parent / "HISTORICAL_AUDIT_FREEZE.json").read_text(encoding="utf-8"))
    check(all(freeze["files"][name] == digest for name, digest in before.items()), "Historical frozen input hash mismatch")
    rows, excluded, checks, tables = [], [], [], []
    for fold, path in zip((2, 3, 4), paths):
        record = json.loads(path.read_text(encoding="utf-8"))
        check(record["fold"] == fold, "Record fold identity mismatch")
        r, e, c = extract(record)
        rows.extend(r)
        excluded.extend(e)
        checks.extend(c)
        tables.append(record["tables_sha256"])
    check(len(set(tables)) == 1, "Historical source-table receipts differ")
    result = summarize(rows)
    after = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    check(before == after, "Historical exports changed during verification")
    result.update(utc=datetime.now(timezone.utc).isoformat(), auditor_sha256=sha(Path(__file__)),
                  input_sha256_before=before, input_sha256_after=after,
                  historical_protocol_sha256=sha(LOG.parent / "HISTORICAL_AUDIT_PROTOCOL.md"),
                  input_checks=checks, excluded=excluded, campaigns=rows,
                  scope="posthoc exposed-score synthetic-noise choice audit; not measured replication or deployable selection",
                  model_fits=0, new_measurements=0, raw_protected_reserve_reads=0,
                  imports_root_audit_or_pipeline=False)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("complete_campaigns", "ties_per_draw", "strict_sign_agreement_rate",
        "difference_pearson", "symmetric", "descriptive_continuation_pass", "decision")}))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-exposed-record-audit", action="store_true")
    args = parser.parse_args()
    if not args.run_exposed_record_audit:
        parser.error("Explicit --run-exposed-record-audit required")
    try:
        run()
    except Exception as error:
        LOG.mkdir(parents=True, exist_ok=True)
        with (LOG / "AUDIT_FAILURES.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "error": str(error),
                                     "type": type(error).__name__, "code_sha256": sha(Path(__file__))}) + "\n")
        raise
