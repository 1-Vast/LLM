"""Frozen synthetic gradient signs and ordinary crossloss ridge equivalence."""
import json
from pathlib import Path

import numpy as np


def main():
    g = np.array([1., 2.])
    matrices = {"identity": np.eye(2), "source_curvature": np.diag([.01, 1.]),
                "coupled_SPD": np.array([[1., 2.], [2., 5.]])}
    results = []
    for name, matrix in {**matrices, "unconstrained_negative_identity": -np.eye(2)}.items():
        updated = -.01 * matrix @ g
        molecular = .5 * np.sum((updated + g) ** 2)
        functional = .5 * np.sum((updated - g) ** 2)
        derivative = float(g @ matrix @ g)
        if name in matrices:
            assert np.linalg.eigvalsh(matrix).min() > 0
            assert derivative > 0 and functional > 2.5 and molecular < 2.5
        else:
            assert derivative < 0 and functional < 2.5 and molecular > 2.5
        results.append({"name": name, "functional_derivative_at_eta0": derivative,
                        "molecular_loss_at_eta001": float(molecular),
                        "functional_loss_at_eta001": float(functional)})
    gm, gq = np.array([1., 0.]), np.array([-1., 1.])
    not_collinear = {"raw_inner_product": float(gq @ gm),
                     "transported_inner_product": float(gq @ matrices["coupled_SPD"] @ gm)}
    assert not_collinear == {"raw_inner_product": -1., "transported_inner_product": 1.}

    x = np.array([[1., 0., 1., 2.], [0., 1., 2., -1.]])
    y, ridge = -x, .1
    transport = y @ x.T @ np.linalg.inv(x @ x.T + ridge * np.eye(2))
    design = np.vstack([x.T, np.sqrt(ridge) * np.eye(2)])
    ordinary = np.stack([np.linalg.lstsq(design, np.concatenate([row, np.zeros(2)]), rcond=None)[0] for row in y])
    error = float(np.max(np.abs(transport - ordinary)))
    assert error < 1e-12
    result = {"biological_inputs_read": False, "initial_losses": 2.5, "negative_collinear": results,
              "negative_noncollinear": not_collinear,
              "ordinary_crossloss_ridge": {"transport": transport.tolist(), "normal_equation_maxabs_error": error}}
    output = Path("log/20261022/early_update_mechanism/recursive/CROSSLOSS_RESULT.json")
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
