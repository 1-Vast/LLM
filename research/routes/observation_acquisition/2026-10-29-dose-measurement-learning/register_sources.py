"""Register inspected primary bytes and the scoped author-code snapshot; no network."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import sys

sys.path.insert(0, r"D:\CodexData\.codex\skills\lit-survey\scripts")
import reference_library as library

HERE = Path(__file__).resolve().parent
LIB = HERE.parent.parent / "reference"
ledger = {r["name"]: r for r in map(json.loads, (HERE / "retrieval.jsonl").read_text(encoding="utf-8").splitlines())}
entries = [
    ("arxiv-2610.23623", "p4_mtal_deconstruction.html", "Deconstructing Multi-Task Active Learning: The Paradox of Gradient Conflict and Orthogonal Decomposition", "2026-10-16", "", "main", "arxiv-v1", "",
     "Root original sections3.1-5.3, AppendixA.1 and B.3; acquisition/PCGrad separation, entropy-correlation CTMI proxy; unweighted-gradient cancellation claim checked and limited. Full experiments/display equations/code not reproduced."),
    ("doi-10.1038-s41698-024-00691-x", "p5_dose_mogp.xml", "Multi-output prediction of dose–response curves enables drug repositioning and biomarker discovery", "", "2024-09-20", "supplement", "published-main-JATS", "10.1038/s41698-024-00691-x",
     "Root original Sec10/13/18/22/23; ICM dose outputs, grouped feature product kernels, protocol selection, measured normalized labels and PCHIP interpolation; truncated13/18 recovered. No model/results/code reproduction."),
    ("doi-10.1371-journal.pcbi.1012185", "p6_structure_learning.xml", "Data-driven learning of structure augments quantitative prediction of biological responses", "", "2024-06-03", "supplement", "published-main-JATS", "10.1371/journal.pcbi.1012185",
     "Root original sec006/013/015, truncated006 recovered; SVC boundary distance for quantitative regression and near/far/mixed feedback acquisition. Original main article front Data Availability checked separately from embedded peer review. No numerical reproduction.")
]
receipts = []
for pid, name, title, first, formal, role, version, doi, scope in entries:
    item = ledger[name]
    body = (HERE / "sources" / name).read_bytes()
    assert hashlib.sha256(body).hexdigest() == item["sha256"]
    note = "Original primary identity/bytes checked; partial method reading, not scientific replication."
    if role == "supplement":
        note += " MAIN ARTICLE JATS stored in generic supplement technical slot, not scientific SI; main PDF/HTML pending; earlier public date unknown."
    fields = {"title": title, "type_status": "preprint; formal venue not verified" if not doi else "journal article",
              "first_public_date": first, "formal_date": formal, "doi": doi,
              "date_basis": "Original arXiv Atom v1 published" if first else "Original main JATS epub; earlier public date unknown",
              "landing_page": "https://arxiv.org/abs/2610.23623" if not doi else "https://doi.org/" + doi,
              "candidate_url": item["url"], "version": version, "reading_level": "P", "reading_scope": scope, "note": note}
    if not doi:
        fields["alt_id"] = "arxiv:2610.23623"
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=None, repo=None,
                                      fields=[f"{k}={v}" for k, v in fields.items()]))
    head, rows = library.read_tsv(LIB / "papers.tsv", library.PAPER_COLS)
    status = library.save_paper(LIB, rows, library.main_row(rows, pid), body, item["url"], item["content_type"],
                                role == "main", role, version, name)
    library.write_tsv(LIB / "papers.tsv", head, rows)
    stored = next(r for r in rows if r["paper_id"] == pid and r["sha256"] == item["sha256"])
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=stored["local_path"], repo=None,
                                      fields=["reading_level=P", "reading_scope=" + scope, "note=" + note]))
    if "pcbi" not in pid:
        url = "https://github.com/Juho-Jung/multitask_active_learning_official" if not doi else "https://github.com/juanjogg1987/MOGPs_for_Dose_Response_Predictions"
        library.cmd_record(SimpleNamespace(lib=str(LIB), table="code", key=pid, path=None, repo=None,
                                          fields=["download_status=not_verified", "note=Original paper code link " + url + "; source/commit/license not acquired within bounded decision-focused search"]))
    receipts.append({"paper_id": pid, "local_path": stored["local_path"], "sha256": item["sha256"], "status": status})

sha = "6b0d4e653b6f3f0ac49a6ea3b038442417223018"
pid = entries[2][0]
rid = "ychh-structurelearning"
snapshot = LIB / "code" / rid / sha[:12]
library.cmd_code(SimpleNamespace(lib=str(LIB), repo_id=rid, url=None, archive=None, existing=str(snapshot),
                                relation="official", evidence="Main article front Data Availability points to https://github.com/YChH/StructureLearning; primary main JATS checked, not inferred from reviewer comment",
                                paper=[pid], ref=sha, max_mb=8))
library.cmd_record(SimpleNamespace(lib=str(LIB), table="code", key=pid, path=None, repo=rid,
                                  fields=["repo_url=https://github.com/YChH/StructureLearning", "commit=" + sha,
                                          "commit_date=2024-05-24T15:36:26Z", "license=unknown",
                                          "entrypoints=AL02-Final.ipynb; Main Results.ipynb; LR_Classification.ipynb; OtherRegression_Final.ipynb",
                                          "missing_assets=Eight bundled CSV/XLSX data members excluded from extracted snapshot; AL notebook references round3.xlsx absent from archive; no dependency manifest or license file present",
                                          "note=Four original notebooks imported from freshly fetched pinned author archive; partial source-only reading, outputs/data not used and notebooks not run. API confirms full commit, not exact paper-generating runtime. AL source-array52 branch uses improvement>0.3; other branches and full reproduction not audited. See current episode p6_code_receipt.json. Raw archive incidentally includes unextracted data bytes."]))
receipts.append({"paper_id": pid, "repo_id": rid, "commit": sha, "partial_snapshot": True,
                 "source_notebooks": 4, "excluded_data_members": 8, "executed": False})
(HERE / "library_registration.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipts, ensure_ascii=False))
