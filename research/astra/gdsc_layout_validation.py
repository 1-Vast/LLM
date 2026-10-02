"""Frozen two-action transport diagnostic in later, different GDSC layouts.

This is not confirmation of the original three-action policy, cheap state or STATE.
One previously selected Ridge is reconstructed from development rows, never pickle.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from research.astra.gdsc_transport import digest, save


PAIR = ["gdsc:1036:10uM", "gdsc:1060:0.25uM"]
ALL = ["gdsc:1032:2uM", *PAIR]
CATS = ["tissue", "growth", "medium"]


def choose_pair(predictions):
    predictions = np.asarray(predictions, dtype=float)
    if predictions.ndim != 2 or predictions.shape[1] != 2 or not np.isfinite(predictions).all():
        raise ValueError("two finite action forecasts required")
    return np.argmax(predictions >= predictions.max(axis=1)[:, None] - 1e-12, axis=1)


def finish(out):
    save(out / "manifest.json", {p.name: digest(p) for p in sorted(out.iterdir())
                                 if p.is_file() and p.name != "manifest.json"})


def prepare(snapshot, metadata, source, out):
    out.mkdir(parents=True, exist_ok=False)
    astra = snapshot / "research/astra"
    for name, expected in json.loads((snapshot / "snapshot_manifest.json").read_text())["paths"].items():
        if digest(snapshot / name) != expected:
            raise ValueError("pinned snapshot changed: " + name)
    results = astra / "results"
    dev = pd.read_csv(results / "20261002_gdsc_development_v1/development_panel.csv")
    registered = json.loads((results / "20261002_gdsc_development_v1/development.json").read_text())
    if registered["best_C"] != ["ridge", 10.0]:
        raise ValueError("only the previously selected frozen C model is authorized")
    spec = importlib.util.spec_from_file_location("pinned_screen_for_transport", astra / "gdsc_screen.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Single reconstruction of the registered model; no selection or target refit.
    model = module.predictor(("ridge", 10.), False).fit(dev, dev[ALL], model__sample_weight=module.weights(dev))
    original = pd.read_csv(results / "20261002_gdsc_freeze_v1/split.csv")
    confirmation = original.loc[original.split == "confirmation"].reset_index(drop=True)
    sealed = pd.read_csv(results / "20261002_gdsc_development_v1/sealed_confirmation_predictions.csv")
    q, _, _ = module.support(model, confirmation, dev, False, 0)
    discrepancy = float(np.max(np.abs(q - sealed[["C_q0", "C_q1", "C_q2"]].to_numpy())))
    if discrepancy > 1e-12:
        raise ValueError("reconstructed model differs from sealed predictions")
    keys = ["MASTER_CELL_ID", "model_id", "unit", *CATS]
    annotation = original[keys].drop_duplicates()
    ambiguous = set(annotation.loc[annotation.MASTER_CELL_ID.duplicated(keep=False), "MASTER_CELL_ID"])
    annotation = annotation.loc[~annotation.MASTER_CELL_ID.isin(ambiguous)]
    meta = pd.read_csv(metadata)
    candidates = meta.loc[meta.DRUGSET_ID.isin([231, 284])].copy()
    roster = candidates.groupby("SCAN_ID").agg(
        actions=("action", "nunique"), rows=("action", "size"),
        identities=("MASTER_CELL_ID", "nunique"), barcodes=("BARCODE", "nunique"))
    scans = set(roster.index[(roster.actions == 2) & (roster.rows == 2) & (roster.identities == 1) & (roster.barcodes == 1)])
    candidates = candidates.merge(annotation, on="MASTER_CELL_ID", how="left", validate="many_to_one")
    checks = dict(complete_single_pair=candidates.SCAN_ID.isin(scans),
        known_annotation=candidates.unit.notna(), model_identity_match=candidates.model_id == candidates.SANGER_MODEL_ID,
        assay_match=(candidates.ASSAY == "Glo") & (candidates.DURATION == 4),
        single_agent_tag=candidates.TAG.str.fullmatch(r"[LR]\d+-D\d+-S"),
        no_development_parent=~candidates.unit.isin(set(dev.unit)), no_prior_scan=~candidates.prior_scan,
        later_assay=(pd.to_datetime(candidates.DATE_CREATED, utc=True) > pd.Timestamp("2015-10-22 23:00:00", tz="UTC"))
            & (pd.to_datetime(candidates.SCAN_DATE, utc=True) > pd.to_datetime(candidates.DATE_CREATED, utc=True)))
    for name, values in checks.items():
        candidates["check_" + name] = values.fillna(False)
    candidates["qualified"] = candidates[["check_" + k for k in checks]].all(axis=1)
    candidates["exclusion_reason"] = candidates.apply(
        lambda row: ";".join(k for k in checks if not row["check_" + k]), axis=1)
    candidates.to_csv(out / "candidate_action_metadata.csv", index=False)
    selected = candidates.loc[candidates.qualified].copy()
    prediction_meta = selected.drop_duplicates("SCAN_ID").sort_values(["DATE_CREATED", "SCAN_ID"]).reset_index(drop=True)
    if prediction_meta.empty:
        raise ValueError("no new-parent paired metadata")
    fixed = int(np.argmax(np.average(dev[PAIR], axis=0, weights=module.weights(dev))))
    pair_q = model.predict(prediction_meta)[:, 1:]
    supported = prediction_meta.tissue.isin(set(dev.tissue)).to_numpy()
    action = choose_pair(pair_q)
    action[~supported] = fixed
    preds = prediction_meta[["SCAN_ID", "BARCODE", "DRUGSET_ID", "MASTER_CELL_ID", "CELL_ID", "DATE_CREATED", "SCAN_DATE", "unit", *CATS]].copy()
    preds["date_cluster"] = pd.to_datetime(preds.DATE_CREATED, utc=True).dt.strftime("%Y-%m-%d")
    preds["q_PLX"], preds["q_PD"] = pair_q.T
    preds["C2_action"], preds["supported"], preds["fixed_action"] = action, supported, fixed
    preds.to_csv(out / "sealed_predictions.csv", index=False)
    protocol = dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(), code_sha256=digest(__file__),
        raw_source=str(source.resolve()), raw_sha256=digest(source), metadata_sha256=digest(metadata),
        model_source_sha256=digest(astra / "gdsc_screen.py"),
        development_sha256=digest(results / "20261002_gdsc_development_v1/development_panel.csv"),
        original_annotation_sha256=digest(results / "20261002_gdsc_freeze_v1/split.csv"),
        task="new-parent two-action historical transport diagnostic; original three-action value untested",
        actions=PAIR, layouts=[231,284], model="registered C Ridge alpha10, reconstructed once; no target fitting",
        sealed_reconstruction_max_difference=discrepancy, new_model_reconstructions=1,
        new_hyperparameter_searches=0, target_outcomes_opened=False,
        predictions_sha256=digest(out / "sealed_predictions.csv"),
        membership_sha256=digest(out / "candidate_action_metadata.csv"),
        outcome="1 - (INTENSITY - mean B)/(mean NC-1 - mean B); no clipping",
        qc="exclude FAIL positions, require >=3 distinct finite NC-1 and B wells, positive range, one finite single-agent well per action",
        selection="original absolute 1e-12 tie tolerance; out-of-tissue-support uses development fixed pair action",
        primary="equal original parent/patient-component-weight C2 minus development-fixed pair value; report each layout",
        uncertainty="no physical confidence interval; original sample identity is not certified independent cultures",
        gates_remaining=["actual culture/decision-time availability of background", "randomized positions",
                         "complete failure denominator", "measured costs", "third action missing"],
        cost=None, state_acquisition=None, refusal="no new threshold; unsupported tissue falls back to fixed",
        stop="no target refit/threshold adjustment; failure of contrast transport does not uniquely identify position bias")
    save(out / "protocol.json", protocol)
    (out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    finish(out)
    print(json.dumps(dict(scans=len(preds), units=int(preds.unit.nunique()), dates=int(preds.date_cluster.nunique()),
                         fixed_action=PAIR[fixed], reconstruction_difference=discrepancy)))


def normalize_scan(group, assigned):
    """Normalize observed wells only; failed and ambiguous attempts stay explicit."""
    reasons = []
    failed = set(group.loc[group.TAG == "FAIL", "POSITION"])
    good = group.loc[~group.POSITION.isin(failed)]
    controls = [good.loc[good.TAG == tag] for tag in ("NC-1", "B")]
    if any(len(c) < 3 or c.POSITION.duplicated().any() or not np.isfinite(c.INTENSITY).all() for c in controls):
        reasons.append("invalid_or_missing_controls")
    nc, blank = [float(c.INTENSITY.mean()) for c in controls]
    if not np.isfinite([nc, blank]).all() or nc <= blank:
        reasons.append("nonpositive_control_range")
    observations = []
    for row in assigned.itertuples():
        target = good.loc[good.source_row == row.source_row]
        aliases = good.loc[(good.POSITION == row.POSITION) & good.DRUG_ID.notna()]
        if len(target) != 1 or len(aliases) != 1 or not np.isfinite(target.INTENSITY).all():
            reasons.append("missing_failed_ambiguous_or_nonfinite_action:" + row.action)
        else:
            native = target.iloc[0]
            if native.DRUG_ID != row.DRUG_ID or abs(native.CONC - row.CONC) > 1e-12 or native.TAG != row.TAG:
                raise ValueError("action identity differs from frozen native metadata")
            observations.append(dict(action=row.action, source_row=int(row.source_row), POSITION=int(row.POSITION),
                raw_intensity=float(native.INTENSITY), mean_NC1=nc, mean_B=blank,
                control_source_rows_NC1=";".join(map(str, controls[0].source_row)),
                control_source_rows_B=";".join(map(str, controls[1].source_row))))
    if reasons:
        return [], sorted(set(reasons))
    if sorted(r["action"] for r in observations) != sorted(PAIR):
        return [], ["incomplete_action_menu"]
    for row in observations:
        row["utility"] = 1. - (row["raw_intensity"] - blank) / (nc - blank)
    return observations, []


def evaluate(freeze, out):
    protocol = json.loads((freeze / "protocol.json").read_text())
    for name, expected in json.loads((freeze / "manifest.json").read_text()).items():
        if digest(freeze / name) != expected:
            raise ValueError("frozen artifact changed: " + name)
    source = Path(protocol["raw_source"])
    if digest(source) != protocol["raw_sha256"] or digest(__file__) != protocol["code_sha256"]:
        raise ValueError("source or analysis changed after freeze")
    out.mkdir(parents=True, exist_ok=False)
    predictions = pd.read_csv(freeze / "sealed_predictions.csv")
    assignments = pd.read_csv(freeze / "candidate_action_metadata.csv")
    assigned = assignments.loc[assignments.qualified].copy()
    scans = set(predictions.SCAN_ID)
    pieces = []
    cols = ["SCAN_ID", "POSITION", "TAG", "DRUG_ID", "CONC", "INTENSITY"]
    for chunk in pd.read_csv(source, usecols=cols, chunksize=250000):
        subset = chunk.loc[chunk.SCAN_ID.isin(scans)].copy()
        subset.insert(0, "source_row", subset.index)
        if len(subset):
            pieces.append(subset)
    raw = pd.concat(pieces, ignore_index=True)
    attempts, observations = [], []
    for scan, group in assigned.groupby("SCAN_ID", sort=True):
        native, reasons = normalize_scan(raw.loc[raw.SCAN_ID == scan], group)
        attempts.append(dict(SCAN_ID=int(scan), qc_pass=not reasons, reasons=";".join(reasons),
                             published_scan=True, complete_attempt_denominator="unknown", cost="unknown"))
        observations.extend(dict(SCAN_ID=int(scan), **row) for row in native)
    pd.DataFrame(attempts).to_csv(out / "attempt_qc.csv", index=False)
    observed = pd.DataFrame(observations)
    observed.to_csv(out / "observations.csv", index=False)
    if observed.empty:
        save(out / "summary.json", dict(status="no QC-valid panel", outcome_evaluation_run=False))
        finish(out)
        return
    wide = observed.pivot(index="SCAN_ID", columns="action", values="utility").reindex(columns=PAIR)
    panel = predictions.merge(wide, on="SCAN_ID", how="inner", validate="one_to_one")
    y = panel[PAIR].to_numpy()
    panel["C2_utility"] = y[np.arange(len(y)), panel.C2_action.to_numpy(dtype=int)]
    panel["fixed_utility"] = y[np.arange(len(y)), panel.fixed_action.to_numpy(dtype=int)]
    panel["gain"] = panel.C2_utility - panel.fixed_utility
    panel["observed_PD_minus_PLX"] = y[:,1] - y[:,0]
    panel["predicted_PD_minus_PLX"] = panel.q_PD - panel.q_PLX
    panel.to_csv(out / "policy_evaluation.csv", index=False)
    summaries = []
    for label, g in [("all", panel), *[(str(k),v) for k,v in panel.groupby("DRUGSET_ID")]]:
        w = 1. / g.groupby("unit").unit.transform("size").to_numpy()
        summaries.append(dict(layout=label, scans=len(g), units=int(g.unit.nunique()), dates=int(g.date_cluster.nunique()),
            C2_minus_fixed_pp=float(np.average(g.gain, weights=w)*100),
            C2_value=float(np.average(g.C2_utility, weights=w)), fixed_value=float(np.average(g.fixed_utility, weights=w)),
            mean_PD_minus_PLX_pp=float(np.average(g.observed_PD_minus_PLX, weights=w)*100),
            contrast_RMSE=float(np.sqrt(np.average((g.observed_PD_minus_PLX-g.predicted_PD_minus_PLX)**2,weights=w))),
            policy_counts={PAIR[int(k)]:int(v) for k,v in g.C2_action.value_counts().items()},
            action_switches=int((g.C2_action != g.fixed_action).sum()),
            utilities_outside_01=int(((g[PAIR] < 0) | (g[PAIR] > 1)).sum().sum()), physical_CI=None))
    save(out / "summary.json", dict(status="limited historical two-action transport only",
         freeze_sha256=digest(freeze / "protocol.json"), outcome_evaluation_run=True,
         assigned_scans=len(predictions), qualified_scans=len(panel), qc_failed_scans=len(predictions)-len(panel),
         comparisons=summaries, original_three_action_policy_tested=False, cheap_state_gain_tested=False,
         STATE_tested=False, physical_experiment=False, net_deployment_value=None,
         exclusions="metadata excludes development-parent overlap; published QC and later annotations remain conditional"))
    finish(out)
    print((out / "summary.json").read_text())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "evaluate"])
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.phase == "prepare":
        if not all([args.snapshot, args.metadata, args.source]):
            parser.error("prepare requires --snapshot, --metadata, --source")
        prepare(args.snapshot, args.metadata, args.source, args.out)
    else:
        if args.freeze is None:
            parser.error("evaluate requires --freeze")
        evaluate(args.freeze, args.out)
