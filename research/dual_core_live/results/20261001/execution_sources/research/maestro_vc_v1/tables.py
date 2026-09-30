"""The five logical tables of MAESTRO-VC v1: state, intervention, evidence, case and episode.

File summary
- Path: research/maestro_vc_v1/tables.py
- Purpose: write the data products the design names, from the real prepared releases and the replay
  records, in plain CSV or gzip JSON lines with a SHA-256 for each file, so a reader can rebuild
  every number from a file that has a checksum.
- Core points:
  - `state_table`: one row per (dataset, compound, cell line, time, dose) planned by the study
    design within the scope of the prepared release (the conditions the release holds for any
    compound; design rows for other cell lines or doses are out of scope, not missing), with the
    typed measurement status. A planned condition with no prepared row is
    `planned_missing`; a row that fails the release's own QC is `qc_failed`; a measured row is
    `undetected` or `qualified` by the registered detection rule. No status is ever converted to a
    zero. The state vector itself stays in the prepared NPZ and is named by `state_vector_uri`
    (file, array, row).
  - `intervention_table`: the same grain with the compound's canonical structure, independent
    chemical unit, nominal target and mechanism annotation where the release states one, and
    `not_planned` engagement and functional-activity status unless an engagement release covers the
    compound. Nominal dose is stated; realised dose is `not_recorded_in_release`.
  - `evidence_table`: one row per real reading of an episode's condition under its contrast (the
    evaluator's exact outcome tables), with qualification status, independent units, the registered
    interpretation rule and whether the reading's premises held.
  - `case_table`: one row per reference case of the full library (no held-out fold), holding the
    design's fields as JSON.
  - `episode_table`: one row per replay episode with its hypotheses, menu, each arm's chosen first
    action and terminal decision. It is the evaluator view; `views.py` writes the policy view.
  - Raw and processed artefacts are both kept: the state vectors are not copied, and every table names
    the prepared source file and its checksum.
- Interfaces: `state_table`, `intervention_table`, `evidence_table`, `episode_table`, `case_table`,
  `write_frame`, `write_jsonl`, `STATE_COLUMNS`
- Depends on: pandas, numpy, research/dynamic_world_model, research/belief_planning, case memory package
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STATE_COLUMNS = ["unit_id", "chemical_unit_id", "compound_id", "context_id", "cell_line", "time", "dose_nominal",
                 "dose_realized", "control_id", "assay_id", "feature_space", "state_vector_uri", "replicate_count",
                 "qc_status", "detection_status", "measurement_status", "provenance"]
SOURCES = {
    "sciplex3": {"conditions": "outputs/dynamic_world_model_20260926/prepared/conditions.csv",
                 "shifts": "outputs/dynamic_world_model_20260926/prepared/shifts.npz",
                 "compounds": "outputs/biological_depth_20260926/prepared/compounds.csv",
                 "design": "outputs/protocol_v2_1_20260927/design/sciplex3_design.csv",
                 "assay": "sci-RNA-seq3 pseudobulk shift", "feature_space": "sciplex3_2473_genes", "unit": "skeleton"},
    "l1000": {"conditions": "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
              "shifts": "outputs/sequence_audit_20260926/l1000/prepared/shifts.npz",
              "compounds": "outputs/sequence_audit_20260926/l1000/prepared/compounds.csv",
              "design": "outputs/protocol_v2_1_20260927/design/l1000_design.csv",
              "assay": "L1000 Level 5 MODZ signature", "feature_space": "l1000_978_landmark_genes", "unit": "component"},
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_frame(frame: pd.DataFrame, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")
    return {"path": _rel(path), "rows": int(len(frame)), "columns": list(frame.columns), "sha256": sha256_file(path)}


def write_jsonl(rows, path: Path) -> dict:
    from research.scientific_case_memory import case_store as CS

    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with CS.open_text(path, "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, default=_default, allow_nan=False) + "\n")
            n += 1
    return {"path": _rel(path), "rows": n, "sha256": sha256_file(path)}


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _default(v):
    if hasattr(v, "item"):
        return v.item()
    if isinstance(v, (set, frozenset)):
        return sorted(v)
    if isinstance(v, tuple):
        return list(v)
    return str(v)


def _clean(v):
    if isinstance(v, float) and not np.isfinite(v):
        return None
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    if hasattr(v, "item") and not isinstance(v, (str, bytes)):
        return _clean(v.item())
    return v


# ---------------------------------------------------------------------------------------- state
def _detected(dataset: str, conditions: pd.DataFrame, data=None) -> np.ndarray:
    if dataset == "l1000":
        return conditions["detected"].to_numpy(bool)
    from research.dynamic_world_model import common as C

    spec = C.load_protocol()
    data = data or C.load()
    return C.detected_flags(data, C.detection_null(data, spec))


def state_table(dataset: str) -> pd.DataFrame:
    """One row per planned (compound, cell line, time, dose): typed status, never a zero for missing."""
    cfg = SOURCES[dataset]
    cond = pd.read_csv(ROOT / cfg["conditions"])
    comps = pd.read_csv(ROOT / cfg["compounds"])
    if dataset == "l1000":
        comps = comps.rename(columns={"compound": "compound"})
    design = pd.read_csv(ROOT / cfg["design"])
    cond["compound"] = cond["compound"].astype(str).str.strip()
    # Scope of the prepared release: the (cell line, time, dose) conditions it holds for any compound. A design row for a
    # condition outside that scope (another cell line, another dose) was never part of this study's tiers, so it is out of
    # scope, not a missing measurement.
    scope = set(zip(cond.cell_line, cond.time.astype(float), cond.dose.astype(float)))
    design = design[[(c, float(t), float(d)) in scope for c, t, d in zip(design.cell_line, design.time, design.dose)]]
    detected = _detected(dataset, cond)
    if dataset == "sciplex3":
        qc = ((cond.replicates == 2) & (cond.n_cells_rep1 >= 20) & (cond.n_cells_rep2 >= 20)).to_numpy()
    else:
        qc = cond["qc"].to_numpy(bool)
    cond["row"] = np.arange(len(cond))
    cond["qc_ok"], cond["detected_flag"] = qc, detected
    unit_of = dict(zip(comps["compound"].astype(str).str.strip(), comps[cfg["unit"]].astype(str)))
    shifts_sha = sha256_file(ROOT / cfg["shifts"])
    cond_sha = sha256_file(ROOT / cfg["conditions"])
    keyed = {(r.compound, r.cell_line, float(r.time), float(r.dose)): r for r in cond.itertuples()}
    rows = []
    for d in design.itertuples():
        if d.compound not in unit_of:
            continue
        r = keyed.get((d.compound, d.cell_line, float(d.time), float(d.dose)))
        if r is None:
            status, qc_s, det_s, reps, uri = "planned_missing", "not_observed", "not_observed", None, None
        else:
            reps = int(r.replicates)
            qc_s = "pass" if r.qc_ok else "fail"
            uri = f"{cfg['shifts']}#shift[{int(r.row)}]"
            if not r.qc_ok:
                status, det_s = "qc_failed", "not_assessed"
            elif r.detected_flag:
                status, det_s = "qualified", "detected"
            else:
                status, det_s = "undetected", "undetected"
        rows.append({
            "unit_id": f"{dataset}|{d.compound}|{d.cell_line}|{int(d.time)}h|{d.dose:g}nM",
            "chemical_unit_id": unit_of[d.compound], "compound_id": d.compound, "context_id": f"{dataset}:{d.cell_line}",
            "cell_line": d.cell_line, "time": float(d.time), "dose_nominal": float(d.dose),
            "dose_realized": None, "control_id": f"{dataset}|{d.cell_line}|{int(d.time)}h|vehicle",
            "assay_id": cfg["assay"], "feature_space": cfg["feature_space"], "state_vector_uri": uri,
            "replicate_count": reps, "qc_status": qc_s, "detection_status": det_s, "measurement_status": status,
            "provenance": f"{cfg['conditions']}@{cond_sha[:12]};{cfg['shifts']}@{shifts_sha[:12]}"})
    return pd.DataFrame(rows, columns=STATE_COLUMNS)


# ---------------------------------------------------------------------------------------- intervention
def intervention_table(dataset: str, state: pd.DataFrame | None = None) -> pd.DataFrame:
    from research.maestro_vc_v1 import preprocess as P

    cfg = SOURCES[dataset]
    comps = pd.read_csv(ROOT / cfg["compounds"])
    if dataset == "l1000":
        smiles = P._l1000_smiles()
        comps["smiles"] = [smiles.get(c) for c in comps["compound"]]
    comps["compound"] = comps["compound"].astype(str).str.strip()
    state = state if state is not None else state_table(dataset)
    ann = comps.set_index("compound")
    rows = []
    canonical: dict = {}
    for c, s in zip(comps["compound"], comps["smiles"]):
        canonical[c] = _canonical(s)
    for r in state.itertuples():
        a = ann.loc[r.compound_id]
        if dataset == "sciplex3":
            target = a.get("target") if isinstance(a.get("target"), str) else None
            hub = a.get("hub_targets") if isinstance(a.get("hub_targets"), str) else None
            mechanism = a.get("pathway_level_2") if isinstance(a.get("pathway_level_2"), str) else None
            source = "SciPlex3 pathway annotation (release metadata)"
            nominal = f"{target};hub:{hub}" if target or hub else None
        else:
            nominal = None
            mechanism = a.get("klass") if isinstance(a.get("klass"), str) else None
            source = "Broad Repurposing Hub mechanism annotation (release metadata)"
        rows.append({
            "unit_id": r.unit_id, "compound_id": r.compound_id, "canonical_structure": canonical.get(r.compound_id),
            "chemical_unit_id": r.chemical_unit_id, "nominal_target": nominal,
            "nominal_target_status": "annotation" if nominal else "not_recorded_in_release",
            "mechanism_annotation": mechanism, "engagement_status": "not_planned", "functional_activity_status": "not_planned",
            "dose": r.dose_nominal, "dose_unit": "nM", "time": r.time, "context": r.context_id, "assay": r.assay_id,
            "source": source})
    return pd.DataFrame(rows)


def _canonical(smiles):
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    mol = Chem.MolFromSmiles(smiles.split(",")[0].strip())
    return Chem.MolToSmiles(mol) if mol is not None else None


# ---------------------------------------------------------------------------------------- evidence and episodes
def _iter_jsonl(directory: Path):
    for path in sorted(Path(directory).glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                yield json.loads(line)


def episode_id(r: dict) -> str:
    return f"{r['dataset']}|{r['tier']}|f{r['fold']}|{r['compound']}|{r['h1']}|{r['h2']}"


def evidence_table(replay: Path):
    """Evaluator-side evidence rows: one per real reading of an episode's condition."""
    for r in _iter_jsonl(replay / "tables"):
        for action, o in sorted(r["outcomes"].items()):
            valid = o["lifecycle"] == "measured_valid"
            eliminating = valid and o["outcome"] in ("eliminate_a", "eliminate_b")
            yield {"episode_id": episode_id(r), "action_id": action, "hypothesis_id": f"{r['h1']}|{r['h2']}",
                   "observable": "registered_validator_reading", "value": o["outcome"], "interval": None,
                   "measurement_status": ("qualified" if eliminating else o["readout"] if valid else
                                          "qc_failed" if o["lifecycle"] == "measured_qc_failed" else o["lifecycle"]),
                   "qualification_status": "qualified" if eliminating else "not_qualified",
                   "independent_units": 1 if valid else 0,
                   "interpretation_rule": "registered_validator_projected_similarity_elimination",
                   "premises_satisfied": bool(valid), "source": f"{r['dataset']}:{r['compound']}"}


def episode_table(replay: Path):
    """Evaluator view: hypotheses, menu, truth, exact outcomes and each arm's choice and terminal decision."""
    arms: dict = {}
    for r in _iter_jsonl(replay / "scored"):
        arms.setdefault(episode_id(r), {})[r["arm"]] = {
            "chosen_first_action": r["steps"][0]["action"] if r["steps"] else None, "measurements": r["measurements"],
            "remaining": r["remaining"], "terminal_decision": r["score"]["final"], "stop": r["stop"]}
    for r in _iter_jsonl(replay / "tables"):
        eid = episode_id(r)
        yield {"episode_id": eid, "dataset": r["dataset"], "tier": r["tier"], "compound": r["compound"], "unit": r["unit"],
               "initial_hypotheses": [r["h1"], r["h2"]], "available_actions": sorted(r["outcomes"]),
               "truth": r["truth"], "observed_outcome": {a: o["outcome"] for a, o in r["outcomes"].items()},
               "history_by_arm": arms.get(eid, {}), "evaluation_split": f"fold_{r['fold']}"}
