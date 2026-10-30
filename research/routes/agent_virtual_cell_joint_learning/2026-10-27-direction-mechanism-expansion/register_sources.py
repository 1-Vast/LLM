"""Register already identified primary papers; no data/model execution."""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LIB = HERE.parents[1] / "reference"
TOOL = pathlib.Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")
SCOPES = {
    "10.1038/s41467-026-72903-w": "Original JATS: Results sections 4 and 7, Methods section 14; mean effects, cross-study shifts and grouped validation. Section 20 partial. Not reproduced.",
    "10.3390/genes17070816": "Original JATS: Methods section 5 first 2200 characters, Limitations section 14; control-dependent calibration and scope restrictions. Not reproduced.",
    "10.1186/s13321-026-01242-1": "Original JATS: Methods section 8 first 4200 of 4927 characters and section 9; random-triple splits and distinct synergy definitions. Not reproduced.",
}


def run(*args):
    proc = subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    if proc.returncode:
        raise SystemExit(proc.returncode)


for meta_path in sorted((HERE / "primary").glob("*.json")):
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if "resultList" not in meta:
        continue
    paper = meta["resultList"]["result"][0]
    doi = paper["doi"]
    pid = "doi-" + doi.replace("/", "-")
    run("record", str(LIB), "paper", pid,
        "title=" + paper["title"], "authors=" + paper["authorString"],
        "doi=" + doi, "type_status=journal_article", "alt_id=" + paper["pmcid"],
        "first_public_date=" + paper["firstPublicationDate"],
        "formal_date=" + paper["electronicPublicationDate"],
        "date_basis=Official Europe PMC core metadata retrieved 2026-10-27",
        "landing_page=https://doi.org/" + doi, "reading_level=P",
        "reading_scope=" + SCOPES[doi],
        "note=Original official full JATS and SHA256 receipt retained in research/2026-10-27-direction-mechanism-expansion/primary; XML is not counted as library PDF/HTML.")
    run("record", str(LIB), "code", pid, "download_status=not_verified",
        "note=Code availability not fully verified in this bounded mechanism-development round; no execution.")
    run("paper", str(LIB), pid, "https://pmc.ncbi.nlm.nih.gov/articles/" + paper["pmcid"] + "/", "--html", "--version", "PMC-published")
