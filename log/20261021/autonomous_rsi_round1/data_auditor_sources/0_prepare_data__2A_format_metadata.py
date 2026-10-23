import os

import numpy as np
import polars as pl
from tqdm import tqdm

meta_keep = [
    "well_id",
    "source",
    "plate",
    "compound_concentration_um",
    "compound_name",
    "compound_target",
    "compound_pathway",
    "compound_research_area",
    "compound_clinical_information",
    "compound_url",
    "compound_scode",
    "well",
    "row",
    "col",
    "mtt_lumi",
    "ldh_abs_signal",
    "ldh_abs_background",
    "ldh_abs",
    "mtt_normalized",
    "ldh_normalized",
    "mtt_ridge_norm",
    "ldh_ridge_norm",
    "OASIS_ID",
]


def process_meta(input_meta_path: str, meta_nms: list) -> pl.DataFrame:
    """Process metadata.

    Select columns of interest and rename.



    """
    meta = pl.read_parquet(input_meta_path)
    missing_cols = [i for i in meta_keep if i not in meta.columns]
    for mc in missing_cols:
        meta = meta.with_columns(
            pl.lit(None).alias(mc),
        )
    meta = meta.select(meta_keep)
    meta.columns = meta_nms

    return meta


def main() -> None:
    """Format metadata.

    Merge metadata from each plate into one file.

    """
    # Process metadata
    meta_nms = [f"Metadata_{i}" for i in meta_keep]
    meta_path = "../1_snakemake/inputs/metadata/biochem"
    cc_path = "../1_snakemake/inputs/metadata/cc.parquet"
    meta = []

    plates = os.listdir(meta_path)
    for plate in tqdm(plates):
        plate_path = f"{meta_path}/{plate}"
        meta.append(process_meta(plate_path, meta_nms))

    meta = pl.concat(meta, how="vertical_relaxed")
    meta = meta.rename({
        "Metadata_plate": "Metadata_Plate",
        "Metadata_well": "Metadata_Well",
        "Metadata_compound_name": "Metadata_Compound",
        "Metadata_compound_concentration_um": "Metadata_Concentration",
    }).with_columns(
        pl.concat_str(["Metadata_Compound", "Metadata_Concentration"], separator="_").alias("Metadata_Perturbation"),
        pl.col("Metadata_Well")
        .map_elements(lambda well: well if len(well) == 3 else f"{well[0]}0{well[1]}", return_dtype=pl.Utf8)
        .alias("Metadata_Well"),
    )

    compounds = meta.select("Metadata_Compound").to_series().unique().to_list()
    compounds = [i for i in compounds if i != "DMSO"]
    meta_log10 = meta.filter(pl.col("Metadata_Compound") == "DMSO").with_columns(
        pl.lit(0).cast(pl.Float64).alias("Metadata_Log10Conc"),
    )

    for compound in compounds:
        temp = meta.filter(pl.col("Metadata_Compound") == compound)
        concs = temp.select(pl.col("Metadata_Concentration")).to_series().sort().unique().to_list()
        shift_val = np.abs(np.log10(concs[0] / 3))

        temp = temp.with_columns(
            (pl.col("Metadata_Concentration").log10() + shift_val).alias("Metadata_Log10Conc"),
        )

        meta_log10 = pl.concat([meta_log10, temp], how="vertical")

    cc = pl.read_parquet(cc_path)
    meta_log10 = meta_log10.join(cc, on=["Metadata_Plate", "Metadata_Well"])

    # Filter out plates with different microscope
    meta_log10 = meta_log10.filter(
        ~pl.col("Metadata_Plate").is_in(["plate_41002698", "plate_41002695", "plate_41002696"]),
    )

    meta_log10.write_parquet("../1_snakemake/inputs/metadata/metadata.parquet")


if __name__ == "__main__":
    main()
