"""Register already acquired originals through the library owner, no HTTP."""
import csv
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
lib = root.parent.parent / "reference"
owner = Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")
plain = lambda element: " ".join("".join(element.itertext()).split()) if element is not None else ""

def call(*args):
    run = subprocess.run([sys.executable, str(owner), *map(str, args)],
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert run.returncode == 0, run.stderr or run.stdout
    return run.stdout

sources = [
    ("p3_transition.xml", "Selected original methods: treatment history, separate dishes, functional endpoints and compartment-model prior; evidence/evidence.md", "PMC12673137"),
    ("p4_collateral_sarcoma.xml", "Selected original methods: temporal collateral sensitivity, CTG/direct-count distinction, replicate/dose limitations; evidence/evidence.md", "PMC12334625"),
    ("p5_negative_hysteresis.xml", "Original Sec3-8,13-16 and data availability: switch/recovery/genetic controls and OD-CFU/source-selection limits; evidence/evidence.md", "PMC13187417"),
]
prior = root / "evidence/p6_hysteresis_prior.xml"
if prior.exists():
    sources.append((prior.name, "Selected original passages on cellular hysteresis, selection/induction and growth/CFU controls; evidence/prior_hysteresis_check.md", "PMC6166819"))
for name, scope, pmc in sources:
    source = root / "evidence" / name
    article = ET.parse(source).getroot()
    doi = next(plain(e) for e in article.findall(".//article-meta/article-id") if e.get("pub-id-type") == "doi")
    pid = "doi-" + doi.replace("/", "-")
    date = article.find(".//article-meta/pub-date")
    parts = [plain(date.find(k)) for k in ["year", "month", "day"]]
    formal = "-".join([parts[0], parts[1].zfill(2), parts[2].zfill(2)]) if all(parts) else ""
    title = plain(article.find(".//article-title"))
    author = article.find(".//contrib[@contrib-type='author']/name")
    authors = plain(author.find("surname")) + ", " + plain(author.find("given-names")) if author is not None else ""
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML"
    call("record", lib, "paper", pid, "title=" + title, "authors=" + authors,
         "doi=" + doi, "formal_date=" + formal, "type_status=published journal original",
         "landing_page=https://doi.org/" + doi, "date_basis=original published JATS pub-date")
    call("paper", lib, pid, "--file", source, "--role", "supplement", "--version", "published-primary-JATS")
    with (lib / "papers.tsv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    stored = next(r for r in rows if r["paper_id"] == pid and r["local_path"].endswith("supp-" + name))
    call("record", lib, "paper", pid, "--path", stored["local_path"],
         "source_url=" + url, "reading_level=P", "reading_scope=" + scope,
         "identity_check=original JATS title and DOI inspected",
         "note=Main published JATS is stored in a supplement slot because owner accepts main PDF/HTML only; original bytes preserved. Actual acquisition provenance in episode evidence requests. Partial reading, not author reproduction.")
    print(pid, stored["local_path"])

pid = "doi-10.1063-1.4930551"
source = root / "scout/Dyre_2015_1504.05930v4.pdf"
call("record", lib, "paper", pid,
     "title=Narayanaswamy's 1971 aging theory and material time", "authors=Dyre, Jeppe C.",
     "doi=10.1063/1.4930551", "alt_id=arxiv:1504.05930v4",
     "type_status=published journal article; inspected arXiv v4", "formal_date=",
     "date_basis=Publication year2015 from journal/arXiv source; exact formal publication day not verified; internal PDF Dated August14,2021 does not establish a new version")
call("paper", lib, pid, "--file", source, "--version", "arxiv-1504.05930v4")
call("record", lib, "paper", pid, "source_url=https://arxiv.org/pdf/1504.05930v4",
     "reading_level=P", "reading_scope=Scout pp1-6,7-10,11Appendix; exact passage locators in episode scout/source_map.md; bibliography/algebra not independently reproduced",
     "note=Older foundational donor, outside 2025-2026 latest-paper window. Original query/download receipts in episode. No biological transfer validated.")
print(pid)
