"""A0 census: which measured chemical-genetic pairs exist locally, under what conditions, and what truth backs them.

Metadata only. Reads L1000 signature metadata (GSE92742 and GSE70138), the Repurposing Hub annotation
table and the MAP-KG edge list, and lists the files in every directory that could hold independent
target-engagement evidence. It opens no expression matrix, no PRISM 24Q2 response and downloads nothing.

    python research/mechanism_falsification_20261014/census.py            # writes CENSUS.json
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STUDY = Path(__file__).resolve().parent
P1 = ROOT / "data/external/lincs_l1000_gse92742"
P2 = ROOT / "data/external/lincs_l1000_phase2/meta"
HUB = P1 / "repurposing_drugs_20200324.txt"
MAPKG_EDGES = ROOT / "data/external/mapkg_20261009/DRUG-GENE_filtered_by_existing_drugs_and_genes.csv"
MAPKG_GENES = ROOT / "data/external/mapkg_20261009/GENE_tahoe_filtered.csv"
GENETIC = {"trt_sh.cgs": "knockdown_consensus", "trt_sh": "knockdown_single_hairpin", "trt_oe": "overexpression"}
INHIBIT = re.compile(r"inhibitor|antagonist|blocker|degrader|disruptor|depleter|inverse agonist|suppressor", re.I)
ACTIVATE = re.compile(r"agonist|activator|stimulant|potentiator|opener|inducer|enhancer|stabilizer", re.I)
# Places that could hold target-engagement, rescue or epistasis evidence independent of annotation.
TRUTH_CANDIDATES = {
    "biophysical_engagement_PISA": "data/external/pisa_living_cells",
    "biophysical_engagement_Hill2017": "data/external/hill2017",
    "kinobeads_lysate_engagement": "data/raw/kinobeads",
    "kinobeads_1000": "data/raw/kinobeads1000",
    "nyman2020_engagement_prep": "data/external/nyman2020/data",
    "engagement_case_package_v1": "data/evaluation/cases/engagement_v1",
    "case_packages_real": "data/evaluation/cases/real",
    "case_packages_real_v2": "data/evaluation/cases/real_v2",
    "case_packages_real_v3": "data/evaluation/cases/real_v3",
    "jump_target_cell_painting_pairs": "data/external/jump_target",
    "pubchem_pharmacology_descriptions": "data/external/gcp2020/pharmacology",
}
TRUTH_FILE_PATTERNS = re.compile(r"rescue|epistasis|achilles|gene_effect|crispr|cetsa|pisa|kinobead|engagement|ic50|ki_|chembl", re.I)


def _load(base: Path, suffix: str = "") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    sig = pd.read_csv(next(base.glob(f"GSE*_sig_info{suffix}*.txt.gz")), sep="\t", low_memory=False)
    pert = pd.read_csv(next(base.glob(f"GSE*_pert_info{suffix}*.txt.gz")), sep="\t", low_memory=False)
    metrics = next(base.glob("GSE*_sig_metrics*.txt.gz"), None)
    return sig, pert, (pd.read_csv(metrics, sep="\t", low_memory=False) if metrics else None)


def _hub() -> pd.DataFrame:
    hub = pd.read_csv(HUB, sep="\t", comment="!", low_memory=False)
    hub["key"] = hub.pert_iname.astype(str).str.strip().str.lower()
    return hub.drop_duplicates("key").set_index("key")


def _direction(moa: str) -> str:
    moa = str(moa)
    if INHIBIT.search(moa) and not ACTIVATE.search(moa.replace("inverse agonist", "")):
        return "inhibition"
    if ACTIVATE.search(moa) and not INHIBIT.search(moa):
        return "activation"
    return "unspecified"


def _hours(label: str) -> float:
    m = re.match(r"\s*([\d.]+)\s*h", str(label))
    return float(m.group(1)) if m else math.nan


def _plates(distil: str) -> list[str]:
    return sorted({d.split(":")[0] for d in str(distil).split("|")})


def _gold(metrics: pd.DataFrame) -> set[str]:
    """CMap's published reproducibility rule: distil_cc_q75 >= 0.2 and pct_self_rank_q25 <= 5.

    Consensus gene signatures (trt_sh.cgs) have no self-rank (it is -666 for every one), so for them the
    rule is reduced to distil_cc_q75 >= 0.2; this is a declared variant, not the published rule.
    """

    cc = pd.to_numeric(metrics.distil_cc_q75, errors="coerce")
    rank = pd.to_numeric(metrics.pct_self_rank_q25, errors="coerce")
    cgs = metrics.pert_type == "trt_sh.cgs"
    return set(metrics.sig_id[((cc >= 0.2) & (rank >= 0) & (rank <= 5)) | (cgs & (cc >= 0.2))])


def scan_truth_assets() -> dict:
    out = {}
    for name, rel in TRUTH_CANDIDATES.items():
        path = ROOT / rel
        files = [p for p in path.rglob("*") if p.is_file()] if path.exists() else []
        out[name] = {"path": rel, "exists": path.exists(), "files": len(files), "bytes": int(sum(p.stat().st_size for p in files))}
    named = sorted(p.relative_to(ROOT).as_posix() for base in ("data", "research") for p in (ROOT / base).rglob("*")
                   if p.is_file() and p.suffix.lower() in {".csv", ".tsv", ".gz", ".npz", ".parquet", ".json", ".txt"}
                   and TRUTH_FILE_PATTERNS.search(p.name) and "mechanism_falsification" not in p.as_posix())
    out["files_whose_names_suggest_truth_evidence"] = named[:60]
    return out


def phase_summary(sig: pd.DataFrame) -> dict:
    counts = sig.pert_type.value_counts().to_dict()
    return {"signatures_by_type": {k: int(v) for k, v in sorted(counts.items())},
            "cell_lines_by_type": {t: int(sig[sig.pert_type == t].cell_id.nunique()) for t in sorted(counts)}}


def main() -> int:
    sig, pert, metrics = _load(P1)
    gold = _gold(metrics)
    sig["gold"] = sig.sig_id.isin(gold)
    sig["hours"] = sig.pert_itime.map(_hours)
    hub = _hub()
    cp = sig[sig.pert_type == "trt_cp"].copy()
    pert_cp = pert[pert.pert_type == "trt_cp"].drop_duplicates("pert_id").set_index("pert_id")
    cp["iname_key"] = cp.pert_iname.astype(str).str.strip().str.lower()
    in_hub = cp.iname_key.isin(hub.index)
    cp["targets"] = [set(str(hub.at[k, "target"]).split("|")) - {"nan", ""} if k in hub.index else set() for k in cp.iname_key]
    cp["moa"] = [str(hub.at[k, "moa"]) if k in hub.index else "" for k in cp.iname_key]
    cp["direction"] = cp.moa.map(_direction)
    cp["family"] = cp.moa.map(lambda m: m.split("|")[0].strip().lower() if m else "")
    compounds = cp.drop_duplicates("pert_id")
    census: dict = {
        "study": "mechanism_falsification_20261014 A0 census (metadata only)",
        "reads": [str(p.relative_to(ROOT)).replace("\\", "/") for p in (HUB, MAPKG_EDGES, MAPKG_GENES)]
                 + ["data/external/lincs_l1000_gse92742/GSE92742_Broad_LINCS_{sig_info,pert_info,sig_metrics}.txt.gz",
                    "data/external/lincs_l1000_phase2/meta/GSE70138_Broad_LINCS_{sig_info,pert_info}_2017-03-06.txt.gz"],
        "expression_matrices_opened": False, "prism_24q2_responses_opened": False, "downloads": 0,
        "exposure": "every L1000 signature was exposed to earlier MAESTRO studies; any result here is exploratory",
        "gold_rule": "distil_cc_q75 >= 0.2 and pct_self_rank_q25 <= 5 (CMap-published reproducibility rule, applied by this census)",
        "phase1": phase_summary(sig),
        "phase2": phase_summary(_load(P2, "")[0]),
    }
    census["compounds"] = {
        "trt_cp_signatures": int(len(cp)), "unique_pert_id": int(cp.pert_id.nunique()),
        "with_hub_record": int(compounds.iname_key.isin(hub.index).sum()),
        "with_hub_target": int((compounds.targets.map(len) > 0).sum()),
        "with_hub_direction_inhibition": int((compounds.direction == "inhibition").sum()),
        "with_hub_direction_activation": int((compounds.direction == "activation").sum()),
        "with_smiles": int(pert_cp.reindex(compounds.pert_id).canonical_smiles.map(lambda s: isinstance(s, str) and s not in ("-666", "")).sum()),
        "dose_time_top": {k: int(v) for k, v in (cp.pert_idose + " / " + cp.pert_itime).value_counts().head(6).items()},
    }
    # genetic perturbation inventory per line and modality
    genetic = {m: sig[sig.pert_type == m] for m in GENETIC}
    gene_sets = {(m, line): set(d[d.cell_id == line].pert_iname) for m, d in genetic.items() for line in d.cell_id.unique()}
    census["genetic"] = {m: {"signatures": int(len(d)), "genes": int(d.pert_iname.nunique()), "cell_lines": int(d.cell_id.nunique()),
                             "gold_signatures": int(d.gold.sum()), "time_hours": {str(k): int(v) for k, v in d.hours.value_counts().head(5).items()}}
                         for m, d in genetic.items()}
    # pairs: (compound, annotated target, cell line) with a measured genetic signature of that target in that line
    rows = []
    for (pid, line), group in cp.groupby(["pert_id", "cell_id"]):
        targets, direction, family = group.targets.iloc[0], group.direction.iloc[0], group.family.iloc[0]
        for m in GENETIC:
            genes = gene_sets.get((m, line), set()) & targets
            for gene in genes:
                rows.append((pid, group.pert_iname.iloc[0], gene, line, m, direction, family))
    pairs = pd.DataFrame(rows, columns=["pert_id", "iname", "gene", "line", "modality", "direction", "family"])
    pairs["pair_class"] = [("LOF_analogue" if (d == "inhibition" and m != "trt_oe") else "GOF_analogue" if (d == "activation" and m == "trt_oe")
                            else "direction_mismatch" if d in ("inhibition", "activation") else "direction_unspecified")
                           for d, m in zip(pairs.direction, pairs.modality)]
    census["pairs_annotation_only"] = {
        "definition": "compound with a Hub-annotated target T, in a cell line where a genetic signature of T was measured; the pairing rests on a database annotation, not on measured engagement",
        "triples_compound_gene_line_modality": int(len(pairs)),
        "unique_compounds": int(pairs.pert_id.nunique()), "unique_genes": int(pairs.gene.nunique()),
        "unique_mechanism_families": int(pairs.family.replace("", np.nan).nunique()),
        "cell_lines": int(pairs.line.nunique()),
        "by_modality": {k: int(v) for k, v in pairs.modality.value_counts().items()},
        "by_pair_class": {k: int(v) for k, v in pairs.pair_class.value_counts().items()},
        "by_line": {k: int(v) for k, v in pairs.line.value_counts().head(12).items()},
    }
    # condition matching of the pairs
    cp_times, g_times = cp.groupby(["pert_id", "cell_id"]).hours.apply(lambda s: sorted(set(s.dropna()))), {}
    for m, d in genetic.items():
        g_times[m] = d.groupby(["pert_iname", "cell_id"]).hours.apply(lambda s: sorted(set(s.dropna())))
    matched, matched_by = 0, {}
    for r in pairs.itertuples():
        ct = set(cp_times.get((r.pert_id, r.line), []))
        gt = set(g_times[r.modality].get((r.gene, r.line), []))
        if ct & gt:
            matched += 1
            matched_by[r.modality] = matched_by.get(r.modality, 0) + 1
    plates_cp = {p for d in cp.distil_id for p in _plates(d)}
    plate_overlap = {}
    for m, d in genetic.items():
        shared = d[[bool(set(_plates(x)) & plates_cp) for x in d.distil_id]]
        plate_overlap[m] = {"signatures_on_a_plate_that_also_holds_chemical_wells": int(len(shared)),
                            "their_perturbation_ids": sorted(shared.pert_id.astype(str).unique())[:10]}
    census["condition_matching"] = {
        "pairs_with_an_exactly_matching_exposure_time": int(matched), "pairs_total": int(len(pairs)),
        "exact_time_matches_by_modality": matched_by, "plate_overlap": plate_overlap,
        "typical_chemical_times_h": sorted(set(cp.hours.dropna()))[:6], "typical_genetic_times_h": [96, 120, 144],
        "note": "chemical signatures are 6 h or 24 h, shRNA signatures 96 h or later: the two interventions are observed at different "
                "points of the response; consensus knockdown and overexpression signatures never share a plate with chemical wells, and the few "
                "single-hairpin signatures that do are control wells on compound plates, not designed pairs",
    }
    # qualifying signatures per pair
    qual_cp = set(cp[(cp.gold) & (cp.pert_idose == "10 µM") & (cp.hours.isin([6.0, 24.0]))].pert_id.astype(str) + "|" + cp.cell_id)
    g_gold = {m: set(d[d.gold].pert_iname.astype(str) + "|" + d[d.gold].cell_id) for m, d in genetic.items()}
    qualifying = [(f"{r.pert_id}|{r.line}" in qual_cp) and (f"{r.gene}|{r.line}" in g_gold[r.modality]) for r in pairs.itertuples()]
    pairs["qualifying"] = qualifying
    q = pairs[pairs.qualifying]
    census["qualifying_pairs"] = {
        "rule": "gold chemical signature at 10 uM, 6 h or 24 h, and a gold genetic signature of the annotated target, same line",
        "triples": int(len(q)), "compounds": int(q.pert_id.nunique()), "genes": int(q.gene.nunique()),
        "mechanism_families": int(q.family.replace("", np.nan).nunique()), "cell_lines": int(q.line.nunique()),
        "by_modality": {k: int(v) for k, v in q.modality.value_counts().items()},
        "by_pair_class": {k: int(v) for k, v in q.pair_class.value_counts().items()},
        "families_with_at_least_3_compounds": int((q.groupby("family").pert_id.nunique() >= 3).sum()),
        "largest_families_by_compounds": {k: int(v) for k, v in q.groupby("family").pert_id.nunique().sort_values(ascending=False).head(8).items()},
    }
    # replicate and batch structure of the qualifying signatures
    key = sig.set_index("sig_id")
    cp_q = cp[cp.pert_id.isin(q.pert_id) & cp.cell_id.isin(q.line) & cp.gold]
    census["replicate_and_batch_structure"] = {
        "chemical_replicates_per_signature_median": float(np.median([len(str(d).split("|")) for d in cp_q.distil_id])) if len(cp_q) else None,
        "chemical_plates_per_signature_median": float(np.median([len(_plates(d)) for d in cp_q.distil_id])) if len(cp_q) else None,
        "vehicle_control_signatures": int((sig.pert_type == "ctl_vehicle").sum()),
        "vector_control_signatures": int((sig.pert_type == "ctl_vector").sum()),
        "note": "every L1000 chemical signature is a plate-level differential expression against that plate's vehicle; genetic signatures use vector controls on other plates",
    }
    # decoys: unannotated genes with a genetic signature in the same line (constructed, never a verified negative)
    decoy_pool = {line: sorted(gene_sets.get(("trt_sh.cgs", line), set())) for line in q.line.unique()}
    census["constructed_decoys"] = {
        "definition": "genes with a measured consensus knockdown in the same line that the Hub does not list for the compound; a decoy is a bias probe, never a verified false target",
        "mean_pool_size_per_line": float(np.mean([len(v) for v in decoy_pool.values()])) if decoy_pool else 0.0,
        "qualifying_pairs_with_decoy_pool_at_least_100": int(sum(len(decoy_pool.get(l, [])) >= 100 for l in q.line)),
    }
    # GSE70138 (phase 2) holds CRISPR knockout (trt_xpr) signatures; its QC metrics file is not local, so these counts are ungated
    sig2 = _load(P2, "")[0]
    sig2["hours"] = sig2.pert_itime.map(_hours)
    cp2 = sig2[sig2.pert_type == "trt_cp"].copy()
    cp2["key"] = cp2.pert_iname.astype(str).str.strip().str.lower()
    cp2["targets"] = [set(str(hub.at[k, "target"]).split("|")) - {"nan", ""} if k in hub.index else set() for k in cp2.key]
    xpr = sig2[sig2.pert_type == "trt_xpr"]
    cell2 = pd.read_csv(next(P2.glob("GSE70138_Broad_LINCS_cell_info*.txt.gz")), sep="	", low_memory=False)
    base_of = dict(zip(cell2.cell_id, cell2.base_cell_id))
    xpr_genes_exact = {line: set(g.pert_iname) for line, g in xpr.groupby("cell_id")}
    xpr_genes = {line: set(g.pert_iname) for line, g in xpr.assign(base=xpr.cell_id.map(base_of)).groupby("base")}
    exact_triples = sum(len(grp.targets.iloc[0] & xpr_genes_exact.get(line, set())) for (pid, line), grp in cp2.groupby(["pert_id", "cell_id"]))
    rows2 = [(pid, gene, line) for (pid, line), grp in cp2.groupby(["pert_id", "cell_id"]) for gene in grp.targets.iloc[0] & xpr_genes.get(line, set())]
    p2 = pd.DataFrame(rows2, columns=["pert_id", "gene", "line"])
    cp_t2 = cp2.groupby(["pert_id", "cell_id"]).hours.apply(lambda x: set(x.dropna()))
    xp_t2 = xpr.assign(base=xpr.cell_id.map(base_of)).groupby(["pert_iname", "base"]).hours.apply(lambda x: set(x.dropna()))
    census["phase2_knockout_pairs_ungated"] = {
        "crispr_knockout_signatures": int(len(xpr)), "knockout_genes": int(xpr.pert_iname.nunique()), "knockout_cell_lines": int(xpr.cell_id.nunique()),
        "knockout_times_h": {str(k): int(v) for k, v in xpr.hours.value_counts().head(4).items()},
        "knockout_cell_ids": sorted(xpr.cell_id.unique()),
        "triples_with_the_identical_cell_id": int(exact_triples),
        "note": "knockout lines are Cas9-expressing derivatives (.311 / .101) of the compound lines; pairing them to the parent line (below) is a context assumption, not a match",
        "annotation_only_triples_via_parent_line": int(len(p2)), "compounds": int(p2.pert_id.nunique()), "genes": int(p2.gene.nunique()), "cell_lines": int(p2.line.nunique()),
        "pairs_with_an_exactly_matching_exposure_time": int(sum(bool(cp_t2.get((r.pert_id, r.line), set()) & xp_t2.get((r.gene, r.line), set())) for r in p2.itertuples())),
        "qc_gating": "none: GSE70138 sig_metrics is not a local asset",
    }
    # annotation dependence: Hub and MAP-KG are built from overlapping upstream databases
    edges = pd.read_csv(MAPKG_EDGES)
    genes = pd.read_csv(MAPKG_GENES)
    symbol = dict(zip(genes["Gene stable ID"], genes["Gene name"].astype(str)))
    cid = pert_cp.pubchem_cid.dropna() if "pubchem_cid" in pert_cp.columns else pd.Series(dtype=float)
    mk = {}
    for d, g in zip(edges["Drug ID"], edges["Gene ID"]):
        if g in symbol:
            mk.setdefault(int(d), set()).add(symbol[g])
    agree = both = 0
    for r in q.drop_duplicates(["pert_id", "gene"]).itertuples():
        c = pert_cp.pubchem_cid.get(r.pert_id)
        try:
            c = int(float(c))
        except (TypeError, ValueError):
            continue
        if c in mk:
            both += 1
            agree += r.gene in mk[c]
    census["annotation_dependence"] = {
        "hub_target_source": "Repurposing Hub (curated from literature and databases; non-commercial licence)",
        "mapkg_source": "MAP-KG (derived from ChEMBL / DrugBank-class resources)",
        "dependency": "both annotation sources draw on overlapping upstream databases and are not independent evidence of engagement",
        "qualifying_compound_gene_pairs_also_in_mapkg": both, "of_which_mapkg_agrees": agree,
    }
    census["independent_mechanism_truth"] = {
        "categories": {"measured_positive_reference": 0, "measured_negative_reference": 0,
                       "annotation_only_candidate": int(len(q.drop_duplicates(["pert_id", "gene"]))),
                       "constructed_decoy": "constructible; not a truth label", "unknown": "all other compound-gene combinations"},
        "assets_scanned": scan_truth_assets(),
        "finding": "no local asset holds target-engagement, genetic-rescue, epistasis or CRISPR-dependency evidence for these compounds",
    }
    census["power"] = {
        "independent_measured_positive_references": 0, "independent_measured_negative_references": 0,
        "units_for_any_annotation_based_analysis": {"compounds": census["qualifying_pairs"]["compounds"],
                                                      "mechanism_families": census["qualifying_pairs"]["mechanism_families"]},
        "zero_failure_bound": "demonstrating a false-rejection rate <= 0.10 at 95% confidence with no observed failure needs 29 independent positive references (0.9^n <= 0.05)",
        "estimation_halfwidth": "at an observed false-rejection rate of 0.05, a 95% interval half-width of 0.07 needs about 37 independent positive references; compound-level units inside one family count once",
        "available_now": 0,
    }
    census["a0_decision"] = "INSUFFICIENT_MECHANISM_TRUTH"
    census["a0_also_blocked_by"] = ["INSUFFICIENT_CONTEXT_MATCHING (exposure time matches for under 1% of pairs, all overexpression; no designed pair shares a plate)"]
    census["a0_reading"] = ("The falsification estimand needs independently supported positive mechanisms and independently excluded ones. "
                            "None exists locally, so false rejection of true mechanisms and exclusion of false ones cannot be measured. "
                            "Annotation-recovery results on these pairs would be a replication of earlier annotation-recovery work, not mechanism validation.")
    (STUDY / "CENSUS.json").write_text(json.dumps(census, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: census[k] for k in ("a0_decision", "pairs_annotation_only", "qualifying_pairs", "condition_matching")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
