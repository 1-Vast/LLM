"""Build production-schema episodes from the external pack's reference blocks.

File summary
- Path: tools/case_memory/build_cases.py
- Purpose: turn the reference side of the untouched data pack into `scm-2` scientific episodes in
  an append-only `EpisodeStore`, demonstrating the production schema on real data. The mechanism
  class is stored as a curated annotation - proxy truth, never biological ground truth - and every
  episode records `data_origin: real` with the pack checksums in provenance.
- Performance: reference centroids and detection thresholds are indexed once and reused across
  leave-one-unit-out episode construction and validation.
- Run: `python -m tools.case_memory.build_cases`
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT))

from tools.datasets import lincs_pack as XD  # noqa: E402


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    denom = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(left @ right / denom) if denom else 0.0


def _reference_centroid(pack, arrays, klass: str, cell: str, exclude: str | None = None):
    return _reference_centroid_from_index(
        pack, arrays, klass, cell, exclude=exclude, index=None
    )


def build_reference_index(pack, arrays):
    """Precompute reference sums/counts for repeated centroid queries.

    Builders and validators ask for the same class/cell centroids many times. Keeping
    sums instead of materialising a fresh list and mean for every query reduces the
    repeated scans while preserving leave-one-unit-out semantics.
    """

    index: dict[tuple[str, str], tuple[np.ndarray, int]] = {}
    for block, unit in pack["units"].items():
        if unit["unseen"]:
            continue
        for cell in unit["conditions"]:
            key = (unit["moa"], cell)
            vector = arrays.get(f"vec::{block}::{cell}")
            if vector is None:
                continue
            total, count = index.get(key, (None, 0))
            index[key] = (vector.copy() if total is None else total + vector, count + 1)
    return index


def reference_norm_thresholds(pack, arrays, percentile: float = 5.0) -> dict[str, float]:
    """Return per-cell detection thresholds from reference vectors in one pass."""

    norms: dict[str, list[float]] = {}
    for block, unit in pack["units"].items():
        if unit["unseen"]:
            continue
        for cell in unit["conditions"]:
            vector = arrays.get(f"vec::{block}::{cell}")
            if vector is not None:
                norms.setdefault(cell, []).append(float(np.linalg.norm(vector)))
    return {
        cell: float(np.percentile(values, percentile)) if values else 0.0
        for cell, values in norms.items()
    }


def _reference_centroid_from_index(pack, arrays, klass: str, cell: str,
                                   exclude: str | None = None, index=None):
    if index is not None:
        total_count = index.get((klass, cell))
        if total_count is None:
            return None
        total, count = total_count
        if exclude is not None:
            excluded = arrays.get(f"vec::{exclude}::{cell}")
            excluded_unit = pack["units"].get(exclude)
            if excluded is not None and excluded_unit is not None and excluded_unit["moa"] == klass:
                total = total - excluded
                count -= 1
        return total / count if count > 0 else None
    members = [b for b, u in pack["units"].items()
               if not u["unseen"] and u["moa"] == klass and b != exclude
               and f"vec::{b}::{cell}" in arrays]
    if not members:
        return None
    return np.mean([arrays[f"vec::{b}::{cell}"] for b in members], axis=0)


def build_reference_episodes(pack, arrays, manifest):
    """Yield proxy episodes using only reference units; no test signatures enter fitted artifacts."""
    from maestro import case_memory as CM
    from maestro import adaptive_retrieval as DR

    units = pack["units"]
    gene_sets = pack["gene_sets"]
    reference_index = build_reference_index(pack, arrays)
    thresholds = reference_norm_thresholds(pack, arrays)
    for unit in units.values():
        for cell in unit["conditions"]:
            thresholds.setdefault(cell, 0.0)
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
                availability="outcome_only",
                pathway_direction={k: round(v, 4) for k, v in state.pathway_direction.items()},
                state_ref=CM.RawDataRef(manifest["inputs"]["gctx"]["path"],
                                        manifest["inputs"]["gctx"]["sha256"], "level5_signature"),
            ))
        hypotheses = tuple(
            [CM.HypothesisClaim(f"class:{klass}", f"mechanism class {klass} (curated annotation)")]
            + [CM.HypothesisClaim(f"class:{d}", f"mechanism class {d} (curated annotation)")
               for d in decoys]
            + [CM.HypothesisClaim("advisory:annotation_error",
                                  "the curated MoA annotation may not describe the realized "
                                  "mechanism in this context", advisory=True)]
        )
        updates = []
        real_measurements = []
        for cell in unit["conditions"]:
            vec = arrays[f"vec::{block}::{cell}"]
            co = _reference_centroid_from_index(
                pack, arrays, klass, cell, exclude=block, index=reference_index
            )
            for primary_decoy in decoys:
                action_id = f"lincs2020:{cell}:24h:10uM"
                cd = (_reference_centroid_from_index(
                    pack, arrays, primary_decoy, cell, index=reference_index
                ) if primary_decoy else None)
                if co is None or cd is None:
                    status, label = CM.ScientificMeasurementStatus.AMBIGUOUS, "unresolved"
                elif float(np.linalg.norm(vec)) < thresholds[cell]:
                    status, label = CM.ScientificMeasurementStatus.UNDETECTED, "absent"
                else:
                    margin = abs(_cosine(vec, co) - _cosine(vec, cd))
                    if margin < 0.02:
                        status, label = CM.ScientificMeasurementStatus.AMBIGUOUS, "unresolved"
                    elif _cosine(vec, co) > _cosine(vec, cd):
                        status, label = CM.ScientificMeasurementStatus.QUALIFIED, "match_h1"
                    else:
                        status, label = CM.ScientificMeasurementStatus.QUALIFIED, "match_h2"
                real_measurements.append(CM.RealMeasurement(
                    action_id, status, label, independent_units=1,
                    source="LINCS2020 Level 5 derived validator; not biological evidence",
                    conditioning_hypothesis=f"class:{klass}",
                    contrast=(f"class:{klass}", f"class:{primary_decoy}"),
                    label_kind="derived_annotation_proxy", sampling_frame="valid_only"))
                updates.append(CM.HypothesisUpdate(
                    action_id, (f"class:{klass}", f"class:{primary_decoy}"), label, (), False,
                    "leave-one-compound-out proxy; no biological hypothesis eliminated"))
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
                                                      for c in unit["conditions"]},
                                 "detection_thresholds_p5": thresholds},
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
                                   "l1000_level5", 8.0, 1.0, "signature",
                                   cell_line=cell, time_h=24.0, dose_nM=10000.0)
                for cell in unit["conditions"]) or (
                CM.CandidateAction("lincs2020:none", "no core-scope signature", "l1000_level5",
                                   0.0, 0.0, "signature", available=False),),
            virtual_cell_forecasts=(), predicted_outcome_branches=(),
            real_measurements=tuple(real_measurements),
            measurement_quality={"label_kind": "derived_annotation_proxy",
                                 "missing_centroid_is_not_qc_failure": True}, qualified_evidence=(), hypothesis_updates=tuple(updates),
            next_action={}, branching_interpretation_plan=(),
            final_decision={"status": "open", "basis": "reference case of the proxy benchmark"},
            failure_modes=(), calibration_history=(),
            provenance={"builder": "tools.case_memory.build_cases",
                        "sources": manifest["inputs"]["gctx"]["sha256"],
                        "created_at": "2026-09-29", "data_origin": "real",
                        "pack_manifest": "data/processed/case_memory_integration/pack_manifest.json",
                        "label_kind": "curated_annotation_proxy",
                        "independent_unit": block, "builder_version": "loo-proxy-3"},
        )
        yield episode


def main() -> int:
    from maestro import case_memory as CM

    pack, arrays = XD.load_pack()
    manifest = json.loads((ROOT / "data/processed/case_memory_integration/pack_manifest.json").read_text())
    output = os.environ.get("MAESTRO_CASE_MEMORY_EPISODES_OUT")
    output = Path(output) if output else ROOT / "outputs/case_memory_integration/episodes/proxy_reference_cases_v3.jsonl.gz"
    store = CM.EpisodeStore(output)
    written = 0
    for episode in build_reference_episodes(pack, arrays, manifest):
        existing = store.get(episode.case_id)
        if existing is None:
            store.append(episode)
            written += 1
        elif existing.digest != episode.digest:
            raise ValueError("output_contains_different_cases:choose_a_new_output_path")
    print(json.dumps({"episodes_written": written, "snapshot": store.snapshot_digest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
