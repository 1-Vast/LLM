"""Exact synthetic witness; no assay values, fitted biology or source execution."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "log/20261023/cxcl9_source_feasibility/constructive"


def dot(x, y):
    return sum(a*b for a, b in zip(x, y))


def residual(x, direction):
    return [a-dot(x, direction)/dot(direction, direction)*b
            for a, b in zip(x, direction)]


def main():
    # Two drug/cytokine contexts. A common action shift and a context gate.
    action = [F(1), F(1)]
    edge = [F(0), F(1)]
    defect = [F(0), F(1)]
    rp, hp = residual(defect, action), residual(edge, action)
    edge_update = dot(hp, rp)/dot(hp, hp)
    action_update = dot(action, [r-edge_update*h for r, h in zip(defect, edge)])/dot(action, action)
    scalar_update = dot(action, defect)/dot(action, action)
    scalar_sse = sum((r-scalar_update*j)**2 for r, j in zip(defect, action))
    corrected = [action_update*j+edge_update*h for j, h in zip(action, edge)]
    assert edge_update == 1 and action_update == 0
    assert scalar_sse == F(1, 2)
    assert corrected == defect
    # A direct model y = beta_0 + beta_gate*c2 fits exactly the same two columns.
    direct = [F(0)+F(1)*c2 for c2 in (0, 1)]
    assert direct == corrected
    # If edge and action have identical response signatures, projection vanishes.
    indistinguishable = residual(action, action)
    assert dot(indistinguishable, indistinguishable) == 0
    # Equal-budget exhaustive two-column least squares also gives (0,1).
    result = {
        "scope": "exact stipulated linear response witness only; no biological performance",
        "action_jacobian": list(map(str, action)),
        "edge_jacobian": list(map(str, edge)),
        "feedback_residual": list(map(str, defect)),
        "projected_residual": list(map(str, rp)),
        "edge_update": str(edge_update),
        "action_update": str(action_update),
        "scalar_only_sse": str(scalar_sse),
        "structural_sse": str(sum((r-y)**2 for r, y in zip(defect, corrected))),
        "direct_interaction_predictions": list(map(str, direct)),
        "ordinary_union_refit_predictions": list(map(str, corrected)),
        "nonidentifiable_edge_projected_norm": str(dot(indistinguishable, indistinguishable)),
        "conclusion": "scalar repair insufficient in witness; restricted edge repair equals direct interaction/union least squares",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "EXACT_WITNESS.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
