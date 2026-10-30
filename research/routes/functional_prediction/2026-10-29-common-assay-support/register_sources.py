"""Register already fetched original responses using the lit-survey library writer; zero network."""
from pathlib import Path
import hashlib
import json
import sys
from types import SimpleNamespace

sys.path.insert(0, r"D:\CodexData\.codex\skills\lit-survey\scripts")
import reference_library as library

HERE = Path(__file__).resolve().parent
LIB = Path(r"D:\MAESTRO\reference")
retrieval = {row["name"]: row for row in map(json.loads, (HERE / "retrieval.jsonl").read_text(encoding="utf-8").splitlines())}
entries = [
    ("arxiv-2603.29677", "p4_multimodal_pitfalls.html", "Mind the Gap: A Framework for Assessing Pitfalls in Multimodal Active Learning",
     "2026-03-31", "", "main", "arxiv-v1", "P: sections 3-5 and appendix A.4; not all results/proofs/code", "preprint; acceptance not verified"),
    ("arxiv-2605.14917", "p5_mi_lower_bound.html", "A Mutual Information Lower Bound for Multimodal Regression Active Learning",
     "2026-05-14", "", "main", "arxiv-v1", "P: sections 2-3 and E12-16 alttext; independent reviewer also checked E17; not full proofs/experiments/code", "preprint; acceptance not verified"),
    ("doi-10.1093-bioadv-vbag246", "p6_ludrp.xml", "Leveraging uncertainty estimates for drug response prediction in cancer cell lines",
     "", "2026-08-25", "supplement", "original-main-JATS", "P: sections 7,11,14,22,29 of main JATS; no author code/data execution", "journal article")
]
receipt = []
for pid, filename, title, first_date, formal_date, role, version, scope, status in entries:
    source = retrieval[filename]
    body = (HERE / "sources" / filename).read_bytes()
    assert hashlib.sha256(body).hexdigest() == source["sha256"]
    note = "Root retrieved original response; exact source URL and hash follow retrieval.jsonl; downloaded does not mean fully read or reproduced."
    if role == "supplement":
        note += " Original MAIN ARTICLE JATS uses generic supplement storage because helper main slot accepts only PDF/HTML; NOT scientific supplementary information. First public date unknown. Main PDF/HTML not acquired."
    fields = {"title": title, "type_status": status, "first_public_date": first_date, "formal_date": formal_date,
              "date_basis": "original arXiv entry published date" if first_date else "original PubMed electronic publication; earlier public date not verified",
              "landing_page": source["url"], "candidate_url": source["url"], "version": version,
              "reading_level": "P", "reading_scope": scope, "note": note}
    if pid.startswith("arxiv"):
        fields["alt_id"] = pid.replace("arxiv-", "arxiv:")
    else:
        fields["doi"], fields["alt_id"] = "10.1093/bioadv/vbag246", "PMID42781244;PMC13600678"
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=None, repo=None,
                                      fields=[f"{k}={v}" for k, v in fields.items()]))
    head, rows = library.read_tsv(LIB / "papers.tsv", library.PAPER_COLS)
    base = library.main_row(rows, pid)
    result = library.save_paper(LIB, rows, base, body, source["url"], source["content_type"],
                                role == "main", role, version, filename)
    library.write_tsv(LIB / "papers.tsv", head, rows)
    stored = [r for r in rows if r["paper_id"] == pid and r["sha256"] == source["sha256"]]
    assert len(stored) == 1
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=stored[0]["local_path"], repo=None,
                                      fields=["reading_level=P", "reading_scope=" + scope, "note=" + note]))
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="code", key=pid, path=None, repo=None,
                                      fields=["download_status=not_verified", "note=Code snapshot not acquired under this round budget; no execution/reproduction claimed"]))
    receipt.append({"paper_id": pid, "source_sha256": source["sha256"], "result": result,
                    "local_path": stored[0]["local_path"], "storage_role": role, "network_requests": 0})
(HERE / "library_registration.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt))
