"""Exact finite-support residual-invariance witness, not a method replication."""
from collections import defaultdict
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/response_law_revision/root'


def delta_hsic(rows):
    joint, pa, pb = defaultdict(F), defaultdict(F), defaultdict(F)
    for a, b, p in rows:
        joint[a, b] += p
        pa[a] += p
        pb[b] += p
    return sum((joint[a, b] - pa[a] * pb[b]) ** 2 for a in pa for b in pb)


if __name__ == '__main__':
    atoms = [(d, x, d*x, F(1, 4)) for d in (-1, 1) for x in (-1, 1)]
    residual_laws = {str(d): {str(r): str(sum(p for dd, x, y, p in atoms if dd == d and y == r) * 2)
                              for r in (-1, 1)} for d in (-1, 1)}
    conditional = {str((d, x)): d*x for d in (-1, 1) for x in (-1, 1)}
    marginal = delta_hsic([(y, d, p) for d, x, y, p in atoms])
    joint = delta_hsic([((y, x), d, p) for d, x, y, p in atoms])
    pooled_risk = sum(p * y*y for d, x, y, p in atoms)
    interaction_risk = sum(p * (d*x-y)**2 for d, x, y, p in atoms)
    assert residual_laws['-1'] == residual_laws['1']
    assert marginal == 0 and joint > 0
    assert pooled_risk == 1 and interaction_risk == 0
    result = dict(atoms=[dict(domain=d, x=x, y=y, probability=str(p)) for d, x, y, p in atoms],
                  residual_laws=residual_laws, conditional_means=conditional,
                  delta_kernel_population_HSIC_residual_domain=str(marginal),
                  delta_kernel_population_HSIC_joint_residual_input_domain=str(joint),
                  pooled_MSE=str(pooled_risk), ordinary_interaction_MSE=str(interaction_risk),
                  code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope='Exact unrestricted-gate witness, not CICME replication, biological experiment or novelty evidence')
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'GATE_RESULT.json'
    assert not target.exists()
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
