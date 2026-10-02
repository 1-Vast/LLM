"""Inspect official assay exports and fixed downstream CTRP acquisition code."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from research.astra.gdsc_transport import fetch, save

OUT = Path(__file__).resolve().parent
URLS = [
    ("ctrp_compounds", "https://portals.broadinstitute.org/ctrp.v2.1/rest/datatablecompounds"),
    ("ctrp_build", "https://portals.broadinstitute.org/ctrp.v2.1/rest/buildInfo"),
    ("ctrp_pipeline_tree", "https://api.github.com/repos/BHKLAB-DataProcessing/CTRPv2-Pharmacoset_Snakemake/git/trees/main?recursive=1"),
    ("ctrp_raw_tree", "https://api.github.com/repos/BHKLAB-DataProcessing/ctrpv2RecalculateFromRaw/git/trees/main?recursive=1"),
    ("gdsc_release", "https://cog.sanger.ac.uk/cancerrxgene/GDSC_release8.5/"),
    ("gdsc_raw_release", "https://cog.sanger.ac.uk/cancerrxgene/GDSC_release8.5/GDSC2_public_raw_data_27Oct23.csv"),
    ("ctrp2016_europepmc", "https://europepmc.org/articles/PMC4718762"),
    ("ctrp2015_europepmc", "https://europepmc.org/articles/PMC4631646"),
]
if (OUT / "source_receipts.json").exists():
    raise FileExistsError("use a new directory")
with ThreadPoolExecutor(max_workers=3) as pool:
    receipts = list(pool.map(lambda pair: fetch(pair[1], OUT, pair[0]), URLS))
save(OUT / "source_receipts.json", receipts)
print([{k:r.get(k) for k in ("url", "status", "bytes", "error")} for r in receipts])
