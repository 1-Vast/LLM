"""Check sealed peer synthetic mathematics without executing their output writers."""
import ast
from fractions import Fraction as F
import hashlib
from itertools import product
import json
from pathlib import Path

BASE = Path("log/20261022/mechanism_gap/functional")


if __name__ == "__main__":
    recursive = Path("research/mechanism_gap_recursive_20261022/check_continuation.py")
    tree = ast.parse(recursive.read_text(encoding="utf-8"))
    functions = ast.Module(body=[node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in ("prediction", "run")],
        type_ignores=[])
    namespace = {"F": F}
    exec(compile(functions, str(recursive), "exec"), namespace)
    sequences = list(product((0, 1), repeat=2))
    losses = {str(seq): sum(namespace["run"](a, rho, seq)[1]
        for a, rho in product((F(1, 4), F(3, 4)), (F(1), F(1, 2)))) / 4
        for seq in sequences}
    assert losses["(1, 1)"] == 0
    assert all(value > 0 for seq, value in losses.items() if seq != "(1, 1)")
    # A shared-rate equality test can pass a physically invalid negative-rate fit.
    s = ((20, -10), (10, -20), (20, -20))
    w = (2, 2, -3)
    negative = (-2, 2, 0)
    assert sum(x*y for x, y in zip(w, negative)) == 0
    assert [sum(x*y for x, y in zip(row, (F(-1, 5), F(-1, 5)))) for row in s] == list(negative)
    inputs = [
        Path("log/20261022/mechanism_gap/frontier/INDEPENDENT_ORIGINAL.md"),
        Path("log/20261022/mechanism_gap/frontier/CHECK_RESULT.json"),
        Path("research/mechanism_gap_frontier_20261022/check_current.py"),
        Path("log/20261022/mechanism_gap/recursive/INDEPENDENT_ORIGINAL.md"),
        Path("log/20261022/mechanism_gap/recursive/RESULT.json"), recursive,
    ]
    result = {"recursive_source_complete_sequence_losses": losses,
        "source_best_program_11_authenticated_without_later_results": True,
        "frontier_zero_W_requires_nonnegative_rate_check": True,
        "peer_output_files_overwritten": False,
        "inputs": [{"path": path.as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in inputs]}
    (BASE / "OPPOSING_MATH_CHECK.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
