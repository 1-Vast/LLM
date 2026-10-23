"""Frozen two-dimensional quadratic counterexample; no biological files."""
import json
from pathlib import Path

import numpy as np


def main():
    source_design = np.diag([10.0, 1.0])
    inherited = np.linalg.inv(source_design.T @ source_design)
    initial = np.ones(2)
    result = {"biological_inputs_read": False, "theta0": initial.tolist(), "scenarios": []}
    for name, design in [("shared_curvature", source_design), ("swapped_curvature", np.diag([1.0, 10.0]))]:
        hessian = design.T @ design
        gradient = hessian @ initial
        candidates = {"source_fixed_preconditioner_eta1": inherited,
                      "fixed_scalar_sgd_eta001": .01 * np.eye(2),
                      "ordinary_same_support_newton": np.linalg.inv(hessian)}
        values = {}
        for candidate, preconditioner in candidates.items():
            updated = initial - preconditioner @ gradient
            eigenvalues = np.linalg.eigvals(preconditioner @ hessian).real
            values[candidate] = {"theta_after": updated.tolist(),
                                 "loss_after": float(.5 * updated @ hessian @ updated),
                                 "max_eigenvalue_PH": float(eigenvalues.max()),
                                 "stable_extra_step_multiplier_open_interval": [0, float(2 / eigenvalues.max())]}
        result["scenarios"].append({"name": name, "support_design": design.tolist(),
                                    "initial_loss": float(.5 * initial @ hessian @ initial), "updates": values})
    shared, swapped = result["scenarios"]
    assert shared["updates"]["source_fixed_preconditioner_eta1"]["loss_after"] < 1e-20
    assert swapped["updates"]["source_fixed_preconditioner_eta1"]["loss_after"] > swapped["initial_loss"]
    assert swapped["updates"]["fixed_scalar_sgd_eta001"]["loss_after"] < swapped["initial_loss"]
    assert swapped["updates"]["ordinary_same_support_newton"]["loss_after"] < 1e-20
    path = Path("log/20261022/early_update_mechanism/recursive/CURVATURE_RESULT.json")
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
