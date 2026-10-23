"""Finite semantic-search arithmetic. No biology or generated-code execution."""
from fractions import Fraction as F
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'log/20261023/update_strategy_renewal/critic'

def execute(program, e):
    a, b = program
    return a*e+b*e*(e-1)

# Explicit coefficient tuples are locally reviewed operations, not author code.
programs = [(F(1),F(0))]*100+[(F(2),F(0)),(F(1),F(1))]
sig = lambda p, probes: tuple(execute(p,F(e)) for e in probes)
counts = {str(probes):len({sig(p,probes) for p in programs}) for probes in ((0,),(1,),(1,2))}
assert counts == {'(0,)':1,'(1,)':2,'(1, 2)':3}
# A and C collide at e1 but at e3 differ3 versus9.
assert sig(programs[0],(1,)) == sig(programs[-1],(1,))
assert execute(programs[0],F(3)) == 3 and execute(programs[-1],F(3)) == 9
# e1 gives a, e2 gives2a+2b; recovered coefficients certify this polynomial grammar.
for p in programs:
    q1,q2 = sig(p,(1,2))
    assert (q1,(q2-2*q1)/2) == p
def cubic_extension(e):
    return e+e*(e-1)*(e-2)
assert all(cubic_extension(F(e)) == F(e) for e in (0,1,2))
assert cubic_extension(F(3)) == 9

n, unique, probes, fingerprint_unit = len(programs),3,2,1
costs = []
for true_eval in (10,1):
    costs.append(dict(true_evaluation_cost_units=true_eval,
        naive=n*true_eval,
        witness_search=n*probes*fingerprint_unit+unique*true_eval,
        ordinary_coefficient_canonicalization=n*fingerprint_unit+unique*true_eval))
result = dict(signature_class_counts=counts,
    omitted_witness_failure=dict(common_e1_signature='1',future_e3_A='3',future_e3_C='9'),
    exact_grammar='theta_new=theta+a*e+b*e*(e-1), rational coefficients',
    grammar_extension_failure='e+e*(e-1)*(e-2) agrees with e at0,1,2 but gives9 rather than3 at e3',
    costs=costs,
    condition='(N-unique)*true_eval > N*probe_count*probe_cost plus discovery/validation costs',
    interpretation='Stipulated duplicates/costs and handchosen probes; not a learned policy or biological result.')
(OUT/'SEMANTIC_WITNESS_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
