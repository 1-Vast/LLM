"""Register primary novelty threats already found by the independent challenger."""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LIB = HERE.parents[1] / "reference"
TOOL = pathlib.Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")
SCOPES = {
    "10.1016/j.cell.2012.03.031": ("A", "Official full abstract only; XML HTTP500 and recovered HTML was a captcha page. Sequence/state-rewiring prior, not full-method verification."),
    "10.1371/journal.pone.0063583": ("P", "Original JATS: abstract, Compound Treatment, Comparison of Assay Formats, Time Dependence of Inter-assay Format Variation; paired assay failures. Not reproduced."),
    "10.1016/j.chembiol.2017.10.010": ("P", "Original JATS: abstract, engagement/activity and ATP-interference sections inspected by independent challenger; not all methods/supplements. First online 2017, issue 2018."),
    "10.1016/j.mcpro.2025.100963": ("P", "Original JATS: abstract, Experimental Design and Statistical Rationale, Discussion; averaged conformation/complex engagement caveat. Not reproduced."),
}
seen = set()
for path in sorted((HERE / "search" / "p4_challenge").glob("*_response.json")):
    for row in json.loads(path.read_text(encoding="utf-8")).get("resultList", {}).get("result", []):
        doi = row.get("doi")
        if doi not in SCOPES or doi in seen:
            continue
        seen.add(doi)
        pid = "doi-" + doi.replace("/", "-")
        level, scope = SCOPES[doi]
        fields = ["title=" + row["title"], "authors=" + row["authorString"], "doi=" + doi,
                  "alt_id=" + row["pmcid"], "type_status=journal_article",
                  "first_public_date=" + row["firstPublicationDate"],
                  "formal_date=" + row.get("electronicPublicationDate", ""),
                  "date_basis=Official Europe PMC metadata retrieved 2026-10-27; older item retained as direct novelty threat",
                  "landing_page=https://doi.org/" + doi, "reading_level=" + level, "reading_scope=" + scope,
                  "note=Primary source and provenance in research/2026-10-27-direction-mechanism-expansion/primary/p4_challenge; no experiments or reproduction."]
        subprocess.run([sys.executable, str(TOOL), "record", str(LIB), "paper", pid, *fields], check=True)
        subprocess.run([sys.executable, str(TOOL), "record", str(LIB), "code", pid,
                        "download_status=not_verified", "note=No official software availability verified in this bounded source check."], check=True)
        if doi == "10.1016/j.cell.2012.03.031":
            subprocess.run([sys.executable, str(TOOL), "record", str(LIB), "paper", pid,
                            "download_status=abstract_only", "failure_reason=Official XML HTTP500; recovered PMC HTML was captcha, not a full paper; no bypass attempted."], check=True)
        else:
            subprocess.run([sys.executable, str(TOOL), "paper", str(LIB), pid,
                            "https://pmc.ncbi.nlm.nih.gov/articles/" + row["pmcid"] + "/", "--html", "--version", "PMC-published"], check=True)
