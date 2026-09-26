"""Case study: slow-acting epigenetic writer inhibitors against "the perturbation failed" in A549.

File summary
- Path: research/dynamic_world_model/case_study.py
- Purpose: (1) check the three pre-registered biological anchors; (2) replay the closed loop for
  each DNA methyltransferase inhibitor as a held-out compound, contrast "DNA methyltransferase
  inhibition" against "HDAC inhibition": register the assay in `CaseStore`, re-extract the raw
  counts of the executed wells from the source file (kept, hashed), run quality control, import a
  `MeasurementResult`, interpret it with the repository's rules, write a `RoundRecord`, and replan;
  (3) show the explicit non-success path with a planned measurement whose wells did not survive.
- Core points:
  - The raw extraction recomputes the shift from counts and must equal the prepared shift; the
    run refuses by name if it does not.
  - Every planner is read by the same validator.
- Run: python research/dynamic_world_model/case_study.py
  - Planners replayed: the current magnitude rule, the time-aware card policy (`dyn_ref`) and the
    registered fixed time course (24 h then 72 h at 10 uM).
- Depends on: common.py, episodes.py, agent.cases, maestro.handoff, h5py
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

import common as C
import episodes as E
from state import PopulationState

sys.path.insert(0, str(C.ROOT / "research" / "biological_depth"))
from prepare import obs_column  # noqa: E402

OUT = C.OUTPUTS / "case_study"
DNMT = ("Azacitidine", "Decitabine")
PRC2 = ("Tazemetostat (EPZ-6438)", "UNC1999", "EED226")
H_DNMT, H_HDAC = "DNA methyltransferase inhibition", "HDAC inhibition"


# ------------------------------------------------------------------------------ anchors
def anchors(data: C.Data, detected: np.ndarray) -> dict:
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    at72 = {c for (line, t, _), m in data.index.items() if t == 72.0 for c in m}
    hdac = sorted(c for c in at72 if comp.klass.get(c) == H_HDAC)
    groups = {"DNMT": [c for c in DNMT if c in at72], "PRC2": [c for c in PRC2 if c in at72], "HDAC": hdac}
    ifn = [g for g in data.gene_sets["HALLMARK_INTERFERON_ALPHA_RESPONSE"]]
    symbols = list(data.genes.symbol)
    ifn_idx = [symbols.index(g) for g in ifn if g in symbols]
    rows = []
    for group, members in groups.items():
        for c in members:
            for dose in (10.0, 100.0, 1000.0, 10000.0):
                rec = {"group": group, "compound": c, "dose": dose}
                for t in (24.0, 72.0):
                    r = data.index.get(("A549", t, dose), {}).get(c)
                    ok = r is not None and C.qc_passed(data, r)
                    rec[f"agreement_{t:g}h"] = float(data.agreement[r]) if ok else None
                    rec[f"detected_{t:g}h"] = bool(detected[r]) if ok else None
                    rec[f"norm_{t:g}h"] = float(np.linalg.norm(data.shift[r])) if ok else None
                    rec[f"ifn_alpha_{t:g}h"] = float(data.shift[r][ifn_idx].mean()) if ok else None
                if rec["norm_24h"] and rec["norm_72h"]:
                    rec["norm_ratio_72_over_24"] = rec["norm_72h"] / rec["norm_24h"]
                rows.append(rec)
    frame = pd.DataFrame(rows)

    def group_mean(group, column, doses=(1000.0, 10000.0)):
        values = frame[(frame.group == group) & frame.dose.isin(doses)][column].dropna()
        return float(values.mean()) if len(values) else None

    summary = {}
    for column in ("agreement_24h", "norm_24h", "norm_ratio_72_over_24", "ifn_alpha_24h", "ifn_alpha_72h"):
        summary[column] = {g: group_mean(g, column) for g in groups}
    a1 = all(summary[c][g] is not None and summary[c][g] < summary[c]["HDAC"]
             for c in ("agreement_24h", "norm_24h") for g in ("DNMT", "PRC2"))
    a2 = all(summary["norm_ratio_72_over_24"][g] is not None
             and summary["norm_ratio_72_over_24"][g] > summary["norm_ratio_72_over_24"]["HDAC"] for g in ("DNMT", "PRC2"))
    dnmt = frame[(frame.group == "DNMT") & frame.dose.isin((1000.0, 10000.0))].dropna(subset=["ifn_alpha_24h", "ifn_alpha_72h"])
    a3_values = (dnmt.ifn_alpha_72h - dnmt.ifn_alpha_24h).tolist()
    a3 = bool(len(a3_values)) and all(v > 0 for v in a3_values)
    # post hoc, labelled: replicate agreement at 72 h (the registered anchors used the shift norm, which
    # for a weak response is dominated by sampling noise)
    summary["posthoc_agreement_72h"] = {g: group_mean(g, "agreement_72h") for g in groups}
    return {"groups": groups, "per_condition": frame.to_dict("records"), "summary_1uM_and_10uM": summary,
            "anchor_1_weaker_at_24h": a1, "anchor_2_grows_more_to_72h": a2,
            "anchor_3_dnmt_ifn_alpha_rises": a3, "anchor_3_differences": a3_values,
            "reading": "means over the 1 uM and 10 uM conditions that passed quality control; DNMT has two compounds and PRC2 three, so these are descriptions, not tests"}


# ------------------------------------------------------------------------------ raw extraction
class Source:
    def __init__(self):
        self.path = C.ROOT / "data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad"
        with h5py.File(self.path, "r") as f:
            obs = f["obs"]
            self.meta = pd.DataFrame({k: obs_column(obs, k) for k in
                                      ("cell_line", "perturbation", "dose_value", "time", "replicate", "plate", "well")})
            self.shape = tuple(int(v) for v in f["X"].attrs["shape"])
        self.meta["time"] = self.meta.time.astype(float)
        self.meta["dose_value"] = self.meta.dose_value.astype(float)
        self.meta["perturbation"] = self.meta.perturbation.astype(str).str.strip()
        manifest = json.loads((C.PREPARED / "prepare_manifest.json").read_text(encoding="utf-8"))
        self.sha256 = manifest["audit"]["source_sha256"]
        from virtual_cell.identity_markers import shift_labels
        with h5py.File(self.path, "r") as f:
            published = obs_column(f["var"], "ensembl_id").astype(str)
        labels = np.array([x if x is not None else "" for x in shift_labels(list(published), manifest["audit"]["label_offset"], self.shape[1])])
        duplicated = pd.Series(labels).duplicated(keep=False).to_numpy() & (labels != "")
        self.human = np.array([e.startswith("ENSG") for e in labels]) & ~duplicated
        column_of = {e: i for i, e in enumerate(labels) if self.human[i]}
        genes = pd.read_csv(C.FROZEN / "genes.csv")
        self.columns = np.array([column_of[e] for e in genes.ensembl])

    def rows(self, line, t, compound, dose, replicate):
        m = self.meta
        mask = (m.cell_line == line) & (m.time == t) & (m.replicate == replicate)
        mask &= (m.perturbation == "control") & (m.dose_value == 0) if compound == "control" else \
            (m.perturbation == compound) & (m.dose_value == dose)
        return np.flatnonzero(mask.to_numpy())

    def read(self, rows: np.ndarray):
        """Raw counts for the given cells, all features, as CSR pieces."""
        data, indices, indptr = [], [], [0]
        with h5py.File(self.path, "r") as f:
            X = f["X"]
            ptr = X["indptr"]
            for r in rows:
                a, b = int(ptr[r]), int(ptr[r + 1])
                data.append(X["data"][a:b]); indices.append(X["indices"][a:b]); indptr.append(indptr[-1] + (b - a))
        return (np.concatenate(data) if data else np.zeros(0), np.concatenate(indices) if indices else np.zeros(0, int),
                np.array(indptr))

    def pseudobulk(self, data, indices, indptr) -> np.ndarray:
        n = len(indptr) - 1
        out = np.zeros(len(self.columns))
        position = np.full(self.shape[1], -1)
        position[self.columns] = np.arange(len(self.columns))
        for i in range(n):
            d = data[indptr[i]:indptr[i + 1]].astype(np.float64)
            j = indices[indptr[i]:indptr[i + 1]]
            keep = self.human[j]
            library = d[keep].sum()
            values = np.log1p(d[keep] * 1e4 / max(library, 1.0))
            pos = position[j[keep]]
            sel = pos >= 0
            np.add.at(out, pos[sel], values[sel])
        return out / max(n, 1)


def execute_assay(source: Source, data: C.Data, assay_id: str, compound: str, key, raw_dir: Path) -> dict:
    """Run one registered assay against the release: extract, keep, QC, and compute the shift."""
    line, t, dose = key
    log = {"assay_id": assay_id, "compound": compound, "line": line, "time_hours": t, "dose_nM": dose,
           "source": str(source.path.relative_to(C.ROOT)), "source_sha256": source.sha256, "replicates": {}}
    shifts, qc_reasons = {}, []
    arrays = {}
    for rep in ("rep1", "rep2"):
        treated = source.rows(line, t, compound, dose, rep)
        vehicle = source.rows(line, t, "control", 0.0, rep)
        log["replicates"][rep] = {"treated_cells": int(len(treated)), "vehicle_cells": int(len(vehicle)),
                                  "wells": sorted(set(source.meta.well.iloc[treated])),
                                  "plates": sorted(set(source.meta.plate.iloc[treated]))}
        if len(treated) < 20:
            qc_reasons.append(f"{rep}:below_minimum_cells:{len(treated)}")
            continue
        td, ti, tp = source.read(treated)
        vd, vi, vp = source.read(vehicle)
        arrays.update({f"{rep}_treated_rows": treated, f"{rep}_treated_data": td, f"{rep}_treated_indices": ti,
                       f"{rep}_treated_indptr": tp, f"{rep}_vehicle_rows": vehicle, f"{rep}_vehicle_data": vd,
                       f"{rep}_vehicle_indices": vi, f"{rep}_vehicle_indptr": vp})
        shifts[rep] = source.pseudobulk(td, ti, tp) - source.pseudobulk(vd, vi, vp)
    raw_path = raw_dir / f"{assay_id.replace('|', '_')}__{compound.split(' ')[0]}.npz"
    np.savez_compressed(raw_path, **arrays) if arrays else raw_path.write_bytes(b"")
    log["raw_output"] = {"path": str(raw_path.relative_to(C.ROOT)), "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest()}
    qc = not qc_reasons
    log["quality"] = {"passed": qc, "reasons": qc_reasons, "rule": "both replicate wells with at least 20 cells and matched vehicle"}
    if qc:
        mean = 0.5 * (shifts["rep1"] + shifts["rep2"])
        row = data.index[key][compound]
        difference = float(np.max(np.abs(mean - data.shift[row])))
        log["reproduces_prepared_shift_max_abs_difference"] = difference
        if difference > 1e-3:
            raise SystemExit(f"raw_extraction_disagrees_with_prepared_shift:{difference}")
        log["replicate_agreement"] = C._pearson(shifts["rep1"], shifts["rep2"])
        return {"qc": True, "mean": mean, "agreement": log["replicate_agreement"], "log": log}
    return {"qc": False, "log": log}


# ------------------------------------------------------------------------------ closed loop
def closed_loop(data, detected, null, protocol, source, compound, planner: str, store_path: Path, raw_dir: Path) -> dict:
    from agent.cases import CaseStore, CaseState, MeasurementResult
    from maestro.handoff import (ComparabilityStatus, DecisionLayer, EvidenceLayer, ExecutionLayer, RejectedCandidate,
                                 RoundRecord, WorldModelLayer, write_round)
    from maestro.models import DecisionStatus, EvidenceKind
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    fold = int(comp.fold[compound])
    tier = C.tiers(data, protocol)["A"]
    magnitude = E.Magnitude(data, detected)
    ctx = next(c for c, f in E.contexts(data, protocol, detected, magnitude, tier_names=("A",), folds=(fold,)))
    h1, h2 = H_DNMT, H_HDAC
    case_id = f"{planner}:{compound}"
    store = CaseStore(store_path)
    store.open_case(case_id, budget=16.0)
    menu_actions = [E.make_action(k, h1, h2) for k in tier.keys]
    contrast = E.contrast_for(h1, h2, menu_actions)
    from maestro.outcome import EvidenceState
    state = EvidenceState.open(contrast.hypotheses)
    executed, rounds = [], []
    for round_index in range(2):
        key, note = E.choose(planner, ctx, compound, h1, h2, executed, None)
        if key is None:
            store.record_plan(case_id, (), ready_to_measure=False, context_identifier=None, stop_reason=note.get("reason"))
            rounds.append({"round": round_index, "deferred": note.get("reason")})
            break
        action = next(a for a in menu_actions if a.identifier == C.action_id(key))
        snapshot = store.record_plan(case_id, (action,), ready_to_measure=True, context_identifier=key[0])
        card = E.card_for(ctx, key, h1, h2)
        assay = execute_assay(source, data, action.identifier, compound, key, raw_dir)
        if assay["qc"]:
            reading = C.read_profile(ctx.ft, key, assay["mean"], assay["agreement"] >= null[f"{key[0]}|{key[1]:g}"]["threshold"],
                                     h1, h2, ctx.params)
        else:
            reading = {"outcome": "quality_failed"}
        before = set(state.candidates)
        state, interpretation, outcome = C.evidence_update(state, contrast, action, key, reading, h1, h2, qc=assay["qc"],
                                                           agreement=assay.get("agreement", float("nan")),
                                                           source=f"sciplex3:{assay['log']['raw_output']['sha256'][:16]}")
        result = MeasurementResult(
            action_identifier=action.identifier, statement=f"sci-RNA-seq3 pseudobulk shift {action.identifier}",
            source_id=f"sciplex3:{assay['log']['raw_output']['sha256']}", context_identifier=key[0], time_hours=key[1],
            independent_units=2 if assay["qc"] else None, quality_passed=assay["qc"], conditions={"dose_nM": f"{key[2]:g}"},
            metrics={"replicate_agreement": f"{assay.get('agreement', float('nan')):.4f}"},
            evidence_kind=EvidenceKind.REAL_MEASUREMENT, result_id=f"{case_id}:{action.identifier}",
            interpretation_fields=(), limitations=tuple(assay["log"]["quality"]["reasons"]))
        imported = store.import_measurement(case_id, result)
        eliminated = sorted(before - set(state.candidates))
        rejected = tuple(RejectedCandidate(C.action_id(k), "not_selected_by_" + planner)
                         for k in tier.keys if k != key and k not in [e["key"] for e in executed])
        record = RoundRecord(
            session_id=case_id, round_index=round_index,
            evidence=EvidenceLayer(records=tuple(f"{e['action']}:{e['outcome']}" for e in executed),
                                   comparability_status=ComparabilityStatus.COMPARABLE),
            world_model=(WorldModelLayer(in_distribution=True, model_id="reference_scenario_cards", mean=card["p_correct"],
                                         interval=tuple(card["epistemic_interval"]), validation_status="leave_one_out_on_training_references",
                                         readout="p_correct_elimination")
                         if card.get("served") else WorldModelLayer.no_model(card.get("reason") or "card_refused")),
            decision=DecisionLayer(chosen=(action.identifier,), rejected=rejected,
                                   rationale=f"{planner} selector; card p_correct={card.get('p_correct')}"),
            execution=ExecutionLayer(observed={"replicate_agreement": float(assay.get("agreement", 0.0)) if assay["qc"] else 0.0},
                                     belief_delta={h: -1.0 for h in eliminated}, contradiction_flag=bool(eliminated),
                                     stop_decision=("decided" if eliminated else None),
                                     result_id=imported.result_id if assay["qc"] else imported.result_id))
        digest = write_round(OUT / "rounds" / f"{case_id.replace(':', '__').replace(' ', '_')}__round{round_index}.json", record)
        observed_state = (PopulationState.from_condition(data, data.index[key][compound], action.identifier).payload()
                          if assay["qc"] else None)
        executed.append({"key": key, "action": action.identifier, "outcome": outcome, "qc": assay["qc"],
                         "agreement": assay.get("agreement", float("nan")),
                         "score_h1": reading.get("score_a"), "score_h2": reading.get("score_b")})
        rounds.append({"round": round_index, "action": action.identifier, "card": {k: card.get(k) for k in ("served", "p_correct", "p_wrong", "reason")},
                       "case_state_after_import": imported.snapshot.state.value, "outcome": outcome,
                       "interpretation": {"class": interpretation.outcome_class.value, "scope": interpretation.scope.value,
                                          "rule": interpretation.rule_identifier, "boundary": interpretation.boundary},
                       "eliminated": eliminated, "round_record_sha256": digest, "execution_log": assay["log"],
                       "observed_state": observed_state})
        if eliminated:
            store.record_decision(case_id, status=DecisionStatus.DECIDED.value)
            break
        if not assay["qc"]:
            continue
    final = store.snapshot(case_id)
    remaining = sorted(state.candidates)
    return {"compound": compound, "planner": planner, "fold": fold, "hypotheses": [h1, h2], "rounds": rounds,
            "remaining": remaining, "final_case_state": final.state.value, "spent_days": final.spent,
            "decision": ("correct" if remaining == [h1] else "wrong" if remaining == [h2] else "undetermined")}


def main() -> None:
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "raw").mkdir(parents=True)
    result = {"protocol_hashes": C.frozen_hashes(), "anchors": anchors(data, detected), "loops": [], "qc_failure_demo": None}
    source = Source()
    for compound in DNMT:
        for planner in ("magnitude", "dyn_ref", "fixed"):
            result["loops"].append(closed_loop(data, detected, null, protocol, source, compound, planner,
                                               OUT / "cases.sqlite3", OUT / "raw"))
    # explicit non-success: a planned 72 h 10 uM measurement whose wells did not survive
    from agent.cases import CaseStore, MeasurementResult
    from maestro.models import EvidenceKind
    store = CaseStore(OUT / "cases.sqlite3")
    key = ("A549", 72.0, 10000.0)
    compound = "Panobinostat (LBH589)"
    action = E.make_action(key, H_HDAC, H_DNMT)
    store.open_case("qc_failure_demo", budget=16.0)
    store.record_plan("qc_failure_demo", (action,), ready_to_measure=True, context_identifier="A549")
    assay = execute_assay(source, data, action.identifier, compound, key, OUT / "raw")
    imported = store.import_measurement("qc_failure_demo", MeasurementResult(
        action_identifier=action.identifier, statement="sci-RNA-seq3 pseudobulk shift A549 72 h 10 uM",
        source_id=f"sciplex3:{assay['log']['raw_output']['sha256']}", context_identifier="A549", time_hours=72.0,
        independent_units=None, quality_passed=assay["qc"], conditions={"dose_nM": "10000"},
        evidence_kind=EvidenceKind.REAL_MEASUREMENT, result_id="qc_failure_demo:1",
        limitations=tuple(assay["log"]["quality"]["reasons"])))
    result["qc_failure_demo"] = {"compound": compound, "action": action.identifier, "execution_log": assay["log"],
                                 "case_state_after_import": imported.snapshot.state.value, "spent_days": imported.snapshot.spent}
    C.write_json(OUT / "case_study.json", C.clean(result))
    a = result["anchors"]
    print(json.dumps({k: a[k] for k in ("summary_1uM_and_10uM", "anchor_1_weaker_at_24h", "anchor_2_grows_more_to_72h",
                                         "anchor_3_dnmt_ifn_alpha_rises", "anchor_3_differences")}, indent=1, default=str))
    for loop in result["loops"]:
        print(loop["compound"], loop["planner"], loop["decision"], loop["final_case_state"],
              [(r.get("action"), r.get("outcome"), r.get("case_state_after_import")) for r in loop["rounds"]])
    print("qc demo:", result["qc_failure_demo"]["case_state_after_import"], result["qc_failure_demo"]["execution_log"]["quality"])


if __name__ == "__main__":
    main()
