"""Recover the CTRP download route from immutable pipeline source blobs."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from research.astra.gdsc_transport import fetch, save

OUT = Path(__file__).resolve().parent
REPO = "https://api.github.com/repos/BHKLAB-DataProcessing/CTRPv2-Pharmacoset_Snakemake/"
URLS = [
    ("download_rule", REPO + "git/blobs/9e7e14db974d5f4f8913f93681ccd8384b24abd1"),
    ("pipeline_config", REPO + "git/blobs/7aac549f394d608ab7c25fcf0ab67d893dd43316"),
    ("pipeline_readme", REPO + "git/blobs/415d11c3146ffa957a18867fb6ade9c7fa74c779"),
    ("pipeline_commit", REPO + "commits/main"),
    ("ctrp_raw_repo", "https://api.github.com/repos/BHKLAB-DataProcessing/ctrpv2RecalculateFromRaw"),
    ("ccle_2012", "https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&query=DOI:10.1038/nature11003&resultType=core"),
]
if (OUT / "source_receipts.json").exists():
    raise FileExistsError("use a new directory")
with ThreadPoolExecutor(max_workers=3) as pool:
    receipts = list(pool.map(lambda pair: fetch(pair[1], OUT, pair[0]), URLS))
save(OUT / "source_receipts.json", receipts)
print([{k:r.get(k) for k in ("url", "status", "bytes", "error")} for r in receipts])
