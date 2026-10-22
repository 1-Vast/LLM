"""Verify receipt bodies and index the six independent primary works."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/rsi_later_task_literature/advocate"
WORKS = [
    ("DGM", "dgm_v3", "Darwin Godel Machine: Open-Ended Evolution of Self-Improving Agents", "2026-03-12 (v3); original 2025-05-29"),
    ("AlphaEvolve", "alphaevolve", "AlphaEvolve: A coding agent for scientific and algorithmic discovery", "2025-06-16 v1"),
    ("ShinkaEvolve", "shinka", "ShinkaEvolve: Towards Open-Ended And Sample-Efficient Program Evolution", "2025-09-17 v1"),
    ("SEAL", "seal_v2", "Self-Adapting Language Models", "2025-09-18 (v2); original 2025-06-12"),
    ("MaD-RSI", "mad_rsi", "MaD-RSI: Model-as-Data for Recursive Self-Improvement of Agent Harnesses", "2026-10-20 v1"),
    ("Audit", "audit_rsi", "Auditing the Product, Not the Recursion: The Evaluation Evidence Behind Recursive Self-Improvement Claims", "2026-10-20 v1"),
]

if __name__ == "__main__":
    receipts = [json.loads(line) for line in (OUT / "SOURCE_RECEIPTS.jsonl").read_text().splitlines()]
    by_name = {r["name"]: r for r in receipts if r.get("status") == 200}
    primary = []
    for key, name, title, version_date in WORKS:
        receipt = by_name[name]
        body = ROOT / receipt["body_path"]
        actual = hashlib.sha256(body.read_bytes()).hexdigest()
        if actual != receipt["sha256"]:
            raise ValueError("Literature body changed: " + name)
        primary.append({"work": key, "title": title, "version_date": version_date, **receipt,
                        "parsed_text_path": str((OUT / (name + ".txt")).relative_to(ROOT))})
    result = {"primary_works": primary, "unique_primary_work_count": len(primary),
              "successful_receipts": [r for r in receipts if r.get("status") == 200],
              "failed_attempts": [r for r in receipts if r.get("status") != 200],
              "note": "Six distinct primary works. Obsolete DGM v1 and SEAL v1 bodies are retained, but the review cites current v3/v2. Discovery records are not primary scientific evidence."}
    (OUT / "SOURCE_RECEIPTS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = ["# Source receipts index", "", result["note"], "",
             "| Work | Version date | Public primary URL | HTTP status | Bytes | Body SHA256 |", "|---|---|---|---:|---:|---|"]
    for r in primary:
        lines.append(f"| {r['work']} | {r['version_date']} | {r['url']} | {r['status']} | {r['bytes']} | `{r['sha256']}` |")
    lines += ["", "Every raw body and parsed text is in this directory. Exact UTC GET times, final URLs, content types and relative body paths are in SOURCE_RECEIPTS.json and the append-only SOURCE_RECEIPTS.jsonl.",
              "", "Discovery: arXiv query for 2026 self-improving papers (20 returned records), arXiv version metadata for these six IDs, broad OpenAlex query (no evidence claims based on it), GitHub repository search (no substantive repo reviewed), and a Google request that returned challenge/script content (not usable search evidence). The initial two parser failures and superseded bodies are documented in WORK_AND_FAILURES.md."]
    (OUT / "SOURCE_RECEIPTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"primary_works": len(primary), "body_hashes_verified": len(primary),
                      "successful_receipts": len(result["successful_receipts"]), "failed_attempts": len(result["failed_attempts"])}))
