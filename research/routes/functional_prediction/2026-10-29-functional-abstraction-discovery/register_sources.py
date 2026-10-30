"""Register four inspected original sources, without network or source execution."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import sys

sys.path.insert(0, r"D:\CodexData\.codex\skills\lit-survey\scripts")
import reference_library as library

HERE = Path(__file__).resolve().parent
LIB = HERE.parents[1] / "reference"
ledger = {r["name"]: r for r in map(json.loads, (HERE / "retrieval.jsonl").read_text(encoding="utf-8").splitlines())}
entries = [
    ("arxiv-2609.36553", "p4_hiddenkinematics.html", "Learning to Explore Hidden Kinematics for Articulated Object Manipulation", "2026-09-29", "", "main", "arxiv-v1",
     "P: root S3 paragraphs online particles, posterior flow rendering, information reward, privileged expert and distillation; display equations not fully audited; experiments/code not reproduced", "preprint; formal venue not verified"),
    ("arxiv-2608.21031", "p7_physcap.html", "PhysCaP: Grounding Code-as-Policy Agent with Physics-Informed Exploration", "2026-08-21", "", "main", "arxiv-v2",
     "P: root S3.1-S3.3 paragraphs and inline mass/stiffness formulas; no full appendix/prompt/experiment/code audit", "preprint; formal venue not verified"),
    ("doi-10.3389-fbinf.2026.1838904", "p5_bchem.xml", "BCheM: a framework integrating molecular attributes and behavioral representations for precise prediction of drug resistance across multiple disease contexts", "", "2026-05-19", "supplement", "original-main-JATS",
     "P: root s3-1 Materials and s3-2 Method; DRESIS resistance graph plus GPT disease descriptions; not raw functional dose profiles; results/code not audited", "journal article"),
    ("doi-10.1038-s41467-026-72198-x", "p6_regformer.xml", "RegFormer: a single-cell foundation model powered by gene regulatory hierarchies", "", "2026-05-05", "supplement", "original-main-JATS",
     "P: root Sec15-18 architecture/topological order/dual embeddings and Sec29 drug-response method; author causal wording not accepted as causal identification; no full ablation/source-code reproduction", "journal article")
]
receipt = []
for pid, name, title, first, formal, role, version, scope, status in entries:
    item = ledger[name]
    body = (HERE / "sources" / name).read_bytes()
    assert hashlib.sha256(body).hexdigest() == item["sha256"]
    note = "Original bytes and primary identity checked; partial method reading, no source-code snapshot or response-data acquisition/execution."
    if role == "supplement":
        note += " MAIN ARTICLE JATS in generic supplement storage slot, not scientific SI; main PDF/HTML not acquired; earlier first public date unknown."
    fields = {"title": title, "type_status": status, "first_public_date": first, "formal_date": formal,
              "date_basis": "arXiv original entry published" if first else "original JATS publication date; earlier public date unknown",
              "landing_page": item["url"], "candidate_url": item["url"], "version": version,
              "reading_level": "P", "reading_scope": scope, "note": note}
    if pid.startswith("arxiv"):
        fields["alt_id"] = pid.replace("arxiv-", "arxiv:")
    else:
        fields["doi"] = "10.3389/fbinf.2026.1838904" if "fbinf" in pid else "10.1038/s41467-026-72198-x"
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=None, repo=None,
                                      fields=[f"{k}={v}" for k, v in fields.items()]))
    head, rows = library.read_tsv(LIB / "papers.tsv", library.PAPER_COLS)
    result = library.save_paper(LIB, rows, library.main_row(rows, pid), body, item["url"], item["content_type"],
                                role == "main", role, version, name)
    library.write_tsv(LIB / "papers.tsv", head, rows)
    stored = next(r for r in rows if r["paper_id"] == pid and r["sha256"] == item["sha256"])
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="paper", key=pid, path=stored["local_path"], repo=None,
                                      fields=["reading_level=P", "reading_scope="+scope, "note="+note]))
    code_note = "Original paper project page only; repository/commit/license not verified or acquired."
    if "fbinf" in pid:
        code_note = "Original main JATS links https://github.com/Yuu088/BCheM ; commit/license/source not acquired."
    elif "72198" in pid:
        code_note = "Original main JATS links https://github.com/BGIResearch/RegFormer ; commit/license/source not acquired."
    library.cmd_record(SimpleNamespace(lib=str(LIB), table="code", key=pid, path=None, repo=None,
                                      fields=["download_status=not_verified", "note="+code_note]))
    receipt.append({"paper_id": pid, "local_path": stored["local_path"], "sha256": item["sha256"], "status": result})
(HERE / "library_registration.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False))
