"""Register three inspected primary sources and one deferred abstract; no network."""
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
    ("arxiv-2609.22411", "p5_autorasor.html", "AutoRASOR: Autonomous Rapid Scanning Electron Microscope Operator", "2026-09-18",
     "P: root original S2.SS5-S2.SS6 and A2; conditional fine-feature variance, archive NW estimator, jackknife observation noise and qLogNEI. Independent display equations and full results/code not audited"),
    ("arxiv-2610.33272", "p6_atomistic_coupling.html", "Autonomous atomistic-continuum coupling through uncertainty-aware active learning", "2026-10-23",
     "P: root original S3.SS2 and S4, S4.SS1-S4.SS2; steady-state ensemble flux interface, six GP surrogates, uncertainty trigger and refit; no reproduction of simulation, DFT or numerical results"),
    ("arxiv-2608.09104", "p7_multitask_probe.pdf", "Multitask Scanning Probe Microscopy", "2026-08-10",
     "P: root PDF pp6-9,11,15: ICM/LMC and shared-specific models, random scalarization UCB, equal implicit costs, periodic exploration, hyperparameter fitting and paired seeds; equations13 cost extension not executed method")
]
receipts = []
for pid, name, title, date, scope in entries:
    item = ledger[name]
    body = (HERE / "sources" / name).read_bytes()
    assert hashlib.sha256(body).hexdigest() == item["sha256"]
    note = "Original identity/version checked; partial methods reading. Formal venue and author-code repository/commit/license not verified; no author code/data execution."
    fields = {"title": title, "type_status": "preprint; formal venue not verified", "first_public_date": date,
              "date_basis": "original arXiv Atom published; versionv1", "landing_page": "https://arxiv.org/abs/" + pid[6:],
              "candidate_url": item["url"], "alt_id": "arxiv:" + pid[6:], "version": "arxiv-v1",
              "reading_level": "P", "reading_scope": scope, "note": note}
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=None, repo=None, fields=[f"{k}={v}" for k, v in fields.items()]))
    head, rows = library.read_tsv(LIB / "papers.tsv", library.PAPER_COLS)
    status = library.save_paper(LIB, rows, library.main_row(rows, pid), body, item["url"], item["content_type"], True, "main", "arxiv-v1", name)
    library.write_tsv(LIB / "papers.tsv", head, rows)
    stored = next(r for r in rows if r["paper_id"] == pid and r["sha256"] == item["sha256"])
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=stored["local_path"], repo=None,
                                      fields=["reading_level=P", "reading_scope=" + scope, "note=" + note]))
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="code", key=pid, path=None, repo=None,
                                      fields=["download_status=not_verified", "note=Primary paper acquired, author repository/commit/license not inspected; acquisition budget exhausted"]))
    receipts.append({"paper_id": pid, "local_path": stored["local_path"], "sha256": item["sha256"], "status": status})
pid = "doi-10.1186-s13321-026-01204-7"
fields = {"doi": "10.1186/s13321-026-01204-7", "title": "ChemScreener: an active learning enabled hit discovery workflow with WDR5 inhibitor case study.",
          "type_status": "journal article", "landing_page": "https://pubmed.ncbi.nlm.nih.gov/42010453/", "alt_id": "pubmed:42010453",
          "reading_level": "A", "reading_scope": "Original PubMed metadata/abstract only; relevant hit-discovery workflow, no fulltext/method/code acquisition within exhausted bounded budget",
          "note": "Fulltext deferred; PMC13235147 identified in original ArticleIdList. Not a method-level basis for novelty or cell-specific functional claims."}
library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=None, repo=None, fields=[f"{k}={v}" for k, v in fields.items()]))
library.cmd_record(SimpleNamespace(lib=str(LIB), table="code", key=pid, path=None, repo=None, fields=["download_status=not_yet_checked", "note=Deferred primary-method and code check; bounded acquisition exhausted"]))
receipts.append({"paper_id": pid, "status": "metadata_abstract_only_fulltext_deferred"})
(HERE / "library_registration.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipts, ensure_ascii=False))
