"""Small source-only regression checks; no biological inputs or fitted results are loaded."""
from pathlib import Path
import subprocess
import sys

GATES = Path(__file__).resolve().parents[1] / "certified_discovery_gates_20261023"
sys.path.insert(0, str(GATES))

from gate1 import BETTORS, GATE1_BUDGETS, REQUIRED_POOLS, gate1a_decision  # noqa: E402


def passing_cells():
    return {f"{pool}|{bettor}|c{budget}|stop{stop}": {"pass": True}
            for pool in REQUIRED_POOLS for bettor in BETTORS for budget in GATE1_BUDGETS for stop in (1, 2)}


def test_skipped_required_pool_is_incomplete():
    cells = {k: v for k, v in passing_cells().items() if not k.startswith("J-P2|")}
    result = gate1a_decision(cells, {"J-P2": "undersized"}, True)
    assert result["gate1a_label"] == "GATE1_DIAGNOSTIC_INCOMPLETE"
    assert result["gate1a_missing_cells"]
    assert not result["gate1a_diagnostic_complete"]


def test_missing_single_cell_is_incomplete_without_skip_marker():
    cells = passing_cells()
    cells.pop(next(iter(cells)))
    assert gate1a_decision(cells, {}, True)["gate1a_label"] == "GATE1_DIAGNOSTIC_INCOMPLETE"


def test_complete_pass_stays_diagnostic_and_invalid_bets_fail():
    result = gate1a_decision(passing_cells(), {}, True)
    assert result["gate1a_label"] == "GATE1_DIAGNOSTIC_PASS"
    assert result["mathematical_certification"] == "NOT_ESTABLISHED"
    assert gate1a_decision(passing_cells(), {}, False)["gate1a_label"] == "GATE1_DIAGNOSTIC_FAIL"
    cells = passing_cells()
    cells[next(iter(cells))]["pass"] = False
    assert gate1a_decision(cells, {}, True)["gate1a_label"] == "GATE1_DIAGNOSTIC_FAIL"


def test_synthetic_harness_process_exit_codes(tmp_path):
    code = """import sys
sys.path.insert(0, sys.argv[1])
import test_synthetic as harness
mode, out = sys.argv[2:4]
harness.t1_log_lr = lambda: mode == 'pass'
harness.import_certification = lambda: None
selection = 'unknown' if mode == 'empty' else 't1'
sys.argv = ['test_synthetic.py', '--only', selection, '--out', out]
raise SystemExit(harness.main())
"""
    for mode, expected in (("pass", 0), ("fail", 1), ("empty", 1)):
        proc = subprocess.run([sys.executable, "-B", "-c", code, str(GATES), mode, str(tmp_path / f"{mode}.txt")],
                              capture_output=True, text=True)
        assert proc.returncode == expected, proc.stdout + proc.stderr
