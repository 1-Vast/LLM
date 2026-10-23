import os

import polars as pl
from tqdm import tqdm


def process_dino_plate(input_profile_path: str) -> pl.DataFrame:
    """Reformat Dino features.

    Returns
    -------
        pl.DataFrame: A single DataFrame with all the rows from the input DataFrames concatenated vertically.

    """
    channels = [
        "hoechst_33342",
        "phenovue_fluor_488",
        "wga555/phalloidin568",
        "cp_nuclei_acid_512",
        "mito_641_narrow",
        "brightfield",
    ]
    channel_nms = [
        "DNA",
        "ER",
        "AGP",
        "RNA",
        "Mito",
        "Brightfield",
    ]
    feat_names = []
    for nm in channel_nms:
        feat_names += [f"{nm}_{i:03}" for i in range(1, 769)]
    all_cols = ["Metadata_well_id", *feat_names]

    # Process embeddings
    dat = pl.read_parquet(input_profile_path)
    data = []
    for i in range(dat.shape[0]):
        features = []
        for channel in channels:
            features += dat.select(channel)[i].item().to_list()
        data.append(features)

    data = pl.DataFrame(data)
    data = data.transpose()
    data.columns = feat_names

    data = data.with_columns(
        (pl.Series(name="Metadata_well_id", values=dat.select("well_id").to_series())),
    )
    return data.select(all_cols)


def main() -> None:
    """Format Dino embeddings.

    Merge Dino embeddings from each plate into one file and add metadata.

    """
    input_profile_path = "../1_snakemake/inputs/profiles/dino/plates"
    meta_path = "../1_snakemake/inputs/metadata/metadata.parquet"
    output_profile_path = "../1_snakemake/inputs/profiles/dino/raw.parquet"

    meta = pl.read_parquet(meta_path)

    profiles = []
    plates = os.listdir(input_profile_path)
    for plate in tqdm(plates):
        prof_path = f"{input_profile_path}/{plate}"
        profiles.append(process_dino_plate(prof_path))

    data = pl.concat(profiles, how="vertical")
    data = data.join(meta, on="Metadata_well_id")

    # Compute median feature value per well
    meta_cols = [i for i in data.columns if "Metadata_" in i]
    feat_cols = [i for i in data.columns if "Metadata_" not in i]

    data = data.group_by(["Metadata_Plate", "Metadata_Well"]).agg([
        pl.col(meta_cols)
        .exclude(["Metadata_well_id", "Metadata_Plate", "Metadata_Well"])
        .first(),
        pl.median(feat_cols),
    ])

    data.write_parquet(output_profile_path)


if __name__ == "__main__":
    main()
