"""Download Axiom dino embeddings.

Use CPG index to download all Axiom Dino profiles.

"""  # noqa: INP001

import re

from sh import aws


def main() -> None:
    """Download data.

    Read in index file, download data.

    """
    aws_path = "s3://cellpainting-gallery/cpg0037-oasis/axiom/workspace_dl/profiles/dinov2_b_vitl14_fieldnorm_825c11"
    batches = ["prod_25", "prod_26", "prod_27", "prod_30"]

    prof_dir = "../1_snakemake/inputs/profiles/dino/plates"

    # get Dino embedding paths
    for batch in batches:
        batch_path = f"{aws_path}/{batch}/"
        aws_output = aws("s3", "ls", batch_path, "--no-sign-request")
        plates = re.findall(r"plate_\d{8}", aws_output)

        for plate in plates:
            aws("s3", "cp", f"{batch_path}{plate}/{plate}.parquet", f"{prof_dir}/{plate}.parquet", "--no-sign-request")


if __name__ == "__main__":
    main()
