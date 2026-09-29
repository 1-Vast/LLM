"""Build production-schema episodes from the external pack's reference blocks.

File summary
- Path: tools/case_memory/build_cases.py
- Purpose: turn the reference side of the untouched data pack into `scm-2` scientific episodes in
  an append-only `EpisodeStore`, demonstrating the production schema on real data. The mechanism
  class is stored as a curated annotation - proxy truth, never biological ground truth - and every
  episode records `data_origin: real` with the pack checksums in provenance.
- Run: `python -m tools.case_memory.build_cases`
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT))

from research.case_memory_integration import external_data as XD  # noqa: E402


def main() -> int:
    from maestro import case_memory as CM
    from maestro import directional as DR

    pack, arrays = XD.load_pack()
    units = pack["units"]
    manifest = json.loads((ROOT / "data/processed/case_memory_integration/pack_manifest.json").read_text())
    store = CM.EpisodeStore(ROOT / "outputs/case_memory_integration/episodes/reference_cases.jsonl.gz")
    gene_sets = pack["gene_sets"]
    written = 0
    for block, unit in sorted(units.items()):
        if unit["unseen"]:
            continue  # test units are never cases: the memory is reference-side only
        klass = unit["moa"]
        pool = pack["pool"]
        decoys = tuple(c for c in pool if c != klass)
        observations = []
        for cell in unit["conditions"]:
            vec = arrays[f"vec::{block}::{cell}"]
            delta = {g: float(v) for g, v in zip(pack["landmark_symbols"], vec)}
            state = DR.directional_state_from_shift(delta, gene_sets)
            norm = float(np.linalg.norm(vec))
            observations.append(CM.EpisodeObservation(
                condition_id=f"lincs2020:{cell}:24h:10uM",
                status=CM.ScientificMeasurementStatus.QUALIFIED,
                assay="l1000_level5", cell_line=cell, time_h=24.0, dose_nM=10000.0,
                readout="signature_norm", value=norm,
                pathway_direction={k: round(v, 4) for k, v in state.pathway_direction.items()},
                state_ref=CM.RawDataRef(manifest["inputs"]["gctx"]["path"],
                                        manifest["inputs"]["gctx"]["sha256"], "level5_signature"),
            ))
        hypotheses = tuple(
            [CM.HypothesisClaim(f"class:{klass}", f"mechanism class {klass} (curated annotation)")]
            + [CM.HypothesisClaim(f"class:{d}", f"mechanism class {d} (curated annotation)")
               for d in decoys[:1]]
            + [CM.HypothesisClaim("advisory:annotation_error",
                                  "the curated MoA annotation may not describe the realized "
                                  "mechanism in this context", advisory=True)]
        )
        updates = []
        for cell in unit["conditions"]:
            eliminated = []
            for decoy in decoys:
                co_key = f"centroid::{klass}::{cell}"
                cd_key = f"centroid::{decoy}::{cell}"
                if co_key in arrays and cd_key in arrays:
                    vec = arrays[f"vec::{block}::{cell}"]
                    co, cd = arrays[co_key], arrays[cd_key]
                    cos_o = float(vec @ co / (np.linalg.norm(vec) * np.linalg.norm(co) + 1e-12))
                    cos_d = float(vec @ cd / (np.linalg.norm(vec) * np.linalg.norm(cd) + 1e-12))
                    if abs(cos_o - cos_d) >= 0.02 and cos_o > cos_d:
                        eliminated.append(f"class:{decoy}")
            updates.append(CM.HypothesisUpdate(
                f"lincs2020:{cell}:24h:10uM", (f"class:{klass}", "class:*pool*"),
                "unit_out_reading_vs_each_pool_class", tuple(eliminated),
                bool(eliminated), "proxy validator reading on curated annotations"))
        episode = CM.ScientificEpisode(
            case_id=f"lincs2020:{block}", case_version=1, case_kind=CM.CaseKind.CANONICAL,
            problem_type="mechanism_contrast_transcriptomic",
            user_question=("Proxy benchmark case: which curated mechanism class does this "
                           "compound's signature resemble? Curated MoA annotations are proxy "
                           "truth, not biological ground truth."),
            raw_data_references=(CM.RawDataRef(manifest["inputs"]["gctx"]["path"],
                                               manifest["inputs"]["gctx"]["sha256"],
                                               "level5_signature"),),
            data_quality_report={"signature_norms": {c: float(np.linalg.norm(arrays[f"vec::{block}::{c}"]))
                                                      for c in unit["conditions"]}},
            context_fingerprint={"dataset": "lincs2020", "assay": "l1000_level5",
                                 "context": "core_scope", "biological_system": "l1000",
                                 "measurement_type": "transcriptomic",
                                 "control_design": "plate_population",
                                 "intervention_type": "compound", "time_h": 24.0,
                                 "dose_nM": 10000.0},
            initial_observations=tuple(observations),
            initial_hypotheses=hypotheses,
            hypothesis_graph={}, retrieved_cases=(), adaptation_map=(),
            candidate_actions=tuple(
                CM.CandidateAction(f"lincs2020:{cell}:24h:10uM", "L1000 Level 5 signature",
                                   "l1000_level5", 8.0, 1.0, "signature")
                for cell in unit["conditions"]) or (
                CM.CandidateAction("lincs2020:none", "no core-scope signature", "l1000_level5",
                                   0.0, 0.0, "signature", available=False),),
            virtual_cell_forecasts=(), predicted_outcome_branches=(), real_measurements=(),
            measurement_quality={}, qualified_evidence=(), hypothesis_updates=tuple(updates),
            next_action={}, branching_interpretation_plan=(),
            final_decision={"status": "open", "basis": "reference case of the proxy benchmark"},
            failure_modes=(), calibration_history=(),
            provenance={"builder": "tools.case_memory.build_cases",
                        "sources": manifest["inputs"]["gctx"]["sha256"],
                        "created_at": "2026-09-29", "data_origin": "real",
                        "pack_manifest": "data/processed/case_memory_integration/pack_manifest.json",
                        "label_kind": "curated_annotation_proxy"},
        )
        store.append(episode)
        written += 1
    print(json.dumps({"episodes_written": written,
                      "snapshot": store.snapshot_digest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
