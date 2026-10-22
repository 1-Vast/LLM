"""Verify this bounded review's own source receipts and preserved draft."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261022/update_value_qualification/skeptic"
CODE = ROOT / "research/update_value_qualification_20261022"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


receipts = [json.loads(line) for line in (LOG / "HTTP_RECEIPTS.jsonl").read_text(encoding="utf-8").splitlines()]
checks = [{"name": "exactly_four_GETs", "passed": len(receipts) == 4},
          {"name": "independent_draft_unchanged", "passed": sha(LOG / "INDEPENDENT.md") ==
           "523d5fc558c7227b5635c2aee7e9e97e2613bf9f69b3a53389086b1f2d933fa8"}]
for r in receipts:
    checks.append({"name": r["name"], "passed": r["status"] == 200 and r["body_complete"] and
        r["sha256"] == sha(LOG / f"{r['name']}.body") and r["bytes"] == (LOG / f"{r['name']}.body").stat().st_size})
paths = sorted(CODE.glob("skeptic*.py"))
for p in paths:
    ast.parse(p.read_text(encoding="utf-8"))
checks.append({"name": "all_skeptic_python_parses", "passed": True, "files": len(paths)})
comparison = json.loads((LOG / "HISTORICAL_COMPARISON.json").read_text(encoding="utf-8"))
checks.append({"name": "historical_independent_comparison", "passed": comparison["passed"],
               "checks": comparison["checks"], "maxdiff": comparison["maxdiff"]})
report = {"passed": all(c["passed"] for c in checks), "checks": checks,
          "code_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
          "scope": "own source receipts, immutable independent draft and independent exported-score arithmetic; no model performance experiment"}
output = LOG / "INTEGRITY.json"
if output.exists():
    raise RuntimeError("Refuse overwrite")
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": report["passed"], "checks": len(checks), "python_files": len(paths)}))
