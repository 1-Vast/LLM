"""Rank audit of a proposed measurement-intervention design, not assay data."""
from fractions import Fraction
import json
from pathlib import Path

def rank(rows):
    a = [[Fraction(x) for x in row] for row in rows]
    pivot = 0
    for col in range(len(a[0])):
        found = next((i for i in range(pivot, len(a)) if a[i][col]), None)
        if found is None:
            continue
        a[pivot], a[found] = a[found], a[pivot]
        scale = a[pivot][col]
        a[pivot] = [x / scale for x in a[pivot]]
        for i in range(len(a)):
            if i != pivot:
                scale = a[i][col]
                a[i] = [x - scale*y for x, y in zip(a[i], a[pivot])]
        pivot += 1
        if pivot == len(a):
            break
    return pivot

# Locally alpha=Q=N=m=1, beta=0. Unknown order: alpha,beta,N,m.
# y(s)=alpha*(N*m+s)+beta; cell-free same-matrix blank measures beta.
# Orthogonal viability-gated count measures N under its own audited model.
unspiked = [1, 1, 1, 1]
spiked = [2, 1, 1, 1]
blank = [0, 1, 0, 0]
live_count = [0, 0, 1, 0]
designs = {
    'unspiked_only': [unspiked],
    'unspiked_plus_spike': [unspiked, spiked],
    'plus_same_matrix_blank': [unspiked, spiked, blank],
    'plus_orthogonal_live_count': [unspiked, spiked, blank, live_count],
}
results = {k: rank(v) for k, v in designs.items()}
assert results == {'unspiked_only': 1, 'unspiked_plus_spike': 2,
                   'plus_same_matrix_blank': 3, 'plus_orthogonal_live_count': 4}
out = {'local_jacobian_rank': results,
       'unknowns': ['detector_gain', 'background', 'live_cells', 'ATP_per_live_cell'],
       'scope': 'Conditional design rank at one nonsingular point; not global identification, biology, performance, or novelty.',
       'assumptions': ['linear detector over the spike interval', 'spike recovery matches endogenous ATP',
                       'same-matrix blank isolates background', 'orthogonal count is independently calibrated'],
       'conclusion': 'Spikes alone do not identify cell survival; independent live count and assay-valid controls are required.'}
root = Path(__file__).resolve().parents[3]
(root/'log/20261023/reusable_error_mechanism/critic/DESIGN_CHECK.json').write_text(json.dumps(out, indent=2))
print(json.dumps(out))
