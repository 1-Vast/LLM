"""Post hoc exported-score audit; no model imports, fits or raw response access."""
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261022/update_value_qualification"
REC = ROOT / "research/feedback_propagation_20261018/records"
SECTIONS = ("A_B3", "C_noise_seed2")
ARMS = ("ridge", "R1")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def extract(records):
    utilities, labels, excluded = [], [], []
    for fold in (2, 3, 4):
        record = records[fold]
        n = record["compounds"]
        sizes, groups = record["campaign_sizes"], record["campaign_index"]
        if record["fold"] != fold or len(record["family"]) != n or len(sizes) != len(groups):
            raise ValueError("Fold/population identity mismatch")
        if sorted(i for group in groups for i in group) != list(range(n)):
            raise ValueError("Campaign partition is not exhaustive and disjoint")
        for size, group in zip(sizes, groups):
            if len(group) != size or not 0 < size <= 64:
                raise ValueError("Campaign size mismatch")
        values = {}
        for section in SECTIONS:
            for arm in ARMS:
                node = record[section][arm]["unmeasured"]
                hits, cells = node["campaign_hits"], node["hits_c"]
                if node["campaign_compounds"] != sizes or len(hits) != len(groups) or len(cells) != n:
                    raise ValueError("Section/arm campaign keys mismatch")
                if any(not isinstance(x, int) or x < 0 for x in cells + hits):
                    raise ValueError("Invalid hit counts")
                for hit, group in zip(hits, groups):
                    if hit > 32 or hit != sum(cells[i] for i in group):
                        raise ValueError("Campaign hit total mismatch")
                values[section, arm] = hits
        for ci, (size, group) in enumerate(zip(sizes, groups)):
            metadata = {"fold": fold, "campaign_index": ci, "compounds": size,
                        "family_count": len({record["family"][i] for i in group}),
                        "compound_indices": group}
            if size == 64:
                utilities.append([[values[s, a][ci] for a in ARMS] for s in SECTIONS])
                labels.append(metadata)
            else:
                excluded.append(metadata)
    if not labels:
        raise ValueError("No complete campaigns")
    return np.asarray(utilities, dtype=float).transpose(1, 0, 2), labels, excluded


def analyse(utilities, folds):
    u = np.asarray(utilities, dtype=float)
    folds = np.asarray(folds)
    if u.ndim != 3 or u.shape[0] != 2 or u.shape[2] != 2 or u.shape[1] != len(folds):
        raise ValueError("Expected draw x campaign x arm and aligned fold labels")
    if not np.isfinite(u).all() or len(np.unique(folds)) < 2:
        raise ValueError("Need finite utilities and multiple folds")
    n = len(folds)
    directions = {}
    delta = u[:, :, 1] - u[:, :, 0]
    for selection, evaluation in ((0, 1), (1, 0)):
        choices = (delta[selection] > 0).astype(int)
        selected = u[evaluation, np.arange(n), choices]
        fixed = u[evaluation].mean(axis=0)
        hindsight_fixed = int(fixed[1] > fixed[0])
        leave_fold_choices = np.zeros(n, dtype=int)
        fold_records = []
        for fold in np.unique(folds):
            target = folds == fold
            means = u[selection, ~target].mean(axis=0)
            chosen = int(means[1] > means[0])
            leave_fold_choices[target] = chosen
            fold_records.append({"fold": int(fold), "campaigns": int(target.sum()),
                                 "training_means": means.tolist(), "fixed_arm": ARMS[chosen],
                                 "cross_selected_mean": float(selected[target].mean()),
                                 "fixed_evaluation_mean": float(u[evaluation, target, chosen].mean())})
        leave_fold = u[evaluation, np.arange(n), leave_fold_choices]
        directions[str(selection + 1) + "_to_" + str(evaluation + 1)] = {
            "cross_selected_mean": float(selected.mean()),
            "fixed_evaluation_means": dict(zip(ARMS, fixed.tolist())),
            "gain_vs_each_fixed": dict(zip(ARMS, (selected.mean() - fixed).tolist())),
            "hindsight_evaluation_best_fixed_arm": ARMS[hindsight_fixed],
            "gain_vs_hindsight_evaluation_best_fixed": float(selected.mean() - fixed[hindsight_fixed]),
            "leave_fold_fixed_mean": float(leave_fold.mean()),
            "gain_vs_leave_fold_fixed": float((selected - leave_fold).mean()),
            "same_draw_hindsight_best_mean": float(u[selection].max(axis=1).mean()),
            "selection_ties": int((delta[selection] == 0).sum()),
            "chosen_arms": [ARMS[i] for i in choices],
            "cross_selected_hits": selected.tolist(),
            "leave_fold_fixed_arms": [ARMS[i] for i in leave_fold_choices],
            "leave_fold_fixed_hits": leave_fold.tolist(), "per_fold": fold_records,
        }
    both_strict = (delta != 0).all(axis=0)
    agree = (delta[0] * delta[1]) > 0
    reverse = (delta[0] * delta[1]) < 0
    correlation = (float(np.corrcoef(delta)[0, 1])
                   if np.all(np.std(delta, axis=1) > 0) else None)
    return {"campaigns": n, "arms": list(ARMS), "directions": directions,
            "differences_R1_minus_ridge": delta.tolist(),
            "strict_both_draws": int(both_strict.sum()),
            "strict_same_sign": int(agree.sum()), "strict_reversals": int(reverse.sum()),
            "strict_agreement_fraction": float(agree.sum() / both_strict.sum()) if both_strict.any() else None,
            "pearson_difference_correlation": correlation,
            "symmetric_gain_vs_hindsight_fixed": float(np.mean([
                row["gain_vs_hindsight_evaluation_best_fixed"] for row in directions.values()])),
            "symmetric_gain_vs_leave_fold_fixed": float(np.mean([
                row["gain_vs_leave_fold_fixed"] for row in directions.values()])),
            "historical_practical_scale": 0.1875,
            "descriptive_both_direction_screen": all(
                row["gain_vs_hindsight_evaluation_best_fixed"] >= 0.1875 for row in directions.values()),
            "interpretation": "unavailable outcome-based chooser, conditional synthetic-noise stability only; no iid CI"}


def main():
    freeze = json.loads((LOG / "HISTORICAL_AUDIT_FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["files"].items():
        if sha(ROOT / name) != expected:
            raise RuntimeError("Frozen historical-audit binding changed: " + name)
    write(LOG / "HISTORICAL_AUDIT_STARTED.json", {"scope": "historical exported-score audit",
                                                  "new_fits": 0, "new_measurements": 0})
    records = {fold: json.loads((REC / f"E_fold{fold}.json").read_text(encoding="utf-8"))
               for fold in (2, 3, 4)}
    utilities, labels, excluded = extract(records)
    result = analyse(utilities, [row["fold"] for row in labels])
    result.update(campaigns_metadata=labels, excluded_incomplete=excluded,
                  utilities=utilities.tolist(), frozen_inputs_unchanged=all(
                      sha(ROOT / name) == expected for name, expected in freeze["files"].items()))
    write(LOG / "HISTORICAL_CHOICE_AUDIT.json", result)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("campaigns_metadata", "utilities", "differences_R1_minus_ridge", "directions")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
