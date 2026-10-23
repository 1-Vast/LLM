"""Synthetic identifiability check; no biological files or outcomes read."""
import json
from pathlib import Path

import numpy as np


def main():
    # Coordinatewise mixed-state curvature theta; frozen quadratic readout
    # h(z) = w'z + eta ||z||^2. Work at theta=0 for the local update.
    w = np.array([1.0, 1.0])
    eta = 0.5
    xa = np.array([[1.0, 1.0], [1.0, 1.0]])
    xb = np.array([[1.0, 2.0], [2.0, 1.0]])
    q = xa * xb
    g = w + 2 * eta * (xa + xb)
    design = q * g
    theta = np.array([0.2, -0.3])
    feedback = design @ theta
    recovered = np.linalg.solve(design, feedback)
    direct = np.linalg.lstsq(design, feedback, rcond=None)[0]
    fixed_g = np.tile(np.array([1.0, 1.0]), (2, 1))
    # Same q rows are needed to expose why g variation can add constraints.
    same_q = np.ones((2, 2))
    varying_readout = np.array([[1.0, 0.0], [0.0, 1.0]])
    fixed_rank = np.linalg.matrix_rank(same_q * fixed_g)
    varying_rank = np.linalg.matrix_rank(same_q * varying_readout)
    assert fixed_rank == 1 and varying_rank == 2
    assert np.max(np.abs(theta - recovered)) < 1e-12
    assert np.max(np.abs(recovered - direct)) < 1e-12
    out = {
        "scope": "synthetic local identifiability only; no performance claim",
        "design": design.tolist(),
        "theta": theta.tolist(),
        "recovered": recovered.tolist(),
        "same_q_fixed_gradient_rank": int(fixed_rank),
        "same_q_varying_gradient_rank": int(varying_rank),
        "max_same_information_direct_difference": float(np.max(np.abs(recovered - direct))),
        "new_biological_values": 0,
    }
    target = Path("log/20261023/mixed_feedback_estimator/constructive/WITNESS.json")
    target.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
