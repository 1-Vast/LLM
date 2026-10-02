"""Recover failed official source links through PMC HTML and portal assets."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from research.astra.gdsc_transport import fetch, save

OUT = Path(__file__).resolve().parent
URLS = [
    ("ctrp2015_html", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4631646/"),
    ("ctrp2016_html", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4718762/"),
    ("ctrp_rest", "https://portals.broadinstitute.org/ctrp.v2.1/js/ctd2_rest.js"),
    ("ctrp_main", "https://portals.broadinstitute.org/ctrp.v2.1/js/ctd2_main.js"),
    ("ctrp_download", "https://portals.broadinstitute.org/ctrp.v2.1/files/CTRPv2.0_2015_ctd2_ExpandedDataset.zip"),
    ("pharmacogx_tree", "https://api.github.com/repos/bhklab/PharmacoGx/git/trees/master?recursive=1"),
    ("ctrp_repos", "https://api.github.com/search/repositories?q=CTRPv2&per_page=10"),
]
if (OUT / "source_receipts.json").exists():
    raise FileExistsError("use a new directory")
with ThreadPoolExecutor(max_workers=3) as pool:
    receipts = list(pool.map(lambda pair: fetch(pair[1], OUT, pair[0]), URLS))
save(OUT / "source_receipts.json", receipts)
print([{k:r.get(k) for k in ("url", "status", "bytes", "error")} for r in receipts])
