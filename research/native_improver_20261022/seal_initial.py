"""Bind independent position and its actual input files before peer exchange."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("D:/MAESTRO")
OUT = ROOT / "log/20261022/native_operation/improver"
PATHS = [
    Path("C:/Users/59964/.codex/attachments/45d9c2f9-b12a-4e71-bd4a-9f6cc5eb5ce9/goal-objective.md"),
    ROOT / "research/REPORT.md",
    ROOT / "log/20261022/cipa_control_information/PROJECT_CAPABILITY_AUDIT.md",
    ROOT / "log/20261022/mse_source_gate/DECISION.md",
    ROOT / "log/20261022/mse_source_gate/CONTINUATION.md",
    ROOT / "log/20261022/strategy_rethink/RESULT_DECISION.md",
    ROOT / "log/20261022/rsi_later_task_literature/advocate/SOURCE_RECEIPTS.json",
    ROOT / "log/20261022/rsi_later_task_literature/skeptic/SOURCE_MANIFEST.json",
    OUT / "PRIMARY_SOURCE_RECEIPTS.json",
    OUT / "seal.html",
    OUT / "gradient_history.html",
    OUT / "INDEPENDENT_INITIAL.md",
    ROOT / "research/native_improver_20261022/source_check.py",
    ROOT / "research/native_improver_20261022/seal_initial.py",
]


def main():
    output = OUT / "INDEPENDENT_SEAL.json"
    if output.exists():
        raise FileExistsError(output)
    files = [{"path": str(path), "bytes": path.stat().st_size,
              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in PATHS]
    record = {"time_utc": datetime.now(timezone.utc).isoformat(),
              "requested_model": "gpt-6.1-sol", "requested_reasoning": "high",
              "backend_attested": False, "current_peer_material_read": False,
              "root_direct_criteria_clarification_disclosed": True, "files": files}
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({"seal": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                      "bound_files": len(files)}, indent=2))


if __name__ == "__main__":
    main()
