"""Bind independent report and the exact saved primary bodies actually read."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "log/20261023/inherited_update_renewal/constructive"
sources = [
    "log/20261022/rsi_later_task_literature/skeptic/skeptic_learned_optimizer.body",
    "log/20261022/rsi_later_task_literature/skeptic/skeptic_specrsi.body",
]
payload = {
    "scope": "Independent review before current peer/API opinions; no experiment executed",
    "files": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "FIRST_SEAL.json"},
    "reused_primary_bodies": {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "new_HTTP": 0,
    "new_API": 0,
    "new_biological_values": 0,
    "toy_executed": False,
}
(OUT/"FIRST_SEAL.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
