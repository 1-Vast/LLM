"""Register the inspected originals using the installed library owner; no network."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from xml.etree import ElementTree as ET

EPISODE = Path(__file__).resolve().parent
LIBRARY = EPISODE.parents[1] / "reference"
OWNER = Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")
receipts = []


def run(*args):
    result = subprocess.run([sys.executable, str(OWNER), *map(str, args)],
                            capture_output=True, text=True, encoding="utf-8")
    receipts.append({"args": list(map(str, args)), "returncode": result.returncode,
                     "stdout": result.stdout, "stderr": result.stderr})
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


items = []
for path in sorted((EPISODE / "evidence_worker").glob("*.xml")):
    tree = ET.fromstring(path.read_bytes())
    ids = {e.get("pub-id-type"): "".join(e.itertext())
           for e in tree.findall(".//front/article-meta/article-id")}
    title = " ".join("".join(tree.find(".//article-title").itertext()).split())
    authors = "; ".join(" ".join("".join(e.itertext()).split())
                        for e in tree.findall(".//front/article-meta/contrib-group/contrib/name"))
    pid = "doi-" + re.sub(r"[^A-Za-z0-9._-]", "-", ids["doi"])
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/" + ids["pmcid"] + "/fullTextXML"
    items.append((pid, title, authors, ids["doi"], ids["pmcid"], path, url, "published", "supplement"))

scout_ids = {"robotics": "2505.14266", "residual": "2603.03785", "causal": "2608.15645",
             "cv": "2410.22187", "nlp": "2601.13734"}
for name, aid in scout_ids.items():
    path = EPISODE / "scout" / (name + ".html")
    html = path.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip()
    authors = "; ".join(re.findall(r'<meta name="citation_author" content="([^"]+)"', html))
    items.append(("arxiv-" + aid, title, authors, "", "arXiv:" + aid, path,
                  "https://arxiv.org/html/" + aid + ("v2" if name == "nlp" else "v1"),
                  "preprint; cv source also WACV2025", "main"))

palmer = EPISODE / "evidence_worker" / "pair16_palmer_pmc.html"
if palmer.exists():
    items.append(("doi-10.1016-j.cell.2017.11.009",
                  "Combination Cancer Therapy Can Confer Benefit via Patient-to-Patient Variability without Drug Additivity or Synergy",
                  "Adam C. Palmer; Peter K. Sorger", "10.1016/j.cell.2017.11.009", "PMC5741091",
                  palmer, "https://pmc.ncbi.nlm.nih.gov/articles/PMC5741091/", "published; foundational prior", "main"))

before = list(csv.DictReader((LIBRARY / "papers.tsv").open(encoding="utf-8-sig"), delimiter="\t"))
for pid, title, authors, doi, aid, path, url, status, role in items:
    old = [r for r in before if r["paper_id"] == pid]
    if not old:
        run("record", LIBRARY, "paper", pid, "title=" + title, "authors=" + authors,
            "doi=" + doi, "alt_id=" + aid, "type_status=" + status, "landing_page=" + url,
            "candidate_url=" + url, "date_basis=Original document identity; precise version in episode source notes")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if not any(r["sha256"] == sha for r in old):
        args = ["paper", LIBRARY, pid, "--file", path, "--version", "2026-10-29 inspected original"]
        args += ["--html"] if role == "main" else ["--role", role]
        run(*args)
    current = list(csv.DictReader((LIBRARY / "papers.tsv").open(encoding="utf-8-sig"), delimiter="\t"))
    stored = next(r for r in current if r["paper_id"] == pid and r["sha256"] == sha)
    note = ("Original main JATS, NOT supplementary experiments; stored in supplement slot because owner only "
            "supports PDF/HTML in main slot. " if role == "supplement" else "Original arXiv HTML. ")
    note += "Partial method reading only; see 2026-10-29-common-screen-colearning evidence_worker/evidence.md or scout/source_map.md. No author code executed."
    run("record", LIBRARY, "paper", pid, "--path", stored["local_path"], "source_url=" + url,
        "reading_level=P", "reading_scope=Exact selected passages documented in episode; not entire paper", "note=" + note)

receipt_path = EPISODE / "catalog_receipt.json"
previous = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else None
receipt_path.write_text(json.dumps({"items": len(items), "operations": receipts,
                                    "previous_receipt": previous},
                                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"inspected_originals_registered": len(items), "owner_operations": len(receipts)}))
