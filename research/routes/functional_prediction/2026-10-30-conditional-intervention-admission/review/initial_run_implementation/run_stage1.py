"""Launch the one diagnostic with a hard process timeout and retained failures."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parents[3] / "data/processed/conditional_interventions_20261030/cgi/stage1"


def write(path, obj):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    journal = OUT / "launcher.json"
    assert not journal.exists(), "no automatic replay of the authorized diagnostic"
    started = time.perf_counter()
    record = {"status": "running", "timeout_seconds": 1800, "python": sys.executable}
    write(journal, record)
    try:
        result = subprocess.run([sys.executable, str(ROOT / "stage1.py")], timeout=1800)
        if result.returncode:
            raise RuntimeError(f"child failed with exit code {result.returncode}")
        run = json.loads((OUT / "run.json").read_text(encoding="utf-8"))
        if run.get("status") != "complete":
            raise RuntimeError("child returned without a complete result")
        record.update(status="complete", exit_code=result.returncode)
    except Exception as exc:
        record.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        path = OUT / "run.json"
        run = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        access_path = OUT / "call_access_receipt.json"
        access = json.loads(access_path.read_text(encoding="utf-8")) if access_path.exists() else {}
        unknown = bool(run.get("label_extraction_started") and access.get("status") not in ["complete", "failed"])
        run.update(status="failed", launcher_failure=record["failure"],
                   unknown_partial_call_exposure=unknown)
        write(path, run)
        path = OUT / "decision.json"
        decision = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        decision.update(status="NO_HELD_OUT_RELEASE", information_gate_pass=False,
                        held_out_release=False, robust_benefit_established=False,
                        launcher_failure=record["failure"])
        write(path, decision)
        raise
    finally:
        record["wall_seconds"] = time.perf_counter() - started
        write(journal, record)


if __name__ == "__main__":
    main()
