"""Single A matrix with a hard1800-second child limit and no replay."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parents[3] / "data/processed/functional_anchor_binding_20261030/a"

def write(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    journal = OUT / "launcher.json"
    assert not journal.exists(), "No automatic replay"
    record = {"status": "running", "timeout_seconds": 1800, "python": sys.executable, "exit_code": None}
    started = time.perf_counter()
    write(journal, record)
    try:
        result = subprocess.run([sys.executable, str(ROOT / "a.py")], timeout=1800)
        record["exit_code"] = result.returncode
        if result.returncode:
            raise RuntimeError(f"Child exit{result.returncode}")
        run = json.loads((OUT / "run.json").read_text())
        assert run["status"] == "complete" and run["completed_nulls"] == 49
        record.update(status="complete", exit_code=result.returncode)
    except Exception as exc:
        record.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        run_path = OUT / "run.json"
        run = json.loads(run_path.read_text()) if run_path.exists() else {}
        run.update(status="failed", launcher_failure=record["failure"],
            launcher_wall_seconds=time.perf_counter() - started,
            child_cpu_seconds_unavailable_after_forced_stop=run.get("cpu_seconds") is None)
        write(run_path, run)
        write(OUT / "decision.json", {"status": "NO_HELD_OUT_RELEASE", "information_gate_pass": False,
            "held_out_release": False, "robust_benefit_established": False,
            "conditional_interval_above_zero": False, "launcher_failure": record["failure"]})
        raise
    finally:
        record["wall_seconds"] = time.perf_counter() - started
        write(journal, record)

if __name__ == "__main__":
    main()
