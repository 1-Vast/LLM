"""Acquire original CTRPv2 archive through its recovered CDN, not fitted summaries."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from research.astra.gdsc_transport import fetch, save

OUT = Path(__file__).resolve().parent
CACHE = ROOT / "tmp/gdsc_transport_sources_v5"
CACHE.mkdir(parents=True, exist_ok=False)
URLS = [
    ("ctrp_archive", "https://d1hp0ufb0xxisr.cloudfront.net/CTD2/Broad/CTRPv2.0_2015_ctd2_ExpandedDataset.zip", CACHE),
    ("ccle_raw", "https://data.broadinstitute.org/ccle/CCLE_NP24.2009_Drug_data_2015.02.24.csv", OUT),
    ("ctrp_oa", "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC4718762", OUT),
    ("ctrp2015_oa", "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC4631646", OUT),
]
if (OUT / "source_receipts.json").exists():
    raise FileExistsError("use a new directory")
def acquire(item):
    name, url, folder = item
    record = fetch(url, folder, name)
    record["storage_directory"] = folder.relative_to(ROOT).as_posix()
    return record
with ThreadPoolExecutor(max_workers=3) as pool:
    receipts = list(pool.map(acquire, URLS))
save(OUT / "source_receipts.json", receipts)
print([{k:r.get(k) for k in ("url", "status", "bytes", "error")} for r in receipts])
