import os

import polars as pl
from tqdm import tqdm


def main() -> None:
    """Format CPCNN embeddings.

    Merge CPCNN embeddings from each plate into one file and add metadata.

    """
    input_profile_path = "../1_snakemake/inputs/profiles/cpcnn/plates"
    meta_path = "../1_snakemake/inputs/metadata/metadata.parquet"
    output_profile_path = "../1_snakemake/inputs/profiles/cpcnn/raw.parquet"

    meta = pl.read_parquet(meta_path)

    profiles = []
    plates = os.listdir(input_profile_path)
    for plate in tqdm(plates):
        prof_path = f"{input_profile_path}/{plate}"
        dat = pl.scan_parquet(prof_path)

        meta_cols = [i for i in dat.columns if "Metadata_" in i]
        feat_cols = [i for i in dat.columns if "Metadata_" not in i]

        dat = (
            dat.group_by(["Metadata_Plate", "Metadata_Well"])
            .agg([
                pl.col(meta_cols)
                .exclude(["Metadata_Plate", "Metadata_Well"])
                .first(),
                pl.median(feat_cols),
            ])
            .collect()
        )
        profiles.append(dat)

    data = pl.concat(profiles, how="vertical")
    data = data.join(meta, on=["Metadata_Plate", "Metadata_Well"])
    data.write_parquet(output_profile_path)


if __name__ == "__main__":
    main()
