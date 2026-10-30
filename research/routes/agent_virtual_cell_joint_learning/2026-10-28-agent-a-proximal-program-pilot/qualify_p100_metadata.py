"""Offline P100/PRISM metadata qualification; never opens a PRISM effect matrix."""
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import csv
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET

import pandas as pd
from rdkit import Chem, rdBase


ROOT = Path(__file__).resolve().parents[2]
EPISODE = Path(__file__).resolve().parent
P100 = ROOT / "data/external/p100_program_pilot_20261028/raw"
PRISM = ROOT / "data/external/prism_19q4/raw"
SEALED = ROOT / "research/knowledge_reality_20261013/sealed_compounds.csv"


def fingerprint(path):
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def read_csv(name):
    path = PRISM / name
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        records = list(reader)
        fields = reader.fieldnames
    return records, {**fingerprint(path), "rows": len(records), "fields": fields}


def core(value):
    match = re.match(r"^(BRD-[A-Z]\d{8})(?:-|$)", value)
    return match.group(1) if match else None


def decimal_string(value):
    return format(Decimal(value).normalize(), "f")


def canonical_smiles(value):
    molecule = Chem.MolFromSmiles(value)
    return Chem.MolToSmiles(molecule, isomericSmiles=True) if molecule is not None else None


def read_gct(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        assert stream.readline().strip() == "#1.3"
        nr, nc, nrm, ncm = map(int, stream.readline().split())
        offset = 1 + nrm
        header = stream.readline().rstrip("\r\n").split("\t")
        assert len(header) == offset + nc
        sample_ids = header[offset:]
        sample_meta = {}
        for _ in range(ncm):
            fields = stream.readline().rstrip("\r\n").split("\t")
            assert len(fields) == offset + nc
            sample_meta[fields[0]] = fields[offset:]
        rows = []
        for _ in range(nr):
            # The matrix suffix is neither converted to numbers nor analyzed.
            fields = stream.readline().rstrip("\r\n").split("\t", offset)
            rows.append(dict(zip(header[:offset], fields[:offset])))
        assert not stream.read().strip()
    samples = [dict(id=sid, **{k: v[i] for k, v in sample_meta.items() if k != "id"})
               for i, sid in enumerate(sample_ids)]
    assert len(set(sample_ids)) == nc
    assert len({x["pr_id"] for x in rows}) == nr
    groups = defaultdict(list)
    for sample in samples:
        key = tuple(sample[k] for k in ("cell_id", "pert_id", "pert_dose", "pert_dose_unit",
                                        "pert_time", "pert_time_unit", "pert_type"))
        groups[key].append(sample)
    for group in groups.values():
        assert sorted(x["pert_batch_internal_replicate"] for x in group) == ["1", "2", "3"]
        assert len({x["det_well"] for x in group}) == 3
        assert len({x["det_filename"] for x in group}) == 3
    info = {**fingerprint(path), "dimensions": [nr, nc, nrm, ncm],
            "row_fields": header[:offset], "sample_fields": list(sample_meta),
            "unique_row_ids": nr, "unique_sample_ids_within_file": nc,
            "metadata_counts": {k: dict(Counter(x[k] for x in samples)) for k in
                                ("cell_id", "det_plate", "pert_type", "pert_dose_unit", "pert_time",
                                 "pert_time_unit", "pert_batch_internal_replicate", "provenance_code")},
            "condition_groups": len(groups), "all_groups_have_three_distinct_wells_and_raw_files": True,
            "probe_suitability": dict(Counter(x["pr_probe_suitability_manual"] for x in rows)),
            "probe_clusters": dict(Counter(x["pr_p100_cluster"] for x in rows)),
            "unique_genes": len({x["pr_gene_symbol"] for x in rows}),
            "raw_filename_date_prefixes": sorted({x["det_filename"].split("_")[0] for x in samples}),
            "row_normalization_groups": dict(Counter(x["pr_probe_normalization_group"] for x in rows)),
            "sample_normalization_vectors": dict(Counter(x["det_normalization_group_vector"] for x in samples))}
    return samples, rows, info


def main():
    rdBase.DisableLog("rdApp.error")
    # Explicit column projection: sealed annotations and any effect files are not used.
    sealed_ids = set(pd.read_csv(SEALED, usecols=["core"], dtype=str)["core"].dropna())
    parsed = [read_gct(path) for path in sorted(P100.glob("*.gct"))]
    assert len(parsed) == 3
    samples = [sample for ss, _, _ in parsed for sample in ss]
    excluded_controls = {"dmso", "staurosporine", "vorinostat"}
    drug_map = {}
    for sample in samples:
        if sample["pert_iname"].lower() not in excluded_controls and sample["pert_id"] not in sealed_ids:
            drug_map[sample["pert_id"]] = sample
    trt, trt_info = read_csv("secondary-screen-replicate-treatment-info.csv")
    collapsed, collapsed_info = read_csv("secondary-screen-replicate-collapsed-treatment-info.csv")
    pools, pool_info = read_csv("secondary-screen-pooling-info.csv")
    cells, cell_info = read_csv("secondary-screen-cell-line-info.csv")
    by_drug = defaultdict(list)
    for row in trt:
        if row["perturbation_type"] == "experimental_treatment" and core(row["broad_id"]) in drug_map:
            by_drug[core(row["broad_id"])].append(row)
    cell_names = {x["cell_id"] for x in samples}
    cell_matches = {}
    for name in sorted(cell_names):
        matches = [row for row in cells if row["ccle_name"].split("_")[0] == name
                   and row["passed_str_profiling"] == "TRUE"]
        assert len(matches) == 1
        cell_matches[name] = matches[0]
    pool_by_cell_screen = defaultdict(list)
    for row in pools:
        if row["passed_str_profiling"] == "TRUE":
            pool_by_cell_screen[(row["depmap_id"], row["screen_id"])].append(row)
    candidates = []
    exact = []
    target_genes = defaultdict(set)
    target_sets = defaultdict(set)
    for cid, sample in sorted(drug_map.items()):
        records = by_drug.get(cid, [])
        compound_samples = [x for x in samples if x["pert_id"] == cid]
        p100_structures = {canonical_smiles(x["isomeric_smiles"]) for x in compound_samples}
        prism_structures = {canonical_smiles(s) for row in records for s in row["smiles"].split(", ")}
        annotations = sorted({row["target"].strip() for row in records if row["target"].strip()})
        for annotation in annotations:
            genes = tuple(sorted(x.strip() for x in annotation.split(",") if x.strip()))
            target_sets[genes].add(cid)
            for gene in genes:
                target_genes[gene].add(cid)
        dose = decimal_string(sample["pert_dose"])
        matched = [row for row in records if decimal_string(row["dose"]) == dose]
        candidate = {"pert_id": cid, "p100_name": sample["pert_iname"], "p100_dose_uM": dose,
                     "pubchem_cid": sample["pubchem_cid"], "lsm_id": sample["lsm_id"],
                     "p100_canonical_isomeric_smiles_unique_count": len(p100_structures - {None}),
                     "p100_invalid_smiles": None in p100_structures,
                     "prism_invalid_smiles": None in prism_structures,
                     "p100_structures_consistent_across_plates": len(p100_structures) == 1 and None not in p100_structures,
                     "canonical_isomeric_structure_shared_with_prism": bool((p100_structures & prism_structures) - {None}),
                     "normalization_vectors_by_cell": {cell: sorted({x["det_normalization_group_vector"]
                                                                    for x in compound_samples if x["cell_id"] == cell})
                                                       for cell in sorted(cell_names)},
                     "prism_names": sorted({r["name"] for r in records}),
                     "prism_broad_batch_ids": sorted({r["broad_id"] for r in records}),
                     "prism_target_annotations": annotations,
                     "prism_target_annotation_disagreement": len(annotations) > 1,
                     "prism_moa_annotations": sorted({r["moa"] for r in records if r["moa"]}),
                     "prism_doses_uM": sorted({decimal_string(r["dose"]) for r in records}, key=Decimal),
                     "prism_same_dose_screens": sorted({r["screen_id"] for r in matched})}
        candidates.append(candidate)
        for cell, cell_row in cell_matches.items():
            available = [row for row in matched
                         if (cell_row["depmap_id"], row["screen_id"]) in pool_by_cell_screen]
            screens = sorted({row["screen_id"] for row in available})
            if not screens:
                continue
            chosen = "MTS010" if "MTS010" in screens else screens[0]
            exact.append({"pert_id": cid, "p100_name": sample["pert_iname"], "cell_id": cell,
                          "depmap_id": cell_row["depmap_id"], "ccle_name": cell_row["ccle_name"],
                          "dose_uM": dose, "p100_time_h": sample["pert_time"], "screens": screens,
                          "preferred_screen": chosen,
                          "p100_structures_consistent_across_plates": candidate["p100_structures_consistent_across_plates"],
                          "canonical_isomeric_structure_shared_with_prism": candidate["canonical_isomeric_structure_shared_with_prism"],
                          "replicate_metadata_rows_by_screen": dict(Counter(r["screen_id"] for r in available)),
                          "pools_by_screen": {screen: [{k: row[k] for k in
                                                       ("detection_pool", "pool_id", "analyte_id", "minipool_id")}
                                                      for row in pool_by_cell_screen[(cell_row["depmap_id"], screen)]]
                                              for screen in screens},
                          "numeric_response_missingness_checked": False})
    def groups_as_records(groups):
        return [{"target": ", ".join(key) if isinstance(key, tuple) else key,
                 "compounds": [{"pert_id": cid, "name": drug_map[cid]["pert_iname"]} for cid in sorted(cids)]}
                for key, cids in sorted(groups.items()) if len(cids) >= 2]
    exact_ids = {x["pert_id"] for x in exact}
    exact_multitarget = {target: cids & exact_ids for target, cids in target_genes.items()}
    common_rows = set.intersection(*[{x["pr_id"] for x in rows} for _, rows, _ in parsed])
    common_suitable = set.intersection(*[{x["pr_id"] for x in rows
                                        if x["pr_probe_suitability_manual"] == "TRUE"} for _, rows, _ in parsed])
    xml_path = EPISODE / "sources/p100_2021.xml"
    article = ET.parse(xml_path).getroot()
    ids = {x.attrib.get("pub-id-type"): x.text for x in article.findall("./front/article-meta/article-id")}
    output = {"generated_with": {"executable": sys.executable, "python": sys.version, "rdkit": rdBase.rdkitVersion},
              "scope": "offline metadata only; PRISM effect matrices, old confirmation and credentials not opened",
              "source_article": {**fingerprint(xml_path), "title": "".join(article.find(".//article-title").itertext()),
                                 "identifiers": ids},
              "inputs": {"p100_gcts": [info for _, _, info in parsed],
                         "prism_metadata": [trt_info, collapsed_info, pool_info, cell_info],
                         "prism_readme": fingerprint(PRISM / "secondary-screen-readme.txt"),
                         "sealed_id_exclusion_file": fingerprint(SEALED)},
              "p100_summary": {"total_sample_columns": len(samples), "cells": sorted(cell_names),
                               "unique_chemical_ids_including_vehicle": len({x["pert_id"] for x in samples}),
                               "nonvehicle_ids": len({x["pert_id"] for x in samples if x["pert_type"] == "trt_cp"}),
                               "candidate_ids_after_controls_and_sealed_exclusion": len(drug_map),
                               "common_row_ids": len(common_rows), "common_manual_suitable_row_ids": len(common_suitable),
                               "common_manual_suitable_row_id_list": sorted(common_suitable),
                               "all_sample_keys_plate_and_header_unique": len({(x["det_plate"],x["id"]) for x in samples}) == len(samples),
                               "numeric_matrix_values_analyzed": False},
              "cell_identity_mapping": cell_matches,
              "prism_screen_counts": {"replicate_treatment": dict(Counter(r["screen_id"] for r in trt)),
                                      "collapsed_treatment": dict(Counter(r["screen_id"] for r in collapsed)),
                                      "pooling": dict(Counter(r["screen_id"] for r in pools))},
              "prism_replicate_detection_plate_time_tokens": dict(Counter(
                  (re.search(r"_(\d+H)_", r["detection_plate"]).group(1)
                   if re.search(r"_(\d+H)_", r["detection_plate"]) else "not_explicit") for r in trt)),
              "candidate_metadata": candidates,
              "intersection": {"id_matching": "BRD parent core only, not drug batch/salt stereochemistry verification",
                               "dose_matching": "exact Decimal equality in uM; no nearest-dose tolerance",
                               "cell_screen_matching": "exact ccle prefix -> unique STR-passing depmap_id -> same screen_id in pooling",
                               "candidate_ids_with_prism_annotation": len(by_drug),
                               "same_id_cell_dose_condition_count": len(exact),
                               "same_id_cell_dose_unique_compounds": len(exact_ids),
                               "same_id_cell_dose_conditions": exact,
                               "fully_time_matched_condition_count_certified": 0,
                               "fully_time_matched_reason": "P100 3h; PRISM has no explicit time field, MTS010 filenames encode 120H; no 3h condition certified"},
              "nominal_target_gene_groups_at_least_two_compounds": groups_as_records(target_genes),
              "identical_target_set_groups_at_least_two_compounds": groups_as_records(target_sets),
              "nominal_target_groups_with_at_least_two_exact_dose_compounds": groups_as_records(exact_multitarget),
              "engagement_measured": False,
              "prism_response_nonmissingness_measured": False}
    out_path = EPISODE / "p100_qualification_counts.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out_path), "samples": len(samples), "candidates": len(drug_map),
                      "annotated_candidates": len(by_drug), "exact_same_dose_compounds": len(exact_ids),
                      "exact_same_dose_cell_conditions": len(exact),
                      "common_manual_suitable_probes": len(common_suitable),
                      "nominal_shared_target_groups": len(output["nominal_target_gene_groups_at_least_two_compounds"]),
                      "exact_dose_shared_target_groups": len(output["nominal_target_groups_with_at_least_two_exact_dose_compounds"])},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
