"""Download load_data_csv.

Use AWS cli to download files that give map plate and well IDs to image names.

"""  # noqa: INP001

import re

from sh import aws


def main() -> None:
    """Download data.

    Read in index file, download data.

    """
    aws_path = "s3://cellpainting-gallery/cpg0037-oasis/axiom/workspace/load_data_csv"
    batches = ["prod_25", "prod_26", "prod_27", "prod_30"]

    index_dir = "../1_snakemake/inputs/images/load_data_csv"

    for batch in batches:
        batch_path = f"{aws_path}/{batch}/"
        aws_output = aws("s3", "ls", batch_path, "--no-sign-request")
        plates = re.findall(r"plate_\d{8}", aws_output)

        for plate in plates:
            aws("s3", "cp", f"{batch_path}{plate}/load_data.csv", f"{index_dir}/{plate}.csv", "--no-sign-request")


if __name__ == "__main__":
    main()
