"""Freeze development-only direction/signature decisions before computing target scores."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = ROOT / "research/astra/zeroshot_context_20261007"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, allow_nan=False, ensure_ascii=False)
        f.write("\n")


def main():
    gene_path = HERE / "sources/genesets.apoptosis.json"
    genes = json.loads(gene_path.read_text())
    names_path = ROOT / "data/virtual_cell/tahoe_c39_x_hvg_feature_names.json"
    names = json.loads(names_path.read_text())["names"]
    mapped = [{"coordinate": i, "gene": name} for i, name in enumerate(names) if name in set(genes["genes"])]
    if mapped != genes["mapped_native_coordinates"]:
        raise ValueError("Curated source mapping differs from verified native gene axis")
    old = json.loads((PRIOR / "AGENT_PROTOCOL.json").read_text())
    labels = old["correlation"]["labels"]
    wells = {}
    for file in ("c20.h5ad", "c27.h5ad"):
        by = {}
        for label, plate, n in json.loads((PRIOR / "census" / f"{file}.json").read_text())["condition_plate_counts"]:
            if label in labels and n >= 100:
                by.setdefault(label, set()).add(plate)
        for label in labels:
            ordered = sorted(by[label], key=lambda p: hashlib.sha256(f"well-role:{label}:{p}".encode()).hexdigest())
            pair = ordered[:2]
            if len(pair) != 2 or (label in wells and wells[label] != pair):
                raise ValueError("Registered menu does not have common independent-well roles")
            wells[label] = pair
    reference = min(labels, key=lambda l: hashlib.sha256(("phenocopy-reference-20261007:" + l).encode()).hexdigest())
    protocol = dict(
        schema="state_direction_decision_opportunity_v1", created_utc=datetime.now(timezone.utc).isoformat(),
        status="Exploratory development only; prior PANC-1/HepG2 outcomes exposed, new target scores not yet computed",
        contexts={"PANC-1": "c20.h5ad", "HepG2/C3A": "c27.h5ad"},
        unavailable_contexts=["HOP62", "Hs 766T", "C32"], source_heldout_outcomes_read=False,
        menu=dict(labels=labels, wells=wells, completeness="All 146 prior replicated labels retained; no source-availability removal"),
        primary=dict(name="curated_transcript_projection", direction="positive", genes=genes["genes"], mapped=mapped,
                     weights="1/K for mapped coordinates, zero elsewhere; no fitted weights",
                     coverage=f"{len(mapped)}/{len(genes['genes'])} Enrichr MSigDB_Hallmark_2020 Apoptosis members",
                     interpretation="Mean member-transcript upregulation; neither apoptosis rate nor protein/pathway activity. Pro- and anti-apoptotic members coexist."),
        secondary=dict(name="native_reference_phenocopy", reference_label=reference, reference_plate=wells[reference][1],
                       vector="Precision-weighted training-panel observed native RNA delta, normalized L2=1; projection normalized by sqrt(2000). Target fixed by metadata hash, not dev outcomes."),
        models={"M0": "45 training-context precision weighted empirical same-well RNA response",
                "M1": "M0 +0.5 gene-gated deviation (prior fixed selected settings)",
                "M2": "M0 +0.5 frozen STATE context deviation relative to training STATE panel mean",
                "M21": "M1 +0.5 frozen STATE context deviation"},
        controls=dict(state_permutation="Permute candidate STATE deviations within native dose/plate strata, seed42; report identity strata and changed rows, do not drop unpermutable records",
                      target_permutation="39 randomly permuted verified named coordinates, seed42; same count/norm. Descriptive alignment control, not a newly chosen biological target"),
        policies=["none", "fixed_top_prior", "knowledge_gradient"],
        acquisition=dict(max_first_well_profiles=8, final_flags=5, budget_cap=13, cost_A=1, cost_B=1,
                         utility="Sum of independent well-B target projections among five flags, committed before B outcomes released",
                         no_acquisition="Five B confirmations, eight unused cap units explicitly reported; same full action menu",
                         comparator="Fixed top-prior first-well screening uses same posterior update as adaptive policy"),
        gaussian_heuristic=dict(training_only="45 checkpoint-training reference contexts; no dev treated values enter belief fitting",
                               covariance="Across-reference-context scalar well-B residual covariance with fixed50% diagonal shrinkage",
                               observation_intercept="Per-label training mean of scalar A-B difference",
                               observation_variance="Per-label variance of scalar A-B differences across training contexts; includes batch/biology, not pure measurement error",
                               global_observation_slope=1.0, numerical_floor=1e-12, posterior_rule="Common Gaussian update; final largest five posterior means",
                               knowledge_gradient_samples=64, normal_seed=42,
                               calibrated_coverage_claim=False, STATE_in_sample_caveat="STATE learned training contexts; uncertainty is common empirical heuristic, not independently calibrated checkpoint residual risk"),
        metrics=["independent_B_utility", "oracle_top5_B_gap_descriptive", "replacements_and_observed_contribution",
                 "A_vs_B_correlation", "direction_ordering_accuracy", "forecast_error", "paid_profiles_credits_unused",
                 "null_mapping_effect", "actual_CPU_time_bytes_read"],
        novelty_limit="Testing whether decision-aligned target directions expose actionable STATE information; using Gaussian KG, Hallmark sets or STATE alone is not itself novelty",
        no_threshold_tuning="Report natural units and fraction of perfect-information headroom; no retrospectively fitted meaningful-gain criterion",
        source_dependencies={gene_path.relative_to(ROOT).as_posix(): digest(gene_path),
                             names_path.relative_to(ROOT).as_posix(): digest(names_path),
                             (PRIOR / "AGENT_PROTOCOL.json").relative_to(ROOT).as_posix(): digest(PRIOR / "AGENT_PROTOCOL.json")},
    )
    write(HERE / "PROTOCOL.json", protocol)
    write(HERE / "PROTOCOL_FREEZE.json", dict(created_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=digest(HERE / "PROTOCOL.json"), registration_code_sha256=digest(Path(__file__)),
        target_projection_results_read_before_freeze=False, exposed_development_only=True))
    print(json.dumps(dict(labels=len(labels), genes=len(mapped), secondary_reference=reference, protocol_sha256=digest(HERE / "PROTOCOL.json"))))


if __name__ == "__main__":
    main()
