"""Bind the six reviewed source families to saved retrieval evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/rsi_later_task_literature/skeptic"
STEMS = {"2603.19461v1": "skeptic_hyperagents", "2610.16491v1": "skeptic_specrsi",
         "2610.09604v1": "skeptic_learned_optimizer", "2610.24464v1": "skeptic_recursia",
         "2610.24944v1": "skeptic_epi", "2610.27610v1": "skeptic_auditing_recursion"}
metadata = json.loads((BASE / "skeptic_selected_metadata.index.json").read_text(encoding="utf-8"))
sources = []
for identifier, stem in STEMS.items():
    record = next(m for m in metadata if m["id"].endswith(identifier))
    receipt = json.loads((BASE / (stem + ".receipt.json")).read_text(encoding="utf-8"))
    raw = (BASE / (stem + ".body")).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == receipt["sha256"]
    sources.append({"arxiv_id": identifier, "title": record["title"], "published": record["published"],
                    "url": receipt["url"], "status": receipt["status"], "bytes": len(raw),
                    "sha256": receipt["sha256"], "capped": receipt["capped"],
                    "body": str((BASE / (stem + ".body")).relative_to(ROOT)),
                    "receipt": str((BASE / (stem + ".receipt.json")).relative_to(ROOT)),
                    "read_level": "primary full-HTML body retained; targeted methods/experiments/appendix excerpts reviewed",
                    "independently_reproduced": False})
result = {"substantive_source_count": len(sources), "sources": sources,
          "scope": "exactly six substantive papers; discovery snippets are not additional reviewed precedents",
          "no_az_numeric_access": True}
(BASE / "SOURCE_MANIFEST.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"sources": len(sources), "all_http200_complete": all(s["status"] == 200 and not s["capped"] for s in sources)}))
