"""Read-only probes that check the gated plan's audit claims by executing the code they concern.

File summary
- Path: research/gated_plan/probes.py
- Purpose: every statement in `AUDIT.md` that code can decide is decided here, not inferred from
  documentation. The probes read code, committed result files and metadata. They write nothing
  except the output JSON, change no module state, and open no sealed outcome.
- Core points:
  - `tree`: commit, branch and dirty paths of the checkout the audit describes.
  - `historical`: the six historical claims recomputed from the registered protocol-v2 result
    files, with population, denominator, weighting and uncertainty.
  - `gse70138_manifest`: the external cohort funnel, rebuilt from metadata only
    (`external_phase2.manifest`, which reads no measurement, QC metric or label).
  - `availability`: whether the protocol-v2 legal menu can move with an outcome. It lists the
    SciPlex3 conditions absent from the prepared table, counts their cells in the raw release,
    and asks `contracts.availability` whether they are offered.
  - `evidence`: the production admission path (`InterpretationTable`, `EvidenceState`,
    `SourceClusterIndex`, `PremiseRequirement`) on constructed records: retrieved text, QC
    failure, condition mismatch, duplicate citations with and without a registered cluster, and a
    lysate grant against an engagement premise.
  - `validator`: the research validator on an undetected reading, and its reference-absence
    elimination branch.
  - `splits`: whether SciPlex3 development folds are identity- or scaffold-disjoint.
- Run: python -m research.gated_plan.probes --out FILE [--skip-raw]
- Interfaces: `tree`, `historical`, `gse70138_manifest`, `availability`, `evidence`, `validator`, `splits`,
  `main`
- Depends on: research/protocol_v2, research/belief_planning, research/dynamic_world_model, src/maestro
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20260927/0927"
for extra in (ROOT / "src", ROOT / "research/dynamic_world_model", ROOT / "research/biological_depth"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def tree() -> dict:
    status = [line for line in _git("status", "--porcelain").splitlines() if line]
    return {"head": _git("rev-parse", "HEAD"), "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty_paths": status, "clean": not status}


# ------------------------------------------------------------------------------------ historical
def historical() -> dict:
    """The historical claims, recomputed from the registered protocol-v2 analyses."""
    head = json.loads((LOG / "protocol_v2_headroom_registered.json").read_text(encoding="utf-8"))
    screen = json.loads((LOG / "protocol_v2_dev_screen_analysis.json").read_text(encoding="utf-8"))
    cal = json.loads((LOG / "protocol_v2_calibration_registered.json").read_text(encoding="utf-8"))
    tasks = {}
    for name, t in head.items():
        p = t["power"]
        tasks[name] = {
            "units": t["units"], "episodes": t["episodes"],
            "episodes_per_unit": round(t["episodes"] / t["units"], 2),
            "fixed_correct": t["fixed_correct"], "oracle_correct": t["oracle_correct"],
            "fixed_share_of_oracle": t["fixed_correct"] / t["oracle_correct"],
            "headroom_correct": t["headroom_correct"]["difference"], "headroom_ci95": t["headroom_correct"]["ci"],
            "point_estimate_weighting": "episode mean (equal compound weight within a tier); CI by unit-cluster bootstrap",
            "power_basis": f"paired SE of {p['candidate']} minus fixed", "unit_sd": p["se"] * t["units"] ** 0.5,
            "mde_at_current_n": p["mde_at_current_n"], "units_required_for_0.02": p["units_required_for_mpie"],
            "gate": t["gate"]["status"],
        }
    ident = {k: {"episodes": v["episodes"], "unidentifiable_with_this_menu": v["unidentifiable_with_this_menu"],
                 "identifiable": v["identifiable"], "misleading": v["misleading"], "conflicting": v["conflicting"]}
             for k, v in screen["identifiability"].items()}
    second = {}
    for k, v in screen["second_step_headroom"].items():
        second[k] = {"conditional_on_a_legal_second_step": v["second_step_headroom"],
                     "share_of_all_episodes": v["share_of_all_episodes"],
                     "per_all_episodes": v["second_step_headroom"] * v["share_of_all_episodes"]}
    calibration = {}
    for study, block in cal["loso"].items():
        raw = block["methods"]["raw"]
        calibration[study] = {"items": block["n"], "units": block["units"], "observed": block["observed"],
                              "forecast": raw["mean"], "observed_over_forecast": raw["observed_over_forecast"],
                              "population": "executed QC-passed steps of the `belief` arm, leave-one-study-out"}
    ext = cal["post_hoc_external"]
    calibration["gse70138"] = {"items": ext["n"], "units": ext["units"], "observed": ext["observed"],
                               "forecast": ext["methods"]["raw"]["mean"],
                               "observed_over_forecast": ext["methods"]["raw"]["observed_over_forecast"],
                               "population": "post hoc; labels opened once by protocol v1"}
    shares = [v["fixed_share_of_oracle"] for v in tasks.values()]
    return {"tasks": tasks, "identifiability": ident, "second_step_headroom": second,
            "calibration": calibration, "stop_gate": cal["stop_gate_alternatives"],
            "fixed_share_of_oracle_range": [min(shares), max(shares)]}


def gse70138_manifest() -> dict:
    from research.belief_planning import external_phase2 as E
    man = E.manifest()
    return {"audit": man["audit"], "reference_compounds": len(man["reference_compounds"]),
            "test_compounds": len(man["test_compounds"]),
            "test_units": len({c["unit"] for c in man["test_compounds"]}),
            "keys": man["keys"], "sources": man["sources"]}


# ---------------------------------------------------------------------------------- availability
def availability(read_raw: bool = True) -> dict:
    """Is a condition hidden from the legal menu because of an outcome (too few surviving cells)?"""
    import common as C
    from research.protocol_v2 import contracts as K
    data = C.load()
    cond = data.conditions
    doses = sorted(cond.dose.unique())
    expected = set()
    for (line, t), group in cond.groupby(["cell_line", "time"]):
        for compound in set(group.compound):
            expected.update((line, float(t), float(d), compound) for d in doses)
    present = set(zip(cond.cell_line, cond.time.astype(float), cond.dose.astype(float), cond.compound))
    missing = sorted(expected - present)
    keys = sorted({(m[0], m[1], m[2]) for m in missing})
    compounds = sorted({m[3] for m in missing})
    offered = K.availability(SimpleNamespace(data=data), keys, compounds)
    rows = []
    for line, t, d, compound in missing:
        rows.append({"cell_line": line, "time": t, "dose_nM": d, "compound": compound,
                     "offered_by_v2_menu": (line, t, d) in offered[compound]})
    manifest = json.loads((ROOT / "outputs/biological_depth_20260926/prepared/prepare_manifest.json")
                          .read_text(encoding="utf-8"))["audit"]
    out = {"expected_conditions": len(expected), "present": len(present), "missing": rows,
           "excluded_replicate_groups_24h": len(manifest.get("excluded_replicate_groups", [])),
           "exclusion_rule": "replicate group below 20 cells is excluded (biological_depth protocol "
                             "minimum_cells_per_group; dynamic_world_model minimum_cells_per_replicate)"}
    if read_raw:
        import h5py
        import pandas as pd
        from prepare import obs_column
        with h5py.File(ROOT / "data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad", "r") as f:
            meta = pd.DataFrame({k: obs_column(f["obs"], k) for k in
                                 ("cell_line", "perturbation", "dose_value", "time", "replicate")})
        meta["perturbation"] = meta.perturbation.astype(str).str.strip()
        counts = meta.groupby(["cell_line", "time", "dose_value", "perturbation", "replicate"]).size()
        for row in rows:
            row["raw_cells"] = {rep: int(counts.get((row["cell_line"], row["time"], row["dose_nM"], row["compound"], rep), 0))
                                for rep in ("rep1", "rep2")}
        out["all_missing_were_profiled"] = all(sum(r["raw_cells"].values()) > 0 for r in rows)
    out["menu_moves_with_outcome"] = any(not r["offered_by_v2_menu"] for r in rows)
    return out


# -------------------------------------------------------------------------------------- evidence
def _observation(**kw):
    from maestro.models import EvidenceKind
    base = dict(action_identifier="assay", quality_passed=True, interpretation_fields=("readout:x",),
                context_identifier="ctx", time_hours=24.0, conditions={}, evidence_kind=EvidenceKind.REAL_MEASUREMENT,
                independent_units=3, result_id="r1", source_id="lab:exp1", metrics={})
    base.update(kw)
    return SimpleNamespace(**base)


def evidence() -> dict:
    from maestro.models import (BiologicalQuantity, EvidenceAction, EvidenceKind, FunctionalInterventionProfile,
                                MechanismContrast, MechanismHypothesis, PremiseGrant, PremiseRequirement)
    from maestro.outcome import EvidenceState, InterpretationTable, OutcomeRule
    from maestro.handoff import SourceCluster, SourceClusterIndex
    h1, h2 = MechanismHypothesis("H1", "a"), MechanismHypothesis("H2", "b")
    action = EvidenceAction("assay", "registered readout", 1.0, ("H1", "H2"), time_hours=24.0,
                            expected_conditions={"dose": "1uM"})
    contrast = MechanismContrast("c", (h1, h2), ("x",), action)
    profile = FunctionalInterventionProfile(mode="small_molecule", context_identifier="ctx")
    table = InterpretationTable((OutcomeRule("r", "matches_h1", matched_fields=frozenset({"readout:x"}),
                                             eliminates=frozenset({"H2"})),))
    cases = {
        "real_matched": _observation(conditions={"dose": "1uM"}),
        "retrieved_text": _observation(conditions={"dose": "1uM"}, evidence_kind=EvidenceKind.RETRIEVED_SOURCE),
        "model_prediction": _observation(conditions={"dose": "1uM"}, evidence_kind=EvidenceKind.MODEL_PREDICTION),
        "qc_failed": _observation(conditions={"dose": "1uM"}, quality_passed=False),
        "condition_unmatched": _observation(conditions={"dose": "10uM"}),
    }
    results = {}
    for name, obs in cases.items():
        interp = table.interpret(obs, contrast, profile, action)
        state = EvidenceState.open((h1, h2)).apply(interp, obs)
        results[name] = {"outcome_class": interp.outcome_class.value, "eliminated": sorted(state.eliminated)}
    # Duplicate citations of one experiment.
    first, second = _observation(source_id="paper:fig2"), _observation(source_id="review:cites_fig2", result_id="r2")
    registered = SourceClusterIndex((SourceCluster("exp1", frozenset({"paper:fig2", "review:cites_fig2"})),))
    unregistered = SourceClusterIndex()
    clusters = {}
    for label, index in (("registered_cluster", registered), ("no_cluster_registered", unregistered)):
        state = EvidenceState.open((h1, h2))
        for obs in (first, second):
            interp = table.interpret(obs, contrast, profile, action)
            state = state.apply(interp, obs, source_cluster=index.cluster_of(obs.source_id))
        clusters[label] = len(state.independent_source_clusters)
    # A lysate engagement grant against an engagement premise that names no sample state.
    req = PremiseRequirement("engagement:target", BiologicalQuantity.ENGAGEMENT_SHIFT, context_identifier="K562")
    lysate = PremiseGrant("engagement:target", "lysate_cetsa", BiologicalQuantity.ENGAGEMENT_SHIFT,
                          context_identifier="K562", site="lysate", quality="passed", quality_passed=True,
                          provenance="lab:lysate")
    req_site = PremiseRequirement("engagement:target", BiologicalQuantity.ENGAGEMENT_SHIFT,
                                  context_identifier="K562", site="intact_cell")
    return {
        "interpretation": results,
        "only_real_matched_eliminates": (results["real_matched"]["eliminated"] == ["H2"]
                                          and all(not v["eliminated"] for k, v in results.items() if k != "real_matched")),
        "independent_clusters_for_two_citations_of_one_experiment": clusters,
        "unknown_dependence_counted_as_independent": clusters["no_cluster_registered"] > 1,
        "lysate_grant_unmet_reasons_without_site": list(req.unmet_reasons(lysate)),
        "lysate_grant_unmet_reasons_with_site": list(req_site.unmet_reasons(lysate)),
    }


# ------------------------------------------------------------------------------------- validator
def validator() -> dict:
    import common as C
    rng = np.random.default_rng(0)
    undetected_eliminations = 0
    for _ in range(2000):
        scores = rng.uniform(-1, 1, 2)
        if C.decide(False, scores, 0, 1, np.array([5, 5]), np.array([5, 5]), 0.0, 0.0) != "undetected":
            undetected_eliminations += 1
    # A class with measured references but no detected template is eliminated by a detected profile
    # that clears the floor for the other class; two measured references suffice.
    absence = C.decide(True, np.array([0.9, 0.0]), 0, 1, np.array([5, 2]), np.array([5, 0]), 0.3, 0.1)
    return {"undetected_readings_that_eliminated": undetected_eliminations, "trials": 2000,
            "reference_absence_branch": {"measured_references_of_other_class": 2, "detected_templates": 0,
                                          "outcome": absence}}


# ---------------------------------------------------------------------------------------- splits
def splits() -> dict:
    """Which generalisation claim the SciPlex3 development folds support: identity or scaffold."""
    import pandas as pd
    from rdkit import Chem, RDLogger
    from rdkit.Chem.Scaffolds import MurckoScaffold
    RDLogger.DisableLog("rdApp.*")
    comp = pd.read_csv(ROOT / "outputs/biological_depth_20260926/prepared/compounds.csv").drop_duplicates("compound")

    def scaffold(smiles):
        mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
        return MurckoScaffold.MurckoScaffoldSmiles(mol=mol) if mol is not None else None

    comp["scaffold"] = comp.smiles.map(scaffold)
    comp = comp[comp.scaffold.notna() & (comp.scaffold != "")]
    spanning = comp.groupby("scaffold").fold.nunique()
    spanning = spanning[spanning > 1]
    return {"compounds_with_scaffold": int(len(comp)), "scaffolds": int(comp.scaffold.nunique()),
            "scaffolds_spanning_folds": int(len(spanning)),
            "compounds_on_spanning_scaffolds": int(comp.scaffold.isin(spanning.index).sum()),
            "skeleton_groups": int(comp.skeleton.nunique()),
            "skeletons_spanning_folds": int((comp.groupby("skeleton").fold.nunique() > 1).sum()),
            "fold_rule": "SciPlex3: skeleton (InChIKey first block); L1000: components sharing an InChIKey "
                         "block or a Bemis-Murcko scaffold (lincs_prepare)"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--skip-raw", action="store_true", help="do not count cells in the 2.4 GB raw release")
    args = parser.parse_args()
    result = {"tree": tree(), "historical": historical(), "gse70138_manifest": gse70138_manifest(),
              "availability": availability(read_raw=not args.skip_raw), "evidence": evidence(),
              "validator": validator(), "splits": splits()}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    h = result["historical"]
    print("fixed/oracle", [round(x, 4) for x in h["fixed_share_of_oracle_range"]])
    print("gse70138", result["gse70138_manifest"]["test_compounds"], "test compounds;",
          result["gse70138_manifest"]["audit"]["new_compounds"], "new")
    a = result["availability"]
    print("availability: missing", len(a["missing"]), "menu moves with outcome", a["menu_moves_with_outcome"],
          "profiled", a.get("all_missing_were_profiled"))
    e = result["evidence"]
    print("evidence:", e["only_real_matched_eliminates"], e["independent_clusters_for_two_citations_of_one_experiment"],
          e["lysate_grant_unmet_reasons_without_site"], e["lysate_grant_unmet_reasons_with_site"])
    print("validator:", result["validator"])
    print("splits:", result["splits"])


if __name__ == "__main__":
    main()
