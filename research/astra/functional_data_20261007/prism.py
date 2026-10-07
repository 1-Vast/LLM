"""Qualify partial PRISM observations as a separate assay task, never exact Jaaks fills."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger

from research.astra.functional_data_20261007.acquire import HERE, ROOT
from research.astra.drylab_followup_20261007.reproduce import load_replay


def alias(value):
    return re.sub(r"[\s_-]+", "", str(value).casefold())


def structures(value):
    if pd.isna(value):
        return set()
    result = set()
    for text in str(value).split(","):
        mol = Chem.MolFromSmiles(text.strip())
        if mol is None:
            return set()
        result.add(Chem.MolToSmiles(mol, isomericSmiles=True))
    return result


def main():
    out = HERE / "prism_qualified"
    out.mkdir(exist_ok=False)
    raw = HERE / "acquisition/prism"
    treatment = pd.read_csv(raw / "primary-screen-replicate-collapsed-treatment-info.csv")
    cells = pd.read_csv(raw / "primary-screen-cell-line-info.csv")
    identity = pd.read_csv(ROOT / "research/astra/mono_pretraining_20261005/data_s0/drug_identity_map.csv", dtype={"jaaks_id": str})
    drugs = pd.read_csv(ROOT / "research/astra/drylab_solution_20261007/data/drug.csv", dtype={"drug_id": str})
    identity = identity[identity.jaaks_id.isin(drugs.drug_id)]
    aliases = {}
    for row in identity.itertuples(index=False):
        names = str(row.jaaks_names).split(" ; ") + str(row.cmp_synonyms).split(",")
        for name in names:
            if name and name != "nan":
                aliases.setdefault(alias(name), set()).add(row.jaaks_id)
    mapped = []
    RDLogger.DisableLog("rdApp.error")
    idrows = identity.set_index("jaaks_id")
    for row in treatment.itertuples(index=False):
        candidates = aliases.get(alias(row.name), set())
        if len(candidates) != 1:
            continue
        drug = next(iter(candidates))
        a = structures(row.smiles)
        b = structures(idrows.loc[drug, "pubchem_smiles"])
        verified = bool(a and b and a == b and len(a) == 1 and "|" not in drug)
        mapped.append(dict(jaaks_drug_id=drug, column_name=row.column_name, broad_id=row.broad_id,
                           public_name=row.name, dose_uM=row.dose,
                           status="alias_and_exact_isomeric_structure" if verified else "alias_only_unresolved_structure",
                           structure_agreement=verified, time_h=120, time_source="PRISM paper methods/ExtendedData Fig1, not per-record time",
                           assay="pooled_barcode_abundance", normalized_observation="ComBat-corrected log2 fold change vs DMSO",
                           jaaks_exact_match=False))
    matching = pd.DataFrame(mapped)
    matching.to_csv(out / "drug_mapping.csv", index=False)
    model = pd.read_csv(ROOT / "research/astra/repeat_signal_20261005/next_sources/Model.csv", dtype=str)
    valid_map = model[["ModelID", "SangerModelID"]].dropna().drop_duplicates()
    duplicated = valid_map.ModelID.duplicated(keep=False) | valid_map.SangerModelID.duplicated(keep=False)
    valid_map = valid_map[~duplicated]
    cells = cells.merge(valid_map.rename(columns={"ModelID": "depmap_id", "SangerModelID": "sidm"}), on="depmap_id", how="left", validate="many_to_one")
    _, _, menu = load_replay().load_data()
    target = set(menu.SIDM)
    cells["target_excluded"] = cells.sidm.isin(target)
    cells["eligible_identity"] = cells.passed_str_profiling.eq(True) & cells.sidm.notna() & ~cells.target_excluded
    cells.to_csv(out / "cell_mapping.csv", index=False)
    columns = ["Unnamed: 0"] + matching.loc[matching.structure_agreement, "column_name"].tolist()
    matrix = pd.read_csv(raw / "primary-screen-replicate-collapsed-logfold-change.csv", usecols=columns).rename(columns={"Unnamed: 0": "row_name"})
    matrix = matrix.merge(cells[["row_name", "sidm", "eligible_identity", "primary_tissue"]], on="row_name", how="left", validate="one_to_one")
    matrix = matrix[matrix.eligible_identity.eq(True)]
    values = matrix.melt(id_vars=["row_name", "sidm", "primary_tissue"], value_vars=columns[1:], var_name="column_name", value_name="log2_fold_change")
    values = values[np.isfinite(values.log2_fold_change)].merge(matching, on="column_name", validate="many_to_one")
    values.to_csv(out / "reference_observations.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    assert not set(values.sidm) & target
    summary = {"status": "Qualified independent assay-task references; no current Jaaks same-condition fill",
               "public_primary_matrix_cells": int(len(pd.read_csv(raw / "primary-screen-replicate-collapsed-logfold-change.csv", usecols=[0]))),
               "public_treatment_records": len(treatment), "alias_candidates": len(matching),
               "alias_drugs": int(matching.jaaks_drug_id.nunique()),
               "structure_matched_drugs": int(matching[matching.structure_agreement].jaaks_drug_id.nunique()),
               "qualified_response_records": len(values), "qualified_reference_cells": int(values.sidm.nunique()),
               "target_cells_excluded": int(cells.target_excluded.sum()),
               "boundary_drugs": matching[matching.jaaks_drug_id.isin(["1005", "1022", "1179", "1057"])][["jaaks_drug_id", "public_name", "dose_uM", "status"]].to_dict("records"),
               "limits": ["Five-day pooled barcode assay differs from72h ATP single-culture screen", "PRISM release applied ComBat before row exclusions; excluding target rows does not remove all preprocessing dependence", "STR/model mappings required; unmapped cells retained only in quarantine map", "Dose mismatch cannot be erased", "Alias-only compounds not used in reference observations", "Not target state or calibrated mechanism probabilities"]}
    (out / "qualification.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
