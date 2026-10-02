"""Reacquire hash-pinned originals into a new ignored cache, streaming bytes."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from research.astra.gdsc_transport import fetch, save

SOURCES = [
    ("gdsc", "https://cog.sanger.ac.uk/cancerrxgene/GDSC_release8.5/GDSC2_public_raw_data_27Oct23.csv",
     "e915be2948b174982a9b64bea5fab00f6ec8c15f7baa76bc7e2f7a7df295500e"),
    ("ctrp", "https://d1hp0ufb0xxisr.cloudfront.net/CTD2/Broad/CTRPv2.0_2015_ctd2_ExpandedDataset.zip",
     "8f62b3b5ed70cfd367cf52ce0a99884dd0a674d1a8c301474b707648689bdee3"),
]
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    receipts = []
    for name,url,expected in SOURCES:
        record = fetch(url,args.out,name)
        record["expected_sha256"] = expected
        record["matches_frozen_source"] = record.get("status") == 200 and record.get("sha256") == expected
        receipts.append(record)
        save(args.out / "source_receipts.json",receipts)
        if not record["matches_frozen_source"]:
            raise ValueError("source access/version failed; do not substitute a latest release")
    print(receipts)
