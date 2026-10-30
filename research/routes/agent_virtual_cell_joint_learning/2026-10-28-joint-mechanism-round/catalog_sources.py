"""Register inspected source artifacts with lit-survey; no network or author execution."""
from pathlib import Path
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
LIB = ROOT.parents[1] / "reference"
CLI = Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")
if (ROOT / "catalog_receipt.json").exists():
    raise SystemExit("Catalog receipt exists; no automatic replay.")
ns = {"a": "http://www.w3.org/2005/Atom"}
metadata = {}
for path in [ROOT / "sources/final_refresh/arxiv_0.raw", ROOT / "sources/final_refresh/arxiv_1.raw",
             ROOT / "sources/challenger/Q1_psr.xml", ROOT / "sources/challenger/Q2_value.xml"]:
    for entry in ET.parse(path).getroot().findall("a:entry", ns):
        identifier = entry.findtext("a:id", namespaces=ns).split("/abs/")[-1].split("v")[0]
        metadata[identifier] = {"title": " ".join(entry.findtext("a:title", namespaces=ns).split()),
            "authors": "; ".join(a.findtext("a:name", namespaces=ns) for a in entry.findall("a:author", ns)),
            "first_public_date": entry.findtext("a:published", namespaces=ns)[:10]}
specs = [
    ("1103.1343", "final_refresh/switched_realization_1103.1343v2.html", "v2", "Root: Sec4 Theorems3/4 and rank/word conventions, partial section5; 2011 foundation, not recent-window evidence"),
    ("1612.09076", "final_refresh/psr_bases_1612.09076v1.html", "v1", "Root: Sec2 Eq1-3 and Sec3 basis selection partly; end of Algorithm1 not fully received; 2016 foundation"),
    ("2604.07016", "final_refresh/predictive_skill_2604.07016v1.html", "v1", "Root: Sec3.2 expected outcome equivalence definitions and first part Sec3.3 counterexample; no full proof/experiment read"),
    ("1207.4167", "challenger/psr_1207.4167.pdf", "v1", "Challenger: pp4-5 core tests/recursion. Original UAI2004 reissued arXiv2012; foundation outside2025-26"),
    ("2106.03926", "challenger/reward_psr_2106.03926.pdf", "v1", "Challenger pp3-4; root independently checked p3 Theorem1 and p4 Sec4 R-PSR. Original2021 foundation, no full appendix"),
    ("2106.10316", "challenger/pve_2106.10316.pdf", "v2", "Challenger pp3-4; root independently checked p4 Proposition4. Original2021 foundation; no full appendix"),
    ("2206.02072", "challenger/ve_sampling_2206.02072.pdf", "v2", "Challenger pp3-4,6-7 model/action/value-equivalent sampling. Original2022 foundation; root identity/abstract only"),
    ("2607.04464", "challenger/operator_2607.04464.pdf", "v2", "Challenger pp1-2 diagnostic preprint; root identity/abstract only. No experiment result adoption"),
]
receipts = []
def call(arguments):
    process = subprocess.run([sys.executable, str(CLI)] + [str(a) for a in arguments], capture_output=True, text=True, encoding="utf-8")
    receipts.append({"args": [str(a) for a in arguments], "exit_code": process.returncode,
                     "stdout": process.stdout, "stderr": process.stderr})
    if process.returncode:
        (ROOT / "catalog_partial_receipt.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit("Catalog command rejected; see partial receipt.")
for identifier, relative, version, scope in specs:
    pid = "arxiv-" + identifier
    values = metadata[identifier]
    if identifier == "1103.1343":
        values["authors"] = "Mihály Petreczky; Laurent Bako; Jan H. van Schuppen"
    fields = [f"{key}={value}" for key,value in values.items()]
    fields += [f"alt_id={identifier}", f"landing_page=https://arxiv.org/abs/{identifier}",
               "type_status=preprint or foundational original", "reading_level=P", f"reading_scope={scope}",
               "date_basis=Official arXiv Atom first posted date; stored version separately pinned; formal venue date not newly verified",
               "note=Targeted PASS5/PASS6 closest-prior reading, not comprehensive novelty search; source receipts and exact scope in joint-mechanism-round"]
    call(["record", LIB, "paper", pid] + fields)
    file = ROOT / "sources" / relative
    arguments = ["paper", LIB, pid, "--file", file, "--version", version]
    if file.suffix == ".html":
        arguments += ["--html"]
    call(arguments)
    suffix = "html" if file.suffix == ".html" else "pdf"
    call(["record", LIB, "paper", pid, f"source_url=https://arxiv.org/{suffix}/{identifier}{version}"])

pid = "doi-10.1049-syb2.70083"
call(["record", LIB, "paper", pid, "title=Double Q-Learning for Intelligent Multi-Drug Scheduling in Cancer Chemotherapy Optimisation",
      "authors=Behnoush Alizade; Ahmad Hajipour", "doi=10.1049/syb2.70083", "first_public_date=2026-08-03",
      "date_basis=Original JATS epub pub-date 2026-08-03; collection Jan-Dec2026 distinct", "type_status=Journal Article",
      "landing_page=https://pmc.ncbi.nlm.nih.gov/articles/PMC13432990/", "reading_level=P",
      "reading_scope=Challenger conclusions/limitations: PK-PD simulation only, no in-vivo/clinical/retrospective patient validation; root bibliographic identity only",
      "note=Original MAIN article JATS stored in supplement-format slot, not actual supplementary material; main PDF/HTML pending"])
file = ROOT / "sources/challenger/bio_PMC13432990.xml"
call(["paper", LIB, pid, "--file", file, "--role", "supplement", "--version", "primary-original-jats-xml"])
call(["record", LIB, "paper", pid, "--path", "papers/doi-10.1049-syb2.70083/supp-bio_PMC13432990.xml",
      "source_url=https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13432990/fullTextXML", "reading_level=P",
      "reading_scope=Challenger conclusions and limitations only", "note=Primary original JATS, not SI. Real official retrieval receipt in sources/challenger/access_receipts.json"])
original = next((ROOT / "sources/final_refresh/organoid_release1").iterdir())
call(["code", LIB, "yakavets-organoid-zenodo1", "--paper", "doi-10.1126-sciadv.adt1851", "--existing", original,
      "--ref", "1.0", "--relation", "official", "--evidence", "Primary JATS Data availability links Zenodo14890339; its official API resolves Release1.0 DOI14890340"])
call(["record", LIB, "code", "doi-10.1126-sciadv.adt1851", "--repo", "yakavets-organoid-zenodo1",
      "repo_url=https://github.com/yakavetsiv/ml-mf_chemo", "license=GPL-3.0",
      "note=Official Zenodo DOI14890340 Release1.0 dated2025-02-19, downloaded by root then copied locally. Archive SHA997cbcdab23b754b1e0d94817ecac1b7f9fc8674a717c475d3e93fd4457bff82. Full commit unknown; directory shorta179d2a not treated as fullSHA. Sequential tables byte-identical and time mapping unchanged vs e38fc0ded24a. No code execution/response analysis; LICENSE GPLv3 conflicts README MIT."])
(ROOT / "catalog_receipt.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"commands": len(receipts), "added_papers": 9, "official_code_versions_added": 1}))
