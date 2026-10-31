"""Bind the scientific question and inspected evidence before fresh review."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

EP = Path(__file__).resolve().parent.parent
ROOT = EP.parents[3]
out = EP / "choice_question_freeze.json"
assert not out.exists()
names = [
    "choice_transport_question_v1.md", "root/data_inspection_contract.md",
    "investigator/sources/u1c2026.xml", "investigator/sources/ishigami2024.xml",
    "scout/sources/rank_epistasis.xml", "scout/sources/comparative_fitness_2017.xml",
    "scout/sources/eci2d.html", "root/u1c_dose_schema.json",
    "root/geo_sample_metadata_projection.json", "root/junction_header_audit.json",
    "root/sources/u1c-geo-series.txt", "root/sources/u1c-geo-sample-metadata.txt",
    "root/sources/u1c-per-sample-junction-counts.txt.gz",
    "root/sources/u1c-dose-sample-data2.xlsx", "root/sources/scsp-publisher-source.xlsx",
    "root/sources/dedseq-commit.json", "root/sources/dedseq-tree.json",
    "root/sources/dedseq-01-combine-junction.R", "root/sources/dedseq-06-ana-exon-PSI.R",
    "root/sources/dedseq-02-cut-gene-blocks.pl",
]
external = ["reference/papers/doi-10.1038-s41467-026-74594-9/supp-scsp_fulltext.xml"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


result = {"created_utc": datetime.now(timezone.utc).isoformat(),
          "stage": "SCIENTIFIC_QUESTION_ONLY_NOT_NUMERICAL_FREEZE",
          "response_exposure": "Published aggregate literature and schema/sample metadata; no response records projected",
          "files": {name: sha(EP / name) for name in names},
          "external_files": {name: sha(ROOT / name) for name in external}}
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"files": len(names), "external_files": len(external), "stage": result["stage"]}))
