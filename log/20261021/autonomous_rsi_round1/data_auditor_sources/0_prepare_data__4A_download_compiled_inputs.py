"""Download compiled inputs.

Download raw.parquet, metadata.parquet, and index.parquet from Zenodo instead of running 1A-2E.

"""  # noqa: INP001

import os
import requests

# List of files: (URL, target directory, filename)
files_to_download = [
    (
        "https://zenodo.org/records/17067683/files/cellprofiler_raw.parquet",
        "../1_snakemake/inputs/profiles/cellprofiler",
        "raw.parquet",
    ),
    (
        "https://zenodo.org/records/17067683/files/dino_raw.parquet",
        "../1_snakemake/inputs/profiles/dino",
        "raw.parquet",
    ),
    (
        "https://zenodo.org/records/17067683/files/cpcnn_raw.parquet",
        "../1_snakemake/inputs/profiles/cpcnn",
        "raw.parquet",
    ),
    (
        "https://zenodo.org/records/17067683/files/metadata.parquet",
        "../1_snakemake/inputs/metadata",
        "metadata.parquet",
    ),
    (
        "https://zenodo.org/records/17067683/files/index.parquet",
        "../1_snakemake/inputs/images",
        "index.parquet",
    ),
]

for url, dir_path, filename in files_to_download:
    # Create the directory if it doesn't exist
    os.makedirs(dir_path, exist_ok=True)

    local_path = os.path.join(dir_path, filename)

    # Stream download to handle large files
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
