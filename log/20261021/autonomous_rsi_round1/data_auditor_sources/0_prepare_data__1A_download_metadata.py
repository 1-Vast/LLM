"""Download Axiom metadata.

Download all Axiom platemap and biochem metadata.

"""  # noqa: INP001

import re
from pathlib import Path

from sh import aws


def main() -> None:
    """Download metadata.

    Read in index file, download data.

    """
    aws_path = "s3://cellpainting-gallery/cpg0037-oasis/axiom/workspace/metadata"
    local_meta = "../1_snakemake/inputs/metadata"
    batches = ["prod_25", "prod_26", "prod_27", "prod_30"]

    Path(f"{local_meta}/metadata").mkdir(parents=True, exist_ok=True)
    Path(f"{local_meta}/biochem").mkdir(parents=True, exist_ok=True)

    # get metadata (both biochem.parquet and metadata.parquet)
    for batch in batches:
        batch_path = f"{aws_path}/{batch}/"
        aws_output = aws("s3", "ls", batch_path, "--no-sign-request")
        plates = re.findall(r"plate_\d{8}", aws_output)

        for plate in plates:
            metadata_file = Path(f"{local_meta}/metadata/metadata_{plate}.parquet")
            biochem_file = Path(f"{local_meta}/biochem/biochem_{plate}.parquet")

            # only download if the files doesn't already exist
            if not metadata_file.exists():
                aws("s3", "cp", f"{batch_path}{plate}/metadata.parquet", str(metadata_file), "--no-sign-request")

            if not biochem_file.exists():
                aws("s3", "cp", f"{batch_path}{plate}/biochem.parquet", str(biochem_file), "--no-sign-request")


if __name__ == "__main__":
    main()
