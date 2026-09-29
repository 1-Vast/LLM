"""Typed observation bridges: transcriptomic response against viability, kept as separate typed observations.

File summary
- Path: research/maestro_vc_v1/bridges.py
- Purpose: link a compound's transcriptomic reading in a cell line (SciPlex3, L1000) to its fitted
  viability in the same cell line (PRISM secondary screen) without merging them into one feature
  matrix, and turn the discordant pairs into contrastive cases: a detected molecular response with no
  viability effect, and a viability effect with no detected response.
- Core points:
  - Bridge key: the InChIKey connectivity block of the compound's structure (recomputed with RDKit on both
    sides) and the cell line (A549, MCF7, PC3 and K562 map to DepMap models; a line PRISM does not hold has
    no bridge). Each side keeps its own typed status and units; the bridge table carries both and states
    the mismatch: PRISM's fitted AUC integrates a dose range and a 5-day exposure, the transcriptome is one
    24 h condition at the top dose, so the pair is not dose- or time-matched.
  - Thresholds are the case package's declared construction settings, not chosen here: active AUC at or
    below 0.60 and inactive AUC at or above 0.85 (`data/evaluation/derived/real_case_manifest_v3.json`).
    A response is `detected` by the registered detection rule already applied to the state table.
  - Discordance types: `response_without_phenotype` (detected, AUC >= 0.85) and `phenotype_without_response`
    (undetected, AUC <= 0.60). They are the design's "large transcriptomic response but no functional
    effect" and "weak transcriptomic response but strong phenotype" contrastive cases. At most `PER_TYPE`
    of each are written, in a deterministic order (strength, then compound), as `Case`s whose hypotheses
    are "functionally relevant" and "functionally irrelevant" (registered) plus an advisory artifact.
  - Nothing is inferred about mechanism; the bridge only records that two typed observations disagree and
    that the record cannot say why.
- Run: python -m research.maestro_vc_v1.bridges
- Interfaces: `build_bridge`, `discordant_cases`, `summarise`, `run`, `ACTIVE_AUC`, `INACTIVE_AUC`
- Depends on: tables.py, preprocess.py, research/scientific_case_memory, the PRISM release
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.scientific_case_memory import case_schema as S
from research.scientific_case_memory import case_store as CS

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/processed/maestro_vc_v1"
CASES = ROOT / "outputs/scientific_case_memory"
PRISM = ROOT / "data/raw/prism/secondary-screen-dose-response-curve-parameters.csv"
CELL_MODEL = {"A549": "ACH-000681", "MCF7": "ACH-000019", "PC3": "ACH-000090", "K562": "ACH-000551"}
ACTIVE_AUC, INACTIVE_AUC = 0.60, 0.85
PER_TYPE = 25
SHIFTS = {"sciplex3": "outputs/dynamic_world_model_20260926/prepared/shifts.npz",
          "l1000": "outputs/sequence_audit_20260926/l1000/prepared/shifts.npz"}
TOP_DOSE = {"sciplex3": 10000.0, "l1000": 10000.0}


def _block(smiles) -> str | None:
    from research.maestro_vc_v1.preprocess import inchikey_of

    key = inchikey_of(smiles)
    return key[:14] if key else None


def prism_table() -> pd.DataFrame:
    df = pd.read_csv(PRISM, usecols=["broad_id", "depmap_id", "screen_id", "auc", "r2", "name", "moa", "smiles"])
    df = df[df.depmap_id.isin(CELL_MODEL.values())]
    df["prio"] = (df.screen_id == "MTS010").astype(int)
    df = df.sort_values("prio")
    df["block"] = [_block(s) for s in df.smiles]
    df = df.dropna(subset=["block"]).drop_duplicates(["block", "depmap_id"], keep="last")
    inverse = {v: k for k, v in CELL_MODEL.items()}
    df["cell_line"] = df.depmap_id.map(inverse)
    return df[["block", "cell_line", "auc", "r2", "name", "moa", "screen_id", "broad_id"]]


def transcript_table(dataset: str) -> pd.DataFrame:
    state = pd.read_csv(PROCESSED / f"state_table_{dataset}.csv")
    inter = pd.read_csv(PROCESSED / f"intervention_table_{dataset}.csv")[["unit_id", "canonical_structure", "mechanism_annotation"]]
    df = state.merge(inter, on="unit_id")
    df = df[(df.time == 24.0) & (df.dose_nominal == TOP_DOSE[dataset]) &
            df.measurement_status.isin(["qualified", "undetected"])]
    shifts = np.load(ROOT / SHIFTS[dataset])["shift"]
    rows = df.state_vector_uri.str.extract(r"shift\[(\d+)\]")[0].astype(int).to_numpy()
    df = df.assign(strength=np.linalg.norm(shifts[rows], axis=1))
    df["block"] = [_block(s) for s in df.canonical_structure]
    df = df.dropna(subset=["block"])
    df["dataset"] = dataset
    return df[["dataset", "compound_id", "block", "cell_line", "strength", "detection_status", "measurement_status",
               "mechanism_annotation", "unit_id"]].drop_duplicates(["dataset", "block", "cell_line"])


def build_bridge() -> pd.DataFrame:
    prism = prism_table()
    frames = [transcript_table(d) for d in ("sciplex3", "l1000")]
    bridge = pd.concat(frames).merge(prism, on=["block", "cell_line"], how="inner", suffixes=("", "_prism"))
    bridge["discordance"] = np.where((bridge.detection_status == "detected") & (bridge.auc >= INACTIVE_AUC), "response_without_phenotype",
                                     np.where((bridge.detection_status == "undetected") & (bridge.auc <= ACTIVE_AUC),
                                              "phenotype_without_response", "concordant_or_intermediate"))
    return bridge.rename(columns={"strength": "transcript_shift_norm", "auc": "viability_auc", "r2": "viability_curve_r2",
                                  "name": "prism_name", "moa": "prism_moa"})


def summarise(bridge: pd.DataFrame) -> dict:
    out = {"pairs": int(len(bridge)), "compounds": int(bridge.block.nunique()), "by_dataset_line": [], "discordance": {}}
    for (d, c), g in bridge.groupby(["dataset", "cell_line"]):
        rho = float(g[["transcript_shift_norm", "viability_auc"]].corr(method="spearman").iloc[0, 1]) if len(g) > 4 else None
        out["by_dataset_line"].append({"dataset": d, "cell_line": c, "pairs": int(len(g)), "detected": int((g.detection_status == "detected").sum()),
                                       "spearman_strength_vs_auc": rho,
                                       "response_without_phenotype": int((g.discordance == "response_without_phenotype").sum()),
                                       "phenotype_without_response": int((g.discordance == "phenotype_without_response").sum())})
    detected = bridge[bridge.detection_status == "detected"]
    undetected = bridge[bridge.detection_status == "undetected"]
    out["discordance"] = {
        "detected_pairs": int(len(detected)), "detected_with_inactive_auc": int((detected.viability_auc >= INACTIVE_AUC).sum()),
        "detected_with_active_auc": int((detected.viability_auc <= ACTIVE_AUC).sum()),
        "undetected_pairs": int(len(undetected)), "undetected_with_active_auc": int((undetected.viability_auc <= ACTIVE_AUC).sum()),
        "undetected_with_inactive_auc": int((undetected.viability_auc >= INACTIVE_AUC).sum())}
    out["thresholds"] = {"active_auc_at_or_below": ACTIVE_AUC, "inactive_auc_at_or_above": INACTIVE_AUC,
                         "source": "data/evaluation/derived/real_case_manifest_v3.json construction_settings"}
    return out


def discordant_cases(bridge: pd.DataFrame, refs: tuple[S.RawDataRef, ...], created_at: str = "2026-09-29") -> list[S.Case]:
    cases = []
    for kind in ("response_without_phenotype", "phenotype_without_response"):
        g = bridge[bridge.discordance == kind].sort_values(["transcript_shift_norm", "prism_name"], ascending=[kind == "phenotype_without_response", True])
        for r in g.head(PER_TYPE).itertuples():
            cid = f"bridge:{r.dataset}:{r.cell_line}:{r.compound_id}"
            action = S.ActionSpec("matched_target_engagement", "Measure condition-matched engagement and functional activity of the annotated target.",
                                  "functional_measurement", 3.0, 7.0, "target_occupancy", r.cell_line, 24.0, 10000.0, (), (), None, False)
            obs = (S.Observation("transcriptome_24h_10uM", S.MeasurementStatus.QUALIFIED if r.detection_status == "detected" else S.MeasurementStatus.UNDETECTED,
                                 "transcriptome shift", r.cell_line, 24.0, 10000.0, "transcriptome_shift_norm", float(r.transcript_shift_norm)),
                   S.Observation("prism_viability_auc", S.MeasurementStatus.AMBIGUOUS, "PRISM secondary screen fitted dose response", r.cell_line,
                                 None, None, "viability_auc", float(r.viability_auc), note="not dose- or time-matched to the transcriptome"))
            relevant = "The molecular response is functionally relevant: the phenotype follows from it."
            modes = (S.FailureMode("contrast_" + kind, "detected molecular response with no viability effect" if kind == "response_without_phenotype"
                                   else "viability effect with no detected molecular response", severity="informational"),)
            cases.append(S.Case(
                case_id=cid, case_version=1, case_kind=S.CaseKind.CONTRASTIVE, problem_type=S.ProblemType.TRANSCRIPTOMIC_VIABILITY_DISCORDANCE,
                problem_statement=f"{r.compound_id} in {r.cell_line}: {modes[0].description}.", user_question="Is the molecular response the cause of the phenotype?",
                raw_data_references=refs, data_quality_report={"usable": True, "passed_fraction": 1.0},
                context_fingerprint={"dataset": r.dataset, "assay": "transcriptome+viability", "context": f"{r.dataset}:{r.cell_line}",
                                     "compound": cid, "unit": r.block, "hypothesis_class": kind, "cell_line": r.cell_line,
                                     "measurement_type": "typed_bridge", "intervention_type": "small_molecule", "is_training": True,
                                     "prism_name": r.prism_name, "prism_moa": r.prism_moa if isinstance(r.prism_moa, str) else None},
                initial_observations=obs,
                initial_hypotheses=(S.HypothesisClaim("relevant", relevant), S.HypothesisClaim("irrelevant", "The molecular response is real but functionally irrelevant."),
                                    S.HypothesisClaim("artifact", "One of the two records is an artifact of its screen.", (), {}, True)),
                candidate_actions=(action,), retrieved_knowledge=(), virtual_cell_predictions=(), predicted_outcome_branches=(),
                real_measurements=(),
                measurement_quality={}, qualified_evidence=(), hypothesis_updates=(),
                final_decision={"status": "defer", "basis": "no menu action in the retrospective records can separate the hypotheses"},
                next_action={"critical_actions": ["matched_target_engagement"], "why": "engagement and function were never measured"},
                failure_modes=modes, adaptation_map=(), calibration_history=(),
                provenance={"builder": "maestro_vc_v1.bridges", "created_at": created_at,
                            "sources": {"prism": refs[0].sha256, "state_table": "data/processed/maestro_vc_v1"},
                            "limitations": ["the transcriptome is one 24 h condition; PRISM integrates a dose range and a 5-day exposure"]}))
    return cases


def run() -> dict:
    from research.maestro_vc_v1.tables import sha256_file, write_frame, _rel

    bridge = build_bridge()
    info = write_frame(bridge, PROCESSED / "bridge_transcriptome_viability.csv")
    summary = summarise(bridge)
    refs = (S.RawDataRef("data/raw/prism/secondary-screen-dose-response-curve-parameters.csv", sha256_file(PRISM), "viability"),)
    cases = discordant_cases(bridge, refs)
    store = CS.CaseStore()
    store.append_many(cases)
    path = CASES / "cases_transcriptome_viability_discordance.jsonl.gz"
    store.write_snapshot(path)
    result = {"bridge": info, "summary": summary, "cases": len(store), "cases_path": _rel(path), "cases_sha256": sha256_file(path),
              "verify": list(store.verify())}
    (ROOT / "outputs/maestro_vc_v1/analysis/bridge.json").write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    manifest_path = ROOT / "data/manifests/maestro_vc_v1_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["bridge_transcriptome_viability"] = info
    manifest["files"]["case_transcriptome_viability_discordance"] = {"path": _rel(path), "sha256": result["cases_sha256"], "cases": len(store)}
    manifest_path.write_text(json.dumps(manifest, indent=1, default=str), encoding="utf-8")
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps(r["summary"], indent=1, default=str)[:3000])
    print("cases", r["cases"], r["verify"])
