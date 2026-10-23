"""Exact finite source-equivalence falsifier; no biological or model training claims."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import hashlib
import json

ROOT = Path('log/20261022/next_mechanism/recursive')

def edit(name, x, lam):
    if name == 'A':
        return x + 1
    return 2*x + lam*x*(x-1)*(x-2)

def trajectory(start, sequence, lam):
    x = start
    trace = []
    for name in sequence:
        y = edit(name, x, lam)
        trace.append((name, x, y))
        x = y
    return trace

def main():
    laws = [F(0), F(-1, 9)]
    source = []
    exposed = set()
    for start in [F(0), F(1)]:
        for sequence in product('AB', repeat=2):
            left = trajectory(start, sequence, laws[0])
            right = trajectory(start, sequence, laws[1])
            assert left == right
            exposed.update((name, x) for name, x, _ in left)
            source.append(dict(start=str(start), sequence=''.join(sequence),
                observed=[dict(edit=name, input=str(x), output=str(y)) for name, x, y in left]))
    later = []
    for lam in laws:
        ab = trajectory(F(3), 'AB', lam)[-1][-1]
        ba = trajectory(F(3), 'BA', lam)[-1][-1]
        later.append(dict(law_parameter=str(lam), start='3', AB=str(ab), BA=str(ba),
                          order_difference=str(ab-ba), preferred_of_AB_BA='AB' if ab > ba else 'BA'))
    assert later[0]['order_difference'] == '1'
    assert later[1]['order_difference'] == '-1'
    result = dict(status='PASS_SOURCE_EQUIVALENCE_LATER_ORDER_REVERSAL',
        source=source, later=later,
        source_exposed_edit_inputs=[dict(edit=a, input=str(x)) for a, x in sorted(exposed)],
        arithmetic_costs=dict(source_trajectory_replays=16, source_edit_evaluations=32,
            later_trajectory_replays=4, later_edit_evaluations=8,
            unique_source_edit_input_pairs=6),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Exact synthetic indistinguishability; no probabilistic transfer lower bound, training result, biological evidence, or RSI evidence.')
    (ROOT/'FALSIFIER_RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['status','later','arithmetic_costs','scope']}, indent=2))

if __name__ == '__main__':
    main()
