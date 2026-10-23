"""Download image index.

Get files that map image names to metadata.

""" # noqa: INP001

from pathlib import Path

import polars as pl


def main() -> None:
    """Format CellProfiler profiles.

    Merge profiles from each plate into one file and add metadata.

    """
    input_index_dir = "../1_snakemake/inputs/images/load_data_csv"
    Path(input_index_dir).mkdir(parents=True, exist_ok=True)

    output_index_path = "../1_snakemake/inputs/images/index.parquet"

    plate_index = []
    plates = [p for p in Path(input_index_dir).iterdir() if p.is_file() and "plate_" in p.name]

    select_cols = [
        "Metadata_Plate",
        "Metadata_Well",
        "Metadata_Site",
        "URL_OrigBrightfield",
        "URL_OrigRNA",
        "URL_OrigDNA",
        "URL_OrigMito",
        "URL_OrigER",
        "URL_OrigAGP",
    ]

    # Read in data for each plate
    for plate in plates:
        plate_temp = pl.read_csv(plate, infer_schema_length=10000).select(select_cols)
        plate_index.append(plate_temp)

    # Concat together
    index = pl.concat(plate_index, how="vertical_relaxed")

    index = index.with_columns(
        pl.when(pl.col("URL_OrigBrightfield").str.contains("prod_25"))
        .then(pl.lit("prod_25"))
        .when(pl.col("URL_OrigBrightfield").str.contains("prod_26"))
        .then(pl.lit("prod_26"))
        .when(pl.col("URL_OrigBrightfield").str.contains("prod_27"))
        .then(pl.lit("prod_27"))
        .when(pl.col("URL_OrigBrightfield").str.contains("prod_30"))
        .then(pl.lit("prod_30"))
        .alias("Metadata_Batch"),
    )

    index = index.rename({
        "URL_OrigBrightfield": "Brightfield",
        "URL_OrigRNA": "RNA",
        "URL_OrigDNA": "DNA",
        "URL_OrigMito": "Mito",
        "URL_OrigER": "ER",
        "URL_OrigAGP": "AGP",
    })

    index = index.melt(
        id_vars=["Metadata_Batch", "Metadata_Plate", "Metadata_Well", "Metadata_Site"],
        value_vars=["Brightfield", "RNA", "DNA", "Mito", "ER", "AGP"],
        variable_name="Channel",
        value_name="Filename",
    )

    index.write_parquet(output_index_path)


if __name__ == "__main__":
    main()
