"""Finalize this audit's source byte accounting and delivered artifact hashes."""
import hashlib
import json
import pathlib
from datetime import datetime, timezone

AUDIT = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path("D:/MAESTRO/data/external/virtual_cell_four_directions_20261030/assaybench")
log = AUDIT / "requests.jsonl"
entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
if not any(entry.get("retrospectively_logged") for entry in entries):
    entry = {
        "time_utc": None,
        "logged_time_utc": datetime.now(timezone.utc).isoformat(),
        "url": "https://huggingface.co/datasets/Genentech/assaybench/resolve/fa2ed4195d2eea1e5ed570d1a67c21e47650962d/biogrid/train-00000-of-00001.parquet",
        "range": "bytes=4-1380",
        "outcome": "error",
        "error": "URLError(SSLEOFError): first metadata-projection attempt; failure preceded retry logging fix",
        "bytes_received": 0,
        "retrospectively_logged": True,
        "evidence": "tool output from initial inspect_parquet_metadata.py run after footer retrieval, before retry implementation",
    }
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    entries.append(entry)
artifacts = []
for name in ("biogrid_temporal_train_gene_hits_csr.npz", "biogrid_temporal_train_metadata.json", "biogrid_temporal_train_metadata.csv", "biogrid_metadata_only.parquet"):
    path = ROOT / name
    artifacts.append({"path": str(path), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
summary = {
    "response_body_bytes_received": sum(entry.get("bytes_received", 0) for entry in entries),
    "saved_remote_bytes": sum(entry.get("saved_bytes", 0) for entry in entries),
    "requests": len(entries),
    "successful_requests": sum(entry["outcome"] == "saved" for entry in entries),
    "failed_requests": sum(entry["outcome"] == "error" for entry in entries),
    "cap_bytes_authorized": 265000000,
    "gene_hit_column_bytes": 250944990,
    "source_revision": "fa2ed4195d2eea1e5ed570d1a67c21e47650962d",
    "code_revision": "552008a7f3c52c560c60dbdadd2dc0d2f8e928dc",
    "LaTest_data_requests": 0,
    "model_training_or_scoring": False,
    "official_historical_validation_test": "physical chunk bytes co-retrieved; rows masked before Python/census/output; no scoring",
    "artifacts": artifacts,
}
(AUDIT / "acquisition_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
