"""Recover actual component dose vectors from public design annotations only."""
from __future__ import annotations

import json
import re
import zipfile
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from research.astra.functional_data_20261007.acquire import HERE, RAW, ROOT
from research.astra.drylab_followup_20261007.reproduce import load_replay


def as_intervention(record):
    from virtual_cell.biology import CompositeIntervention, InterventionComponent
    ids = str(record["component_ids"]).split("|")
    values = [float(x) for x in str(record["component_doses_uM"]).split("|")]
    if len(ids) != len(values) or any(not np.isfinite(x) or x <= 0 for x in values):
        raise ValueError("invalid_source_recipe")
    return CompositeIntervention(
        identifier=str(record["composite_id"]), context_identifier="public_Jaaks_recipe_reference",
        components=tuple(InterventionComponent(identifier=d, modality="small_molecule", dose=v,
                                                dose_unit="uM", exposure_hours=72.) for d, v in zip(ids, values)))


def top_vectors(recipe):
    records = []
    for _, g in recipe.groupby("BARCODE"):
        matrix = np.array([[float(x) for x in v.split("|")] for v in g.component_doses_uM])
        choices = np.flatnonzero(np.isclose(matrix, matrix.max(axis=0), rtol=1e-10, atol=0).all(axis=1))
        if not len(choices):
            raise ValueError("no_common_componentwise_top_dose")
        records.append(g.iloc[choices[0]])
    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "composite_recipes")
    parser.add_argument("--reuse-wells", type=Path)
    args = parser.parse_args()
    out = args.output
    out.mkdir(exist_ok=False)
    _, _, menu = load_replay().load_data()
    target = set(menu.SIDM)
    source = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/original_screen_all_tissues_fitted.csv"
    design = pd.read_csv(source, usecols=["BARCODE", "SIDM", "Tissue", "LIBRARY_ID", "LIBRARY_CONC"], dtype=str).drop_duplicates()
    wanted = design[design.LIBRARY_ID.str.contains("|", regex=False) & ~design.SIDM.isin(target)]
    assert not wanted.BARCODE.duplicated().any()
    metadata = wanted.set_index("BARCODE").to_dict("index")
    parts = []
    cols = ["BARCODE", "POSITION", "SANGER_MODEL_ID", "TAG", "DRUG_ID", "CONC"]
    if args.reuse_wells:
        recipe = pd.read_csv(args.reuse_wells, dtype={"BARCODE": str, "sidm": str, "composite_id": str, "component_ids": str, "source_nominal_library_top": str})
    else:
        with zipfile.ZipFile(RAW) as archive, archive.open(archive.namelist()[0]) as handle:
            for frame in pd.read_csv(handle, usecols=cols, dtype=str, chunksize=300000):
                # No intensity or combination response column is read at all.
                z = frame[frame.BARCODE.isin(metadata) & frame.TAG.str.fullmatch(r"L\d+-D\d+-S", na=False)]
                if len(z):
                    parts.append(z)
        matched = pd.concat(parts, ignore_index=True).drop_duplicates()
        records = []
        for (barcode, position), g in matched.groupby(["BARCODE", "POSITION"]):
            meta = metadata[barcode]
            ids = sorted(meta["LIBRARY_ID"].split("|"))
            if sorted(g.DRUG_ID.tolist()) != ids:
                continue
            assert set(g.SANGER_MODEL_ID) == {meta["SIDM"]}
            vector = [float(g.loc[g.DRUG_ID.eq(d), "CONC"].iloc[0]) for d in ids]
            records.append(dict(BARCODE=barcode, POSITION=position, sidm=meta["SIDM"], tissue=meta["Tissue"],
                                composite_id=meta["LIBRARY_ID"], source_nominal_library_top=meta["LIBRARY_CONC"],
                                tag=g.TAG.iloc[0], dose_step=int(re.search(r"-D(\d+)-S", g.TAG.iloc[0]).group(1)),
                                component_ids="|".join(ids), component_doses_uM="|".join(format(x, ".12g") for x in vector)))
        recipe = pd.DataFrame(records)
    recipe.to_csv(out / "physical_well_component_doses.csv", index=False)
    top = top_vectors(recipe)
    patterns = top.groupby(["composite_id", "source_nominal_library_top", "component_ids", "component_doses_uM"], as_index=False).agg(
        historical_plates=("BARCODE", "nunique"), historical_cells=("sidm", "nunique"))
    patterns.to_csv(out / "observed_top_recipes.csv", index=False)
    note = {"status": "Direct component dose metadata recovered; no intensity, no unmixing or efficacy inference",
            "historical_composite_library_plates": len(wanted), "matched_physical_wells": len(recipe),
            "top_recipe_patterns": patterns.to_dict("records"),
            "nominal_library_scalar_must_not_be_broadcast_to_components": True,
            "limits": "Transfer source recipe only when its identity and dose-step match. Composite response is not sum/product of its component mono responses."}
    (out / "qualification.json").write_text(json.dumps(note, indent=2) + "\n")
    print(json.dumps(note, indent=2))


if __name__ == "__main__":
    main()
