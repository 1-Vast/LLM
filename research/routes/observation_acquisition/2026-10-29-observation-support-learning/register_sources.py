"""Register this bounded round's inspected originals with the installed library writer; zero network."""
from pathlib import Path
import hashlib
import json
import sys
from types import SimpleNamespace

sys.path.insert(0, r"D:\CodexData\.codex\skills\lit-survey\scripts")
import reference_library as library

HERE = Path(__file__).resolve().parent
LIB = HERE.parents[1] / "reference"
ledger = {r["name"]: r for r in map(json.loads, (HERE / "retrieval.jsonl").read_text(encoding="utf-8").splitlines())}
entries = [
    ("arxiv-2606.24020", "p4_every_eval.html", "You Don't Need to Run Every Eval", "2026-06-22", "", "main", "arxiv-v2",
     "P: root selected S3 data/geometry, S4 bias ALS/setup, S5 probes/temporal splits, S6.2 risk features and S7; some broad projections truncated and not claimed complete; no appendix/code execution", "preprint; venue not verified"),
    ("arxiv-2605.02458", "p5_active_multiple.html", "Active multiple matrix completion with adaptive confidence sets", "2026-05-04", "", "main", "arxiv-v1",
     "P: root S2-S3 paragraphs and display equations E1,Ex9,Ex16-21; proofs/results/code not read", "preprint; venue not verified"),
    ("doi-10.1186-s12915-025-02457-8", "p6_mclrp.xml", "MCLRP: enhanced prediction of anticancer drug response through low-rank matrix completion and transcriptomic profiling", "", "2025-12-03", "supplement", "original-main-JATS",
     "P: root Sec11-14 and notes3; formula text read through JATS; no full supplementary/code audit; not all Results read", "journal article"),
    ("doi-10.34133-csbj.0099", "p7_missingness.xml", "Informative Missingness in Nominal Data: A Graph-Theoretic Approach to Revealing Hidden Structure", "", "2026-05-18", "supplement", "original-main-JATS",
     "P: root sec3,5,9; neutral scout sec2-5 and9; no full method/code/benchmark reproduction", "journal article")
]
receipt = []
for pid, name, title, first, formal, role, version, scope, status in entries:
    item = ledger[name]
    body = (HERE / "sources" / name).read_bytes()
    assert hashlib.sha256(body).hexdigest() == item["sha256"]
    note = "Original bytes/URL checked against episode retrieval ledger. Downloaded and partial reading do not mean reproduced; source-code snapshot not acquired."
    if role == "supplement":
        note += " MAIN ARTICLE JATS in generic supplement storage slot, not scientific SI; main PDF/HTML not acquired. Earlier first public date unknown."
    fields = {"title": title, "type_status": status, "first_public_date": first, "formal_date": formal,
              "date_basis": "arXiv original entry published" if first else "original JATS publication date; earlier public date unknown",
              "landing_page": item["url"], "candidate_url": item["url"], "version": version,
              "reading_level": "P", "reading_scope": scope, "note": note}
    if pid.startswith("arxiv"):
        fields["alt_id"] = pid.replace("arxiv-", "arxiv:")
    else:
        fields["doi"] = "10.1186/s12915-025-02457-8" if "12915" in pid else "10.34133/csbj.0099"
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=None, repo=None,
                                      fields=[f"{k}={v}" for k, v in fields.items()]))
    head, rows = library.read_tsv(LIB / "papers.tsv", library.PAPER_COLS)
    stored_status = library.save_paper(LIB, rows, library.main_row(rows, pid), body, item["url"], item["content_type"],
                                       role == "main", role, version, name)
    library.write_tsv(LIB / "papers.tsv", head, rows)
    stored = next(r for r in rows if r["paper_id"] == pid and r["sha256"] == item["sha256"])
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=stored["local_path"], repo=None,
                                      fields=["reading_level=P", "reading_scope=" + scope, "note=" + note]))
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="code", key=pid, path=None, repo=None,
                                      fields=["download_status=not_verified", "note=Source code not acquired or executed under bounded round budget"]))
    receipt.append({"paper_id": pid, "local_path": stored["local_path"], "source_sha256": item["sha256"], "status": stored_status})
pid = "doi-10.1016-j.cell.2026.06.005"
library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=None, repo=None, fields=[
    "title=UniPert-G2CP bridges genetic and chemical screens from molecular representation to phenotype modeling",
    "doi=10.1016/j.cell.2026.06.005", "alt_id=PMID42497867", "type_status=journal article",
    "formal_date=2026-08-06", "date_basis=original PubMed: electronic2026-07-25; issue2026-08-06; earlier public date unknown",
    "landing_page=https://doi.org/10.1016/j.cell.2026.06.005", "candidate_url=" + ledger["p8_unipert.html"]["url"],
    "download_status=restricted", "failure_reason=Original publisher full-text HTTP403 on2026-10-29; no retry",
    "reading_level=A", "reading_scope=Original PubMed complete abstract and primary IDs/dates only; no full method/code reading",
    "note=Genetic/chemical screen transfer abstract is relevant precedent only; no causal/generalization claim adopted as established"] ))
library.cmd_record(SimpleNamespace(lib=str(LIB), table="code", key=pid, path=None, repo=None,
                                  fields=["download_status=not_verified", "note=Full text restricted; code not checked/acquired"]))
(HERE / "library_registration.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt))
