"""Build the MAESTRO-VC v1 data products and the manifest that names every file with its checksum.

File summary
- Path: research/maestro_vc_v1/data_layer.py
- Purpose: one command that validates the inputs, writes the five logical tables, the policy and
  evaluator views, the case memory (both problem families) and the source manifest, so that every
  derived artefact has a provenance record and a SHA-256.
- Core points:
  - Order: source records, validation report, state and intervention tables, evidence and episode
    tables from the replay, policy and evaluator views with their audit, the case tables of the full
    library (no held-out fold) for the four tiers and the second family, then the manifest.
  - Outputs: `data/processed/maestro_vc_v1/` (tables and views), `outputs/scientific_case_memory/`
    (case store snapshots, adaptation tables) and `data/manifests/maestro_vc_v1_manifest.json`.
  - The case table of the full library is what a real user problem retrieves from; the fold snapshots
    the replay used are named in the manifest with their digests.
  - Nothing is downloaded here: every input is local, and the manifest records which local file each
    table was built from.
- Run: python -m research.maestro_vc_v1.data_layer [--replay DIR]
- Interfaces: `build`, `main`
- Depends on: sources.py, preprocess.py, tables.py, views.py, family2.py, research/scientific_case_memory
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from . import family2 as F2
from . import preprocess as PP
from . import sources as SRC
from . import tables as T
from . import views as V

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/processed/maestro_vc_v1"
MANIFEST = ROOT / "data/manifests/maestro_vc_v1_manifest.json"
CASES = ROOT / "outputs/scientific_case_memory"
REPLAY = ROOT / "outputs/maestro_vc_v1/replay"
CREATED_AT = "2026-09-29"
FULL_FOLD = 99
"""A fold number no compound has: the memory of a real user problem holds every reference, none held out."""


def build(replay: Path = REPLAY, *, with_cases: bool = True) -> dict:
    started = time.time()
    files: dict = {}
    # ---- sources and validation
    sources = SRC.collect()
    report = PP.run_all(ROOT / "outputs/maestro_vc_v1/preprocess/validation_report.json")
    files["validation_report"] = {"path": "outputs/maestro_vc_v1/preprocess/validation_report.json",
                                  "sha256": T.sha256_file(ROOT / "outputs/maestro_vc_v1/preprocess/validation_report.json"),
                                  "summary": report["summary"]}
    # ---- state and intervention tables
    for dataset in ("sciplex3", "l1000"):
        state = T.state_table(dataset)
        files[f"state_table_{dataset}"] = T.write_frame(state, PROCESSED / f"state_table_{dataset}.csv")
        files[f"state_table_{dataset}"]["status_counts"] = {k: int(v) for k, v in state.measurement_status.value_counts().items()}
        files[f"intervention_table_{dataset}"] = T.write_frame(T.intervention_table(dataset, state),
                                                               PROCESSED / f"intervention_table_{dataset}.csv")
    # ---- evidence and episode tables, policy and evaluator views
    if (replay / "tables").exists():
        files["evidence_table"] = T.write_jsonl(T.evidence_table(replay), PROCESSED / "evidence_table.jsonl.gz")
        episodes = list(T.episode_table(replay))
        files["episode_table_evaluator_view"] = T.write_jsonl((V.evaluator_view(e) for e in episodes),
                                                              PROCESSED / "episode_table_evaluator_view.jsonl.gz")
        manifest = json.loads((replay / "manifest.json").read_text(encoding="utf-8"))
        smiles = _smiles()
        policy = []
        for e in episodes:
            task = f"{e['dataset']}_{e['tier']}_{e['evaluation_split'].replace('fold_', '')}"
            snap = manifest["snapshots"][task]
            setting = manifest["settings"][f"{e['dataset']}_{e['tier']}"]
            policy.append(V.policy_view(e, setting, smiles=smiles, snapshot_digest=snap["digest"],
                                        training_references=snap["training_cases"]))
        problems = V.audit_policy_records(policy)
        files["episode_table_policy_view"] = T.write_jsonl(policy, PROCESSED / "episode_table_policy_view.jsonl.gz")
        files["episode_table_policy_view"]["audit_problems"] = problems
    # ---- case memory: full libraries and the second family
    if with_cases:
        from research.scientific_case_memory import build_cases as BC

        rows = []
        for dataset, tier in (("sciplex3", "A"), ("sciplex3", "B"), ("l1000", "LT"), ("l1000", "T")):
            inputs = BC.load_inputs(dataset, tier, FULL_FOLD)
            snap = BC.build_snapshot(inputs, created_at=CREATED_AT, snapshot_id=f"{dataset}-{tier}-full")
            path = CASES / f"library_{dataset}_{tier}.jsonl.gz"
            snap.store.write_snapshot(path)
            files[f"case_library_{dataset}_{tier}"] = {**snap.manifest, "path": T._rel(path), "sha256": T.sha256_file(path)}
            files[f"case_library_{dataset}_{tier}"].pop("adaptation_table_rows", None)
            (CASES / f"adaptation_table_{dataset}_{tier}.json").write_text(
                json.dumps(snap.adaptation.rows(), indent=1), encoding="utf-8")
            rows += [_case_row(c) for c in snap.store.latest() if c.case_kind.value != "adaptation"]
        family = F2.build_store()
        path = CASES / "cases_genetic_pharmacological_and_engagement.jsonl.gz"
        family.write_snapshot(path)
        files["case_family2"] = {"path": T._rel(path), "sha256": T.sha256_file(path), "cases": len(family),
                                 "snapshot_digest": family.snapshot_digest()}
        rows += [_case_row(c) for c in family.latest()]
        files["case_table"] = T.write_jsonl(rows, PROCESSED / "case_table.jsonl.gz")
    manifest_out = {"version": "maestro-vc-v1", "created_at": CREATED_AT, "seconds": round(time.time() - started, 1),
                    "sources": sources, "files": files}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest_out, indent=1, default=str), encoding="utf-8")
    return manifest_out


def _case_row(case) -> dict:
    """The case-table row of the design: its fields as JSON, hypotheses and graph included."""
    from research.scientific_case_memory import case_schema as S

    d = S.to_dict(case)
    return {"case_id": d["case_id"], "case_version": d["case_version"], "case_kind": d["case_kind"],
            "problem_type": d["problem_type"], "context_fingerprint": d["context_fingerprint"],
            "observation_bundle": d["initial_observations"], "hypothesis_graph": d["provenance"].get("graph"),
            "initial_hypotheses": d["initial_hypotheses"], "candidate_actions": d["candidate_actions"],
            "retrieved_cases": None, "adaptation_map": d["adaptation_map"], "virtual_forecasts": d["virtual_cell_predictions"],
            "real_outcomes": d["real_measurements"], "evidence_updates": d["hypothesis_updates"],
            "final_decision": d["final_decision"], "failure_modes": d["failure_modes"],
            "calibration_history": d["calibration_history"], "provenance": {k: v for k, v in d["provenance"].items() if k != "graph"}}


def _smiles() -> dict:
    import pandas as pd

    out = {}
    sp = pd.read_csv(ROOT / "outputs/biological_depth_20260926/prepared/compounds.csv")
    out.update(dict(zip(sp["compound"].astype(str), sp["smiles"])))
    out.update({k: v for k, v in PP._l1000_smiles().items()})
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", default=str(REPLAY))
    parser.add_argument("--no-cases", action="store_true")
    args = parser.parse_args()
    result = build(Path(args.replay), with_cases=not args.no_cases)
    print(json.dumps({k: (v if k != "sources" else len(v)) for k, v in result.items() if k != "files"}, default=str))
    for name, f in result["files"].items():
        print(name, f.get("rows", f.get("cases", "")), f.get("sha256", "")[:12])


if __name__ == "__main__":
    main()
