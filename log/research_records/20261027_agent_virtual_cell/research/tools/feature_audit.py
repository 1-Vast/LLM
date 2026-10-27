"""feature_audit.py - a reusable pre-flight check for multi-arm comparisons.

Five times in this programme an arm or a feature stopped carrying information in the evaluation
condition while still changing what a model did (R135, R144, R147, R138/R139, confirmed in R148).
The ninth standing rule was written down two rounds before it was actually executed, so the rule is
now code.

Three parts:
  1. feature level  - dispersion of each column on the evaluation set, the fraction of evaluation
                      values that never occurred in training (for integer codes), constant columns,
                      and DOMINATED_ON_EVAL (a single level dominating on evaluation but not in
                      training). Dispersion ratios are REPORTED as data but raise no warning: uniform
                      rescaling was measured to be an exact no-op for both a standardising ridge
                      (R152) and a quantile-binned gradient booster (R153)
  2. split level    - overlap between the training and evaluation key sets (catches in-sample pools)
  3. prediction level - dispersion of each arm's prediction on the evaluation set (catches constant
                      or degenerate arms)

Any trigger prints FLAG; the aggregate is returned as a boolean.

This is a necessary check, not a sufficient one.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def _dominant_frac(col):
    if len(col) == 0:
        return 0.0
    vals, counts = np.unique(col, return_counts=True)
    return float(counts.max() / counts.sum())


def _mixed_scale(col, min_frac=0.05, min_decades=2.0):
    """Detect a within-column unit-mixing accident.

    Uniform rescaling of a whole column is a no-op for the models used here (R152, R153), but scaling
    only PART of a column breaks the within-column ordering and costs a great deal: measured tree
    rank correlation fell by 0.10 in R154. That is the shape a unit-mixing accident takes, for example
    some rows in micromolar and others in nanomolar, so it is worth a dedicated check.

    Operates on continuous positive columns only; integer-like columns are skipped.
    """
    x = np.asarray(col, dtype=float)
    x = x[x > 0]
    if len(x) < 20:
        return None
    if np.allclose(x, np.round(x)):
        return None
    lg = np.log10(x)
    lo, hi = np.quantile(lg, 0.05), np.quantile(lg, 0.95)
    if (hi - lo) < min_decades:
        return None
    mid = (lo + hi) / 2.0
    lower = lg[lg <= mid]; upper = lg[lg > mid]
    if len(lower) < min_frac * len(lg) or len(upper) < min_frac * len(lg):
        return None
    gap = float(upper.min() - lower.max())
    if gap >= min_decades:
        return {"gap_decades": gap, "n_lower": int(len(lower)), "n_upper": int(len(upper))}
    return None


def _sentinel_spike(col, min_frac=0.02, off_scale_factor=100.0):
    """Detect a repeated EXTREME value in a continuous column - the sentinel shape.

    A missing value filled with -999, or with 0 among otherwise positive values, shows up as a value
    that (a) recurs on at least min_frac of rows, (b) lies outside the range of the remaining values,
    and (c) is off-scale relative to the column's own median by more than off_scale_factor.

    The third condition is what keeps legitimately repeated extremes - a capped or quantised feature -
    from firing: a cap sits at a few times the median, not a hundred. An absolute-gap version was tried
    first and failed on a zero fill among log-normal concentrations, where the fill sits only micro-units
    below the minimum yet is plainly a sentinel.

    A sentinel in the MIDDLE of a distribution (a missing value filled with the mean) is numerically
    indistinguishable from a real value and is deliberately not targeted.
    """
    x = np.asarray(col, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 50:
        return None
    vals, counts = np.unique(x, return_counts=True)
    span_all = float(vals.max() - vals.min())
    for v, c in zip(vals, counts):
        frac = c / len(x)
        if frac < min_frac:
            continue
        rest = x[x != v]
        if len(rest) < 20:
            continue
        r_min, r_max = float(rest.min()), float(rest.max())
        if r_max <= r_min:
            continue
        if r_min < v < r_max:
            continue                      # inside the rest: not an extreme
        # Off-scale test relative to the column's own magnitude. An absolute gap fails here: a zero
        # fill among log-normal concentrations sits only micro-units below the minimum yet is plainly
        # a sentinel, while a legitimately capped feature sits on the same scale as its own median.
        med = float(np.median(np.abs(rest)))
        if med <= 0:
            continue
        ratio = abs(v) / med
        if ratio > off_scale_factor or ratio < 1.0 / off_scale_factor:
            return {"value": float(v), "frac": float(frac), "ratio_to_median": float(ratio)}
    return None


def audit_features(X_tr, X_ev, names=None, tol=1e-12, ratio_threshold=0.05,
                   dominant_threshold=0.95, dominant_train_below=0.80):
    """Per-column audit on the evaluation set.

    Beyond exact degeneracy (constant, unseen codes) this also flags NEAR degeneracy: a column whose
    evaluation dispersion is a small fraction of its training dispersion, or whose evaluation values
    are dominated by a single level that was not dominant in training. A linear model can barely use
    such a column even though it is not exactly constant.
    """
    X_tr = np.asarray(X_tr); X_ev = np.asarray(X_ev)
    if names is None:
        names = ["f%d" % i for i in range(X_ev.shape[1])]
    rows = []
    for j, nm in enumerate(names):
        col_ev = X_ev[:, j]
        col_tr = X_tr[:, j]
        sd = float(np.std(col_ev))
        sd_tr = float(np.std(col_tr))
        const = sd < tol
        ratio = (sd / sd_tr) if sd_tr > tol else None
        dom_ev = _dominant_frac(col_ev)
        dom_tr = _dominant_frac(col_tr)
        # integer-like columns: what fraction of evaluation values never appeared in training?
        unseen_frac = None
        tr_vals = set(np.unique(col_tr).tolist())
        # R158: report unseen codes only for genuine multi-level CODE columns. In a binary indicator
        # column the value 0 never appears in the training rows of a level that is always present, so
        # any level absent from the evaluation sample reports "unseen" - which is sampling, not a
        # defect. Masked placeholders are caught by the CONSTANT_ON_EVAL non-zero test instead.
        is_indicator = tr_vals.issubset({0.0, 1.0})
        if (not is_indicator
                and np.allclose(col_ev, np.round(col_ev)) and np.allclose(col_tr, np.round(col_tr))):
            unseen_frac = float(np.mean([v not in tr_vals for v in col_ev]))
        flags = []
        notes = []
        if const:
            # R158: distinguish an absent level from a masked one. A one-hot column that is all zero
            # on evaluation simply means that level does not occur in these rows, which happens for
            # every drug that is held out or absent from the evaluation sample - most levels, in a
            # design with many. That is sampling, not degeneracy. The real alarm is a column that is
            # constant at a NON-ZERO value, which is a filled-in placeholder: R138's masked identity
            # block, constant at -1, was exactly that and cost two rounds to find.
            if abs(float(np.unique(col_ev)[0])) > tol:
                flags.append("CONSTANT_ON_EVAL value %.3f" % float(np.unique(col_ev)[0]))
            else:
                notes.append("ABSENT_LEVEL")
        if unseen_frac is not None and unseen_frac > 0.0:
            flags.append("UNSEEN_CODES %.3f" % unseen_frac)
        if is_indicator:
            # R158: an indicator column is exempt from the unseen-code test because a level absent
            # from the evaluation sample is normal. But a value OUTSIDE {0, 1} is not a legitimate
            # one-hot entry at all - it is a filled-in sentinel. R138's masked identity block was
            # constant at -1 on every row and was caught; a PARTIALLY masked block, with -1 on some
            # rows and 0 on others, is not constant and slipped through both earlier checks.
            # An indicator column may legitimately contain 0 and 1 even if one of them never occurs
            # in training: a drug present in evaluation and absent from training has an all-zero
            # training column and a 1 on its evaluation rows, which is not a defect. Only values
            # outside {0, 1} are illegitimate, which is what a -1 sentinel is.
            bad = [v for v in np.unique(col_ev) if v not in (0.0, 1.0)]
            if bad:
                frac = float(np.mean([v not in (0.0, 1.0) for v in col_ev]))
                flags.append("SENTINEL_OUTSIDE_VOCAB %s on %.3f of rows"
                             % (",".join("%g" % v for v in bad), frac))
        # Removed at R153. Uniform rescaling of a column is a no-op for BOTH model families used
        # here: a standardising ridge is invariant to 1e-15 (R152) and a quantile-binned gradient
        # booster is bit-for-bit invariant, delta exactly 0 (R153). So a dispersion-ratio warning
        # would be a pure false alarm. std_ratio is still REPORTED as data, but it raises nothing.
        if not const and dom_ev > dominant_threshold and dom_tr < dominant_train_below:
            flags.append("DOMINATED_ON_EVAL %.3f (train %.3f)" % (dom_ev, dom_tr))
        mix = _mixed_scale(col_ev)
        if mix is not None:
            flags.append("MIXED_SCALE gap %.1f decades" % mix["gap_decades"])
        spike = _sentinel_spike(col_ev)
        if spike is not None:
            flags.append("SENTINEL_SPIKE value %g on %.3f of rows (%.0fx the column median)"
                         % (spike["value"], spike["frac"], spike["ratio_to_median"]))
        rows.append({"name": nm, "std_eval": sd, "std_train": sd_tr, "std_ratio": ratio,
                     "dominant_eval": dom_ev, "dominant_train": dom_tr,
                     "const": bool(const), "unseen_frac": unseen_frac,
                     "flags": flags, "notes": notes})
    return rows


def audit_overlap(keys_tr, keys_ev, tol=1e-12):
    """Fraction of evaluation keys that also appear in training."""
    a = set(np.asarray(keys_tr).tolist()); b = np.asarray(keys_ev).tolist()
    ov = float(np.mean([k in a for k in b]))
    return {"overlap": ov, "flag": ov > tol}


def audit_predictions(preds, tol=1e-12):
    """Dispersion of each arm's prediction on the evaluation set."""
    out = []
    for nm, p in preds.items():
        sd = float(np.std(np.asarray(p, dtype=float)))
        out.append({"arm": nm, "std": sd, "const": bool(sd < tol),
                    "flags": ["CONSTANT_PREDICTION"] if sd < tol else []})
    return out


def run(features=None, split=None, preds=None, tol=1e-12, ratio_threshold=0.05,
        expected_uninformative=None):
    """Run the audit.

    expected_uninformative names columns that are SUPPOSED to carry no information in the evaluation
    condition. The canonical case is a held-out categorical level: a drug that is unseen by design has
    an all-zero identity column on evaluation, which is what "unseen" means. Without this, every
    substitution experiment trips the feature check and real alarms drown in expected ones.

    Suppression applies only to FEATURE-level flags on the named columns. Split-level and
    prediction-level alarms are never suppressed, because neither can be intentional.
    """
    rep = {"features": None, "split": None, "predictions": None, "flags": [],
           "suppressed": [], "passed": True}
    whitelist = set(expected_uninformative or [])
    if features is not None:
        X_tr, X_ev, names = features
        rep["features"] = audit_features(X_tr, X_ev, names, tol, ratio_threshold)
        for r in rep["features"]:
            if r["flags"]:
                msg = "feature %s: %s" % (r["name"], "; ".join(r["flags"]))
                if r["name"] in whitelist:
                    rep["suppressed"].append(msg)
                else:
                    rep["flags"].append(msg)
    if split is not None:
        rep["split"] = audit_overlap(split[0], split[1], tol)
        if rep["split"]["flag"]:
            rep["flags"].append("split: evaluation keys overlap training (%.3f)" % rep["split"]["overlap"])
    if preds is not None:
        rep["predictions"] = audit_predictions(preds, tol)
        for r in rep["predictions"]:
            if r["flags"]:
                rep["flags"].append("arm %s: %s" % (r["arm"], "; ".join(r["flags"])))
    rep["passed"] = len(rep["flags"]) == 0
    return rep


def show(label, rep):
    status = "PASS" if rep["passed"] else "FLAG"
    print("[%-9s] %-20s %s" % (status, label, "" if rep["passed"] else " | ".join(rep["flags"])[:160]))
    return rep["passed"]
