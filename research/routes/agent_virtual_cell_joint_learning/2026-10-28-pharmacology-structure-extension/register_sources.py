"""Register inspected original sources through the existing library CLI."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
lib = root.parents[1] / "reference"
cli = Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")
before = {name: hashlib.sha256((lib / name).read_bytes()).hexdigest() for name in ("papers.tsv", "repositories.tsv")}
receipts = []

def call(*args):
    result = subprocess.run([sys.executable, str(cli), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    receipts.append({"arguments": list(map(str, args)), "exit_code": result.returncode,
                     "stdout": result.stdout, "stderr": result.stderr})
    if result.returncode:
        raise RuntimeError(result.stderr)

items = [
    ("bcl11b", "2026-09-09", "sec5P2-P5, sec9P3, sec19P1, sec21P1, sec29P1, Fig2 and Fig5 legends; selected other methods via evidence investigator. Not whole paper or SI.",
     "State sorting, genetic KO/rescue, washout/replating and rechallenge evidence. Full TNF x maintained-rescue x Doxo cross unverified; SI timeout/official403. CC BY-NC4.0.", "Author Data/code availability states no original code; no public original-code repository claimed."),
    ("myst", "2026-05-13", "Sec3/5/6/7/10/13/27-30 and Data/Code availability selected passages; root Sec6P1/Sec7P2/Sec28P1/Sec30P1 independently inspected. Not full manuscript or SI.",
     "Six-compound proximal dose profiles do not supply six-compound x background matched function. NCI60 text/method dose conflict preserved. CC BY4.0.", "Code availability points to Zenodo15238967 for structure/interface prediction; not retrieved here and not an established functional-screen code package."),
    ("clonal_melanoma", "2026-03-03", "Evidence investigator Sec4-7/30-32 and data availability; selected original protocols/lineage boundary, not whole manuscript/SI.",
     "Continuous treatment lineage evidence; washout/rechallenge remains unverified. Three experimental replicates pooled for some scRNA; barcode transcript frequency is not absolute viable count. CC BY4.0.", "Original article points to github.com/Yeqing95/MeRLin; URL noted, repository/version/license not retrieved or verified.")
]
for name, date, scope, note, code_note in items:
    source = root / "sources/evidence_p7" / (name + ".xml")
    article = ET.fromstring(source.read_bytes()).find("./front/article-meta")
    doi = next(x.text for x in article.findall("article-id") if x.attrib.get("pub-id-type") == "doi")
    pmcid = next(x.text for x in article.findall("article-id") if x.attrib.get("pub-id-type") == "pmcid")
    pid = "doi-" + doi.replace("/", "-")
    title = "".join(article.find("title-group/article-title").itertext())
    author = article.find("contrib-group/contrib/name")
    authors = author.findtext("given-names", "") + " " + author.findtext("surname", "") + "; et al."
    url = json.loads((source.parent / (name + "_receipt.json")).read_text(encoding="utf-8"))["url"]
    call("record", lib, "paper", pid, "title=" + title, "authors=" + authors,
         "doi=" + doi, "alt_id=" + pmcid, "type_status=primary research; peer reviewed",
         "formal_date=" + date, "date_basis=Inspected original JATS pub-date; selected 2026 original research",
         "landing_page=https://doi.org/" + doi, "reading_level=P", "reading_scope=" + scope,
         "note=Main article stored as original JATS in supplement-format slot; main PDF/HTML remains pending. " + note)
    call("paper", lib, pid, "--file", source, "--role", "supplement", "--version", "primary-original-jats-xml")
    path = "papers/" + pid + "/supp-" + name + ".xml"
    call("record", lib, "paper", pid, "--path", path, "source_url=" + url,
         "reading_level=P", "reading_scope=" + scope,
         "note=Original main-article XML, NOT supplementary text. Format slot is a library-tool limitation. Actual source receipt in episode sources/evidence_p7. " + note)
    call("record", lib, "code", pid, "download_status=not_verified", "note=" + code_note)

pid = "doi-10.1038-s41467-024-54728-7"
source = root / "sources/punzi/41467_2024_54728_MOESM8_ESM.zip"
call("paper", lib, pid, "--file", source, "--role", "supplement", "--version", "official-MOESM8-source-data")
url = json.loads((source.parent / "receipt.json").read_text(encoding="utf-8"))["url"]
call("record", lib, "paper", pid, "--path", "papers/" + pid + "/supp-" + source.name,
     "source_url=" + url, "reading_level=P",
     "reading_scope=ZIP member list and Extended Data5 workbook metadata only: sheet5c A1:E4, CTRL at A1 and four drug/holiday labels B1:E1; numeric cells and formulas not exported/read for effect.",
     "note=Original publisher Source Data ZIP; outcome numbers unopened. Four drug/holiday labels do not establish crossed rechallenge, dose, denominator or culture identity.")
after = {name: hashlib.sha256((lib / name).read_bytes()).hexdigest() for name in before}
(root / "library_registration.json").write_text(json.dumps({"before_sha256": before, "after_sha256": after, "commands": receipts}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"new_papers": 3, "new_files": 4, "commands": len(receipts), "status": "registered; verify still required"}))
