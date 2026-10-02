"""Frozen, plate-matched GDSC phenotype study; no STATE or causal-mechanism claim.

prepare reads metadata only for decisions; develop never evaluates confirmation
outcomes; confirm requires frozen fitted models/predictions and creates a new run.
The R data originate from the official gdscIC50 repository, not a fitted benchmark.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pickle
import platform
import time

import numpy as np
import pandas as pd
from scipy.stats import t
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


VERSION = "gdsc-phenotype-v1"
MENU = [(1032, "Afatinib", 2.0), (1036, "PLX-4720", 10.0), (1060, "PD0325901", .25)]
ACTION_IDS = [f"gdsc:{i}:{c:g}uM" for i, _, c in MENU]
ENDPOINT = "1 - (CellTiter-Glo intensity - mean blank)/(mean DMSO - mean blank)"
SEED = 20261002
CATS = ["tissue", "growth", "medium"]
SPECS = [("ridge", a) for a in (1., 10., 100.)] + [("forest", d) for d in (3, 6)]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def stamp():
    return datetime.now(timezone.utc).isoformat()


def manifest(out):
    save(out / "manifest.json", {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "manifest.json"})


def verify_manifest(out):
    for name, digest in json.loads((out / "manifest.json").read_text()).items():
        if sha(out / name) != digest:
            raise ValueError(f"Frozen artifact changed: {out / name}")


def read_raw(path):
    import pyreadr
    x = pyreadr.read_r(str(path))["gdsc_example"]
    x.insert(0, "source_row", np.arange(len(x)))
    for c in ["MASTER_CELL_ID", "CELL_ID", "SCAN_ID", "DRUGSET_ID"]:
        x[c] = x[c].astype(int)
    x["BARCODE"] = x.BARCODE.astype(str)
    return x


def metadata(raw, annotations, passports):
    """No response, control intensity, ID or date is used as a model feature."""
    cols = ["BARCODE", "SCAN_ID", "DATE_CREATED", "SCAN_DATE", "CELL_ID", "MASTER_CELL_ID",
            "COSMIC_ID", "CELL_LINE_NAME", "SEEDING_DENSITY", "DRUGSET_ID", "ASSAY", "DURATION"]
    m = raw.loc[raw.DRUGSET_ID == 159, cols].drop_duplicates().copy()
    if m.BARCODE.duplicated().any() or not (m.ASSAY == "Glo").all() or not (m.DURATION == 4).all():
        raise ValueError("Conflicting plate identity or changed assay/duration")
    a = pd.read_excel(annotations).dropna(subset=["COSMIC identifier"])
    a = a.rename(columns={"GDSC\nTissue descriptor 1": "tissue", "Growth Properties": "growth", "Screen Medium": "medium"})
    m = m.merge(a[["COSMIC identifier"] + CATS], left_on="COSMIC_ID", right_on="COSMIC identifier", how="left", validate="many_to_one")
    p = pd.read_csv(passports)
    p["COSMIC_ID"] = pd.to_numeric(p.COSMIC_ID, errors="coerce")
    p = p.dropna(subset=["COSMIC_ID"])
    if p.COSMIC_ID.duplicated().any():
        raise ValueError("Ambiguous passport COSMIC identity; do not guess")
    m = m.merge(p[["COSMIC_ID", "model_id", "patient_id", "parent_id"]], on="COSMIC_ID", how="left", validate="many_to_one")
    # Union patients of explicitly linked parent/derived models, including parents
    # outside this panel. Patient is an inference cluster, never an input feature.
    full = pd.read_csv(passports)
    parent = {str(v): str(v) for v in full.patient_id.dropna().unique()}
    def root(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v
    model_patient = full.set_index("model_id").patient_id.to_dict()
    for row in full.dropna(subset=["patient_id", "parent_id"]).itertuples():
        other = model_patient.get(row.parent_id)
        if isinstance(other, str):
            one, two = root(row.patient_id), root(other)
            parent[max(one, two)] = min(one, two)
    m["unit"] = m.patient_id.map(lambda x: root(x) if isinstance(x, str) else None)
    m["identity_qualified"] = m.unit.notna()
    m["log2_density"] = np.log2(m.SEEDING_DENSITY)
    if not np.isfinite(m.log2_density).all() or not (m.SCAN_DATE > m.DATE_CREATED).all():
        raise ValueError("Invalid seeding input or plate chronology")
    m[CATS] = m[CATS].fillna("unknown")
    m["date_cluster"] = m.DATE_CREATED.dt.strftime("%Y-%m-%d")
    return m.sort_values(["DATE_CREATED", "BARCODE"]).reset_index(drop=True)


def assign_split(m):
    dates = sorted(m.DATE_CREATED.unique())
    cutoff = dates[int(.7 * len(dates))]
    seen = set(m.loc[(m.DATE_CREATED < cutoff) & m.identity_qualified, "unit"])
    result = m.copy()
    result["split"] = "excluded_unknown_identity"
    result.loc[m.identity_qualified & (m.DATE_CREATED < cutoff), "split"] = "development"
    result.loc[m.identity_qualified & (m.DATE_CREATED >= cutoff), "split"] = "excluded_seen_patient_late"
    result.loc[m.identity_qualified & (m.DATE_CREATED >= cutoff) & ~m.unit.isin(seen), "split"] = "confirmation"
    return result, str(cutoff)


def prepare(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    raw = read_raw(args.raw)
    m, cutoff = assign_split(metadata(raw, args.annotations, args.passports))
    m.to_csv(out / "split.csv", index=False)
    drugs = pd.read_csv(args.compounds).set_index("DRUG_ID")
    for i, name, _ in MENU:
        if drugs.loc[i, "DRUG_NAME"] != name:
            raise ValueError("Drug identity changed")
    counts = {}
    for label, rows in m.groupby("split"):
        counts[label] = {"plates": len(rows), "cell_lines": rows.MASTER_CELL_ID.nunique(),
                         "patient_clusters": rows.unit.nunique(), "date_clusters": rows.date_cluster.nunique()}
    counts = {k: {a: int(b) for a, b in v.items()} for k, v in counts.items()}
    protocol = {
        "version": VERSION, "frozen_at_utc": stamp(), "base_commit": "84da7242db5c5b0833e0cc45d291a527cd9a1e4b",
        "sources": {key: {"path": str(getattr(args, key).resolve()), "sha256": sha(getattr(args, key))}
                    for key in ("raw", "annotations", "passports", "compounds")},
        "raw_upstream_commit": "34d842254a33bd04f318449969ff9976237c9295",
        "raw_url": "https://github.com/CancerRxGene/gdscIC50/blob/34d842254a33bd04f318449969ff9976237c9295/data/gdsc_example.rda",
        "decision_unit": "one assay plate; equal weight to patient/parent-connected cluster",
        "target": "published GDSC example DRUGSET_ID 159; new patient clusters on later dates",
        "estimand": "associative expected measured normalized ATP inhibition under published fixed layout; causal action value requires no position/action artifact and transport assumptions",
        "task": "retrospective intervention prioritization at exact screening concentrations; one reveal per plate",
        "menu": [dict(id=a, drug_id=i, name=n, concentration_uM=c) for a, (i, n, c) in zip(ACTION_IDS, MENU)],
        "menu_rationale": "EGFR/ERBB2, BRAF and MEK pathway interventions in a public common-plate design; maximum tested concentrations chosen before outcomes, no toxicity/dose penalty",
        "endpoint": ENDPOINT, "normalization": "per-plate NC-1 and B means; no clipping, no outcome filtering or imputation",
        "time": {"recorded_DURATION_days": 4, "nominal_drug_exposure_hours": 72, "nominal_preincubation_hours": 24,
                 "actual_treatment_timestamp": None, "binding": "recorded 4-day assay protocol; 72h drug exposure from GDSC2 protocol, not individual timestamp proof"},
        "background": CATS, "added_input": "log2 registered cells seeded per well; protocol context, NOT measured molecular state",
        "forbidden_features": ["CELL_LINE_NAME", "MASTER_CELL_ID", "CELL_ID", "patient_id", "BARCODE", "SCAN_ID", "date_cluster", "INTENSITY", "NC-1", "B", "future outcomes"],
        "metadata_timing": "tissue/growth/medium treated as static background; contemporary annotations are retrospective, not a historical availability audit",
        "cheap_state_RNA_arms": "not run; no measured marker or RNA input authenticated; no zero-padding into STATE",
        "cutoff": cutoff, "split_rule": "first 70% distinct seed dates develop; later dates confirm only unseen patient/parent clusters; unresolved patient IDs excluded with denominator retained",
        "splits": counts, "split_sha256": sha(out / "split.csv"),
        "QC": "reject FAIL well positions, ambiguous/double-tagged action wells, nonfinite readouts, missing menu/controls, nonpositive control range; >=3 distinct control wells of each kind; preserve rejects",
        "main_utility": "U=1-normalized ATP viability; untrimmed; E[U(Y)] equals U(E[Y]) because affine with a fixed observed plate denominator",
        "delta_sensitivity": [.02, .05, .10, .20],
        "delta_basis": "2/5/10/20 percentage-point screening-effect thresholds are assumptions frozen before outcomes; no single biologically validated delta or monetary conversion",
        "budgets": {"reveal_units": 1, "model_queries": 3, "state_assays": 0, "physical_actions_this_run": 0, "money": None},
        "costs": {"historical_measurement": None, "processing": None, "waiting_money": None, "failures": None, "compute_money": None},
        "refusal": "unsupported model input => fixed development action fallback, counted; missing actual outcome => no imputation, coverage-only scope; stop after one reveal",
        "tie": "argmax in frozen menu order within 1e-12 numerical tolerance; no scientific equivalence claim",
        "models": {"background_and_density": SPECS, "selection": "5-fold patient-group CV mean squared action-contrast error, equal patient weight; refit on all development",
                   "features_density": "C plus standardized log2 seeding density; forest allows C-by-density interactions; independently fitted C baseline",
                   "interpretation": "ordinary conditional response predictors, minimal world-core baseline, no novel world-model claim or STATE equivalence"},
        "primary_comparisons": ["selected C+density minus selected C", "selected C+density minus development fixed action"],
        "CI": "paired equal-patient-weight mean; t with min(patient,date)-1 df; conservative max of patient, seed-date, and two-way cluster SE; 97.5% CI for each of two primary comparisons, no per-unit calibration guarantee",
        "A": "all three paired contrasts with Bonferroni 98.333% CIs; first-to-last different-day assay replay on development repeats only; never evaluate same-row observed maximum as headroom",
        "shuffle": "one fixed-seed density shuffle within identical tissue/growth/medium in confirmation; input corruption diagnostic, no exchangeability-based p-value; preserve singleton strata",
        "stop": "no extra seeds for deterministic predictors; do not buy state without measured value/cost; retain simple baseline unless independently measured net value justifies complexity",
        "seed": SEED, "confirmation_outcomes_opened": False,
    }
    save(out / "protocol.json", protocol)
    (out / "source_at_prepare.py.txt").write_bytes(Path(__file__).read_bytes())
    save(out / "metadata_receipt.json", {"raw_rows": len(raw), "raw_plates": int(raw.BARCODE.nunique()),
          "raw_lines": int(raw.MASTER_CELL_ID.nunique()), "selected_plates": len(m), "counts": counts,
          "upstream_FAIL_rows": int((raw.TAG == "FAIL").sum()), "complete_attempt_denominator": None})
    manifest(out)
    print(json.dumps({"freeze": str(out), "cutoff": cutoff, "splits": counts}))


def load_freeze(freeze):
    verify_manifest(freeze)
    p = json.loads((freeze / "protocol.json").read_text())
    for spec in p["sources"].values():
        if sha(spec["path"]) != spec["sha256"]:
            raise ValueError("Pinned source changed")
    m = pd.read_csv(freeze / "split.csv", dtype={"BARCODE": str})
    return p, m


def normalize_panel(raw, m):
    """Keep treatment well and shared-control provenance; never manufacture values."""
    records, audit = [], []
    for barcode, g in raw.loc[raw.BARCODE.isin(m.BARCODE)].groupby("BARCODE", sort=False):
        reasons = []
        failed_positions = set(g.loc[g.TAG == "FAIL", "POSITION"])
        good = g.loc[~g.POSITION.isin(failed_positions)]
        ctrls = [good.loc[good.TAG == tag] for tag in ("NC-1", "B")]
        if any(len(c) < 3 or c.POSITION.duplicated().any() or not np.isfinite(c.INTENSITY).all() for c in ctrls):
            reasons.append("invalid_or_missing_controls")
        nc, blank = (float(c.INTENSITY.mean()) for c in ctrls)
        if not np.isfinite([nc, blank]).all() or nc <= blank:
            reasons.append("nonpositive_control_range")
        selected = []
        for action, (drug, _, conc) in zip(ACTION_IDS, MENU):
            rows = good.loc[(good.DRUG_ID == drug) & np.isclose(good.CONC, conc, rtol=0, atol=1e-12)
                            & good.TAG.str.fullmatch(r"L\d+-D\d+-S")]
            # This pinned panel has one distinct well/action, not technical replicates.
            if len(rows) != 1:
                reasons.append(f"missing_or_ambiguous_action:{action}")
                continue
            row = rows.iloc[0]
            if len(good.loc[good.POSITION == row.POSITION]) != 1 or not np.isfinite(row.INTENSITY):
                reasons.append(f"invalid_action_well:{action}")
                continue
            selected.append((action, row))
        audit.append({"BARCODE": barcode, "eligible": not reasons, "reasons": reasons,
                      "failed_positions": sorted(map(int, failed_positions)), "controls_NC1": len(ctrls[0]), "controls_B": len(ctrls[1])})
        if reasons:
            continue
        for action, row in selected:
            records.append({"BARCODE": barcode, "action": action, "source_row": int(row.source_row),
                            "SCAN_ID": int(row.SCAN_ID), "POSITION": int(row.POSITION), "drug_id": int(row.DRUG_ID),
                            "concentration_uM": float(row.CONC), "raw_intensity": float(row.INTENSITY),
                            "mean_NC1": nc, "mean_B": blank, "control_id": f"scan:{row.SCAN_ID}:NC-1+B",
                            "control_source_rows_NC1": ";".join(map(str, ctrls[0].source_row)),
                            "control_source_rows_B": ";".join(map(str, ctrls[1].source_row)),
                            "utility": 1. - (float(row.INTENSITY) - blank) / (nc - blank)})
    observations = pd.DataFrame(records)
    if observations.empty:
        raise ValueError("No qualified measured panel")
    wide = observations.pivot(index="BARCODE", columns="action", values="utility").reindex(columns=ACTION_IDS)
    panel = m.merge(wide, on="BARCODE", how="inner", validate="one_to_one")
    if not np.isfinite(panel[ACTION_IDS].to_numpy()).all():
        raise ValueError("Missing/nonfinite utility must not be imputed")
    return panel, observations, audit


def weights(frame):
    return (1. / frame.groupby("unit").unit.transform("size")).to_numpy()


def choose(q):
    q = np.asarray(q, dtype=float)
    if q.ndim != 2 or q.shape[1] != len(MENU) or not np.isfinite(q).all():
        raise ValueError("Complete finite menu predictions required")
    return np.argmax(q >= (q.max(axis=1)[:, None] - 1e-12), axis=1)


def contrast_mse(y, q, w):
    error = (y - y.mean(axis=1)[:, None]) - (q - q.mean(axis=1)[:, None])
    return float(np.average(np.mean([(error[:, a] - error[:, b]) ** 2 for a in range(3) for b in range(a + 1, 3)], axis=0), weights=w))


def predictor(spec, density):
    transforms = [("background", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATS)]
    if density:
        transforms.append(("density", StandardScaler(), ["log2_density"]))
    model = Ridge(alpha=spec[1]) if spec[0] == "ridge" else RandomForestRegressor(
        n_estimators=64, max_depth=int(spec[1]), min_samples_leaf=10, random_state=SEED, n_jobs=1)
    return Pipeline([("features", ColumnTransformer(transforms)), ("model", model)])


def fit_candidates(panel, density):
    y = panel[ACTION_IDS].to_numpy()
    folds = list(GroupKFold(5).split(panel, groups=panel.unit))
    metrics, fitted = [], []
    for spec in SPECS:
        q = np.empty_like(y)
        start = time.perf_counter()
        for tr, val in folds:
            model = predictor(spec, density)
            model.fit(panel.iloc[tr], y[tr], model__sample_weight=weights(panel.iloc[tr]))
            q[val] = model.predict(panel.iloc[val])
        model = predictor(spec, density).fit(panel, y, model__sample_weight=weights(panel))
        metrics.append({"spec": spec, "density": density, "cv_contrast_mse": contrast_mse(y, q, weights(panel)),
                        "cv_value": float(np.average(y[np.arange(len(y)), choose(q)], weights=weights(panel))),
                        "elapsed_seconds": time.perf_counter() - start})
        fitted.append(model)
    best = min(range(len(metrics)), key=lambda k: metrics[k]["cv_contrast_mse"])
    return fitted[best], metrics, best


def mean_interval(frame, values, alpha=.05):
    """Approximate crossed-cluster mean CI; honest about its sampling assumptions."""
    values = np.asarray(values, dtype=float)
    w = weights(frame); w = w / w.sum()
    avg = float(w @ values)
    score = pd.Series(w * (values - avg), index=frame.index)
    def variance(keys):
        sums = score.groupby([frame[k] for k in keys]).sum()
        g = len(sums)
        return float(g / (g - 1) * (sums ** 2).sum()) if g > 1 else None
    vunit, vdate, vboth = variance(["unit"]), variance(["date_cluster"]), variance(["unit", "date_cluster"])
    if vunit is None or vdate is None:
        return {"mean": avg, "ci": None, "reason": "fewer_than_two_clusters"}
    twoway = max(0., vunit + vdate - vboth)
    se = float(np.sqrt(max(vunit, vdate, twoway)))
    df = min(frame.unit.nunique(), frame.date_cluster.nunique()) - 1
    half = float(t.ppf(1 - alpha / 2, df) * se)
    return {"mean": avg, "ci": [avg - half, avg + half], "level": 1-alpha, "se": se, "df": int(df),
            "patient_clusters": int(frame.unit.nunique()), "date_clusters": int(frame.date_cluster.nunique()),
            "variance_patient": vunit, "variance_date": vdate, "variance_two_way": twoway,
            "scope": "approximate sampling CI conditional on fixed policies and published QC; not causal/physical calibration"}


def support(model, panel, train, density, fixed):
    q = model.predict(panel)
    allowed = panel.tissue.isin(set(train.tissue)).to_numpy()
    if density:
        allowed &= panel.log2_density.between(train.log2_density.min(), train.log2_density.max()).to_numpy()
    picked = choose(q)
    picked[~allowed] = fixed
    return q, picked, allowed


def develop(args):
    start = time.perf_counter()
    p, m = load_freeze(args.freeze)
    args.out.mkdir(parents=True, exist_ok=False)
    raw = read_raw(p["sources"]["raw"]["path"])
    dev, observations, qc = normalize_panel(raw, m.loc[m.split == "development"].copy())
    observations.to_csv(args.out / "development_observations.csv", index=False)
    dev.to_csv(args.out / "development_panel.csv", index=False)
    save(args.out / "development_QC.json", qc)
    fixed = int(np.argmax(np.average(dev[ACTION_IDS], axis=0, weights=weights(dev))))
    model_c, cv_c, bc = fit_candidates(dev, False)
    model_s, cv_s, bs = fit_candidates(dev, True)
    # Persist only fitted objects built locally, never load external pickle files.
    with (args.out / "models.pkl").open("wb") as f:
        pickle.dump({"C": model_c, "CS": model_s}, f)
    confirm_meta = m.loc[m.split == "confirmation"].copy().reset_index(drop=True)
    preds = confirm_meta[["BARCODE", "unit", "date_cluster"]].copy()
    for label, model, density in (("C", model_c, False), ("CS", model_s, True)):
        q, picked, allowed = support(model, confirm_meta, dev, density, fixed)
        for i, action in enumerate(ACTION_IDS):
            preds[f"{label}_q{i}"] = q[:, i]
        preds[label+"_action"] = picked
        preds[label+"_supported"] = allowed
    shuffled = confirm_meta.copy()
    rng = np.random.default_rng(SEED)
    for _, ids in shuffled.groupby(CATS).groups.items():
        ids = list(ids)
        shuffled.loc[ids, "log2_density"] = rng.permutation(shuffled.loc[ids, "log2_density"].to_numpy())
    q, picked, allowed = support(model_s, shuffled, dev, True, fixed)
    for i in range(3):
        preds[f"shuffle_q{i}"] = q[:, i]
    preds["shuffle_action"], preds["shuffle_supported"] = picked, allowed
    preds["fixed_action"] = fixed
    preds.to_csv(args.out / "sealed_confirmation_predictions.csv", index=False)
    contrasts = {f"{ACTION_IDS[a]} minus {ACTION_IDS[b]}": mean_interval(dev, dev[ACTION_IDS[a]] - dev[ACTION_IDS[b]], alpha=.05/3)
                 for a in range(3) for b in range(a+1, 3)}
    repeated = []
    for line, g in dev.groupby("MASTER_CELL_ID"):
        g = g.sort_values(["DATE_CREATED", "BARCODE"])
        if g.date_cluster.nunique() < 2:
            continue
        first, last = g.iloc[0], g.iloc[-1]
        selected = int(choose(first[ACTION_IDS].to_numpy(dtype=float)[None, :])[0])
        repeated.append({"MASTER_CELL_ID": int(line), "unit": last.unit, "date_cluster": last.date_cluster,
                         "first_barcode": first.BARCODE, "last_barcode": last.BARCODE, "selected": selected,
                         "same_expansion": bool(first.CELL_ID == last.CELL_ID),
                         "gain": float(last[ACTION_IDS[selected]] - last[ACTION_IDS[fixed]]),
                         **{f"first_delta{a}{b}": float(first[ACTION_IDS[a]]-first[ACTION_IDS[b]]) for a in range(3) for b in range(a+1,3)},
                         **{f"last_delta{a}{b}": float(last[ACTION_IDS[a]]-last[ACTION_IDS[b]]) for a in range(3) for b in range(a+1,3)}})
    repeat = pd.DataFrame(repeated)
    repeat.to_csv(args.out / "development_repeat_replay.csv", index=False)
    receipt = {"frozen_at_utc": stamp(), "confirmation_outcomes_opened": False, "fixed_action": fixed,
               "fixed_action_id": ACTION_IDS[fixed], "CV_C": cv_c, "CV_CS": cv_s,
               "best_C": cv_c[bc]["spec"], "best_CS": cv_s[bs]["spec"], "development_contrasts": contrasts,
               "repeat_replay": {"lines": len(repeat), "gain": mean_interval(repeat, repeat.gain) if len(repeat) > 1 else None,
                   "scope": "development diagnostic; first assay chooses, different-day last assay evaluates; not same-row oracle, cultures not necessarily independent",
                   "same_expansion": int(repeat.same_expansion.sum()) if len(repeat) else 0},
               "shuffle_changed_inputs": int((confirm_meta.log2_density != shuffled.log2_density).sum()),
               "elapsed_seconds": time.perf_counter()-start, "python": platform.python_version(),
               "freeze_manifest_sha256": sha(args.freeze / "manifest.json"), "execution_source_sha256": sha(__file__)}
    save(args.out / "development.json", receipt)
    (args.out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    manifest(args.out)
    print(json.dumps({k: receipt[k] for k in ("fixed_action_id", "best_C", "best_CS", "repeat_replay", "elapsed_seconds")}))


def confirm(args):
    start = time.perf_counter()
    p, m = load_freeze(args.freeze)
    verify_manifest(args.development)
    args.out.mkdir(parents=True, exist_ok=False)
    d = json.loads((args.development / "development.json").read_text())
    if d["freeze_manifest_sha256"] != sha(args.freeze / "manifest.json"):
        raise ValueError("Development/confirmation freeze mismatch")
    save(args.out / "opening.json", {"opened_at_utc": stamp(), "development_manifest_sha256": sha(args.development / "manifest.json"),
                                     "script_sha256": sha(__file__), "protocol_sha256": sha(args.freeze / "protocol.json")})
    # The only source of confirmation outcomes is the raw measurement table.
    raw = read_raw(p["sources"]["raw"]["path"])
    panel, observations, qc = normalize_panel(raw, m.loc[m.split == "confirmation"].copy())
    preds = pd.read_csv(args.development / "sealed_confirmation_predictions.csv", dtype={"BARCODE": str})
    rows = panel.merge(preds, on=["BARCODE", "unit", "date_cluster"], validate="one_to_one")
    if len(rows) != len(panel):
        raise ValueError("Missing pre-outcome prediction")
    y = rows[ACTION_IDS].to_numpy()
    metrics = {}
    for arm in ("fixed", "C", "CS", "shuffle"):
        picked = rows[f"{arm}_action"].to_numpy(dtype=int)
        actual = y[np.arange(len(rows)), picked]
        rows[f"{arm}_observed_utility"] = actual
        metrics[arm] = {"value": mean_interval(rows, actual), "action_counts": {ACTION_IDS[int(k)]: int(v) for k,v in pd.Series(picked).value_counts().items()},
                        "fallbacks": int((~rows[f"{arm}_supported"]).sum()) if arm != "fixed" else 0}
        if arm != "fixed":
            q = rows[[f"{arm}_q{i}" for i in range(3)]].to_numpy()
            metrics[arm]["contrast_RMSE"] = float(np.sqrt(contrast_mse(y, q, weights(rows))))
            metrics[arm]["selected_RMSE"] = float(np.sqrt(np.average((q[np.arange(len(rows)),picked]-actual)**2, weights=weights(rows))))
    comparisons = {}
    for a, b in (("CS", "C"), ("CS", "fixed"), ("C", "fixed"), ("CS", "shuffle")):
        delta = rows[f"{a}_observed_utility"]-rows[f"{b}_observed_utility"]
        ci = mean_interval(rows, delta, alpha=.025 if a == "CS" and b in ("C", "fixed") else .05)
        ci["concrete_switches"] = int((rows[f"{a}_action"] != rows[f"{b}_action"]).sum())
        ci["thresholds"] = {str(v): ("above" if ci["ci"][0] > v else "below" if ci["ci"][1] < v else "inconclusive") for v in p["delta_sensitivity"]}
        ci["observed_loss_gt_delta"] = {str(v): int((delta < -v).sum()) for v in p["delta_sensitivity"]}
        comparisons[a+"-"+b] = ci
    contrasts = {f"{ACTION_IDS[a]} minus {ACTION_IDS[b]}": mean_interval(rows, y[:,a]-y[:,b], alpha=.05/3)
                 for a in range(3) for b in range(a+1,3)}
    observations.to_csv(args.out / "confirmation_observations.csv", index=False)
    rows.to_csv(args.out / "policy_evaluation.csv", index=False)
    save(args.out / "confirmation_QC.json", qc)
    summary = {"version": VERSION, "execution": "public measured-data analysis and offline reveal replay; zero new physical experiments",
               "plate_attempts_in_release": len(qc), "qualified_plates": len(rows), "excluded_QC": sum(not r["eligible"] for r in qc),
               "cell_lines": int(rows.MASTER_CELL_ID.nunique()), "patient_clusters": int(rows.unit.nunique()), "date_clusters": int(rows.date_cluster.nunique()),
               "full_attempt_denominator": None, "metrics": metrics, "comparisons": comparisons, "action_contrasts": contrasts,
               "money_costs": None, "elapsed_seconds": time.perf_counter()-start,
               "limits": ["published fixed-position layout, randomization unverified", "no prospective molecular state or RNA reference",
                          "time-zero counts and growth-rate-normalized killing unmeasured", "generalization limited to later held-out patient clusters in this release",
                          "selected-action physical calibration and net monetary value unknown", "95% ancillary CIs descriptive; primary pair family uses 97.5% CIs"]}
    save(args.out / "summary.json", summary)
    (args.out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    manifest(args.out)
    print(json.dumps({k: summary[k] for k in ("qualified_plates", "patient_clusters", "date_clusters", "comparisons")}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    for name in ("raw", "annotations", "passports", "compounds", "out"):
        p.add_argument("--"+name, type=Path, required=True)
    p.set_defaults(run=prepare)
    p = sub.add_parser("develop")
    for name in ("freeze", "out"):
        p.add_argument("--"+name, type=Path, required=True)
    p.set_defaults(run=develop)
    p = sub.add_parser("confirm")
    for name in ("freeze", "development", "out"):
        p.add_argument("--"+name, type=Path, required=True)
    p.set_defaults(run=confirm)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
