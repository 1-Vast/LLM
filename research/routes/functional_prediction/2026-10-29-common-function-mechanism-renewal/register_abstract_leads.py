"""Register relevant already-read abstract leads through the library owner."""
from pathlib import Path
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

episode = Path(__file__).resolve().parent
library = episode.parent.parent / "reference"
owner = Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")
registered = []

def record(pid, fields):
    run = subprocess.run([sys.executable, str(owner), "record", str(library),
                          "paper", pid, *[f"{k}={v}" for k, v in fields.items()]],
                         capture_output=True, text=True, encoding="utf-8", timeout=30)
    if run.returncode:
        raise RuntimeError(run.stderr or run.stdout)
    registered.append(pid)

targets = {"10.64898/2026.10.23.761350", "10.64898/2026.09.17.752270"}
for path in (episode / "evidence").glob("q*.json"):
    data = json.loads(path.read_text(encoding="utf-8"))
    for result in data["resultList"]["result"]:
        doi = result.get("doi", "")
        if doi not in targets:
            continue
        record("doi-" + doi.replace("/", "-"), {
            "title": result["title"].replace("<i>", "").replace("</i>", ""),
            "authors": result.get("authorString", ""), "doi": doi,
            "type_status": "preprint; EuropePMC metadata and abstract only",
            "first_public_date": result.get("firstPublicationDate", ""),
            "date_basis": "EuropePMC firstPublicationDate, not independently checked against original preprint version history",
            "formal_date": "", "landing_page": "https://doi.org/" + doi,
            "source_url": "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            "download_status": "abstract_only", "reading_level": "A",
            "reading_scope": "Complete supplied abstract in " + str(path.relative_to(episode)) + "; no original methods or empirical reproduction",
            "note": "Relevant recency/prior lead; original request URL and saved response identity in episode evidence receipts. No paper/code/data acquisition; method-level overlap unresolved.",
        })

ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
root = ET.parse(episode / "scout/query_arxiv.xml").getroot()
for entry in root.findall("a:entry", ns):
    aid = entry.findtext("a:id", namespaces=ns).rsplit("/", 1)[-1]
    if aid == "1504.05930v4":
        continue  # already registered with the complete original PDF
    doi = entry.findtext("x:doi", default="", namespaces=ns)
    pid = "doi-" + doi.replace("/", "-") if doi else "arxiv-" + aid.split("v")[0]
    fields = {
        "title": " ".join(entry.findtext("a:title", namespaces=ns).split()),
        "authors": "; ".join(e.findtext("a:name", namespaces=ns) for e in entry.findall("a:author", ns)),
        "doi": doi, "alt_id": "arxiv:" + aid,
        "first_public_date": entry.findtext("a:published", namespaces=ns)[:10],
        "formal_date": "", "date_basis": "Native arXiv Atom first published date; exact journal publication day not inspected",
        "type_status": "source-native abstract lead; formal journal identity only when supplied by Atom",
        "landing_page": "https://arxiv.org/abs/" + aid,
        "source_url": "https://export.arxiv.org/api/query",
        "download_status": "abstract_only", "reading_level": "A",
        "reading_scope": "Complete native Atom abstract in scout/query_arxiv.xml; no original method reading",
        "note": "Relevant neutral-scout lead, not a validated biological transfer. Exact query URL and version dates in scout receipts/source map; code not checked.",
    }
    if aid == "2109.11832v3":
        fields["failure_reason"] = "4,500,000-byte capped original PDF has no EOF and zero parseable pages; not a valid library full text, no retry"
    record(pid, fields)

(episode / "library_leads_registered.json").write_text(
    json.dumps({"new_http_requests": 0, "registered_abstract_only": registered}, indent=2) + "\n", encoding="utf-8")
print(json.dumps(registered))
