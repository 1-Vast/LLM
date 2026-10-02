"""Fetch original protocol articles and official CTRP repository listings."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from research.astra.gdsc_transport import fetch, save

OUT = Path(__file__).resolve().parent
URLS = [
    ("ctrp2015", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4631646/fullTextXML"),
    ("ctrp2016", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4718762/fullTextXML"),
    ("replicability", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5580432/fullTextXML"),
    ("broad_ftp", "https://ftp.broadinstitute.org/pub/ctd2/"),
    ("broad_ftp_supplement", "https://ftp.broadinstitute.org/pub/ctd2/SupplementaryFiles/"),
    ("ctd2_broad", "https://ocg.cancer.gov/programs/ctd2/data-portal/2015"),
]
if (OUT / "source_receipts.json").exists():
    raise FileExistsError("use a new directory; do not overwrite source receipts")
with ThreadPoolExecutor(max_workers=3) as pool:
    receipts = list(pool.map(lambda pair: fetch(pair[1], OUT, pair[0]), URLS))
save(OUT / "source_receipts.json", receipts)
print(receipts)
