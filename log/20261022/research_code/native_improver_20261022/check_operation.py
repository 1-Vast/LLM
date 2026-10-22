"""Exact synthetic falsifiers. No assay import, biological fitting or model call."""
import hashlib
import itertools
import json
from fractions import Fraction as Q
from pathlib import Path


ROOT = Path("D:/MAESTRO")
OUT = ROOT / "log/20261022/native_operation/improver"


def proposed_update(theta, gradients, beta):
    return tuple(x - sum(b * g[i] for b, g in zip(beta, gradients)) for i, x in enumerate(theta))


def proposed_outer(theta, gradients, beta, target, rho=Q(1)):
    updated = proposed_update(theta, gradients, beta)
    return tuple(b + rho * sum(g[i] * (updated[i] - target[i]) for i in range(len(theta)))
                 for b, g in zip(beta, gradients))


def conventional_bilevel(theta, gradients, beta, target, rho=Q(1)):
    # Direct derivative of F(theta-G beta), computed separately as a quadratic.
    linear = [sum(g[i] * (theta[i] - target[i]) for i in range(len(theta))) for g in gradients]
    gram = [[sum(a * b for a, b in zip(g, h)) for h in gradients] for g in gradients]
    return tuple(beta[j] + rho * (linear[j] - sum(gram[j][k] * beta[k] for k in range(len(beta))))
                 for j in range(len(beta)))


def loss(theta, target):
    return sum((x - y) ** 2 for x, y in zip(theta, target)) / 2


def main():
    seal = json.loads((OUT / "INDEPENDENT_SEAL.json").read_text(encoding="utf-8"))
    checks = [{"path": entry["path"],
               "pass": hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest() == entry["sha256"]}
              for entry in seal["files"]]
    assert all(item["pass"] for item in checks), "sealed input changed"
    source_theta, source_target = (Q(0), Q(0)), (Q(1), Q(0))
    source_gradients = ((Q(-1), Q(0)), (Q(0), Q(-1)))
    old = (Q(1, 2), Q(1, 2))
    new = proposed_outer(source_theta, source_gradients, old, source_target)
    conventional = conventional_bilevel(source_theta, source_gradients, old, source_target)
    assert new == conventional == (Q(1), Q(0))
    later_theta, later_target = (Q(1), Q(1)), (Q(3), Q(1))
    later_gradients = ((Q(-2), Q(0)), (Q(0), Q(-2)))
    later_losses = {name: loss(proposed_update(later_theta, later_gradients, beta), later_target)
                    for name, beta in [("old", old), ("new", new), ("conventional", conventional)]}
    assert later_losses == {"old": Q(1), "new": Q(0), "conventional": Q(0)}
    # Exhaustive finite coefficient/target/rho grid: no floating tolerance.
    equivalences = 0
    for values in itertools.product((Q(-1), Q(0), Q(1)), repeat=5):
        beta, target, rho = values[:2], values[2:4], values[4]
        assert proposed_outer(later_theta, later_gradients, beta, target, rho) == conventional_bilevel(
            later_theta, later_gradients, beta, target, rho)
        equivalences += 1
    collinear = 0
    gradients = ((Q(-1), Q(0)), (Q(-2), Q(0)))
    for beta in itertools.product((Q(-1), Q(0), Q(1)), repeat=2):
        scalar = beta[0] + 2 * beta[1]
        expected = (later_theta[0] + scalar, later_theta[1])
        assert proposed_update(later_theta, gradients, beta) == expected
        collinear += 1
    menu = [(Q(1, 2), Q(1, 2)), (Q(1), Q(0)), (Q(0), Q(1))]
    selected = min(menu, key=lambda beta: loss(proposed_update(source_theta, source_gradients, beta), source_target))
    assert selected == new
    result = {
        "scope": "EXACT_SYNTHETIC_OPERATION_AUDIT_NOT_BIOLOGICAL_OR_TRANSFER_EVIDENCE",
        "common_later_start": list(map(str, later_theta)),
        "old_beta": list(map(str, old)), "new_beta": list(map(str, new)),
        "later_external_loss": {key: str(value) for key, value in later_losses.items()},
        "new_minus_old_utility": "1", "new_minus_faithful_conventional_utility": "0",
        "exact_outer_update_equivalence_cases": equivalences,
        "collinear_scalar_step_equivalence_cases": collinear,
        "finite_program_search_menu": [[str(v) for v in beta] for beta in menu],
        "finite_search_selected_beta": list(map(str, selected)),
        "finite_search_source_evaluations": 3,
        "meta_rule_source_oracle": "one exact outer derivative of synthetic quadratic; no claim of free assay derivative",
        "downstream_update_count_each": 1,
        "independence": "source/later quadratic examples constructed to share the optimum beta; not independent empirical tasks",
        "sealed_inputs": checks,
        "new_biological_values_accessed": 0, "biological_predictive_fits": 0, "api_calls": 0,
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "OPERATION_CHECK.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "sealed_inputs"}, indent=2))


if __name__ == "__main__":
    main()
