"""Exact reconstruction of the API's own counterexample, without importing its code."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/reusable_error_mechanism'


def main():
    assert not (OUT / 'MARGIN_CHECK.json').exists()
    bindings = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [OUT / 'MARGIN_CHECK_PROTOCOL.md', OUT / 'api/PROPOSAL.md', Path(__file__)]}
    (OUT / 'MARGIN_CHECK_FREEZE.json').write_text(json.dumps(bindings, indent=2), encoding='utf-8')
    values = {'A': F(3, 10), 'B': F(-1)}
    records = []
    for order in [('A', 'B'), ('B', 'A')]:
        delta = F(0)
        trace = []
        for name in order:
            old = delta
            failed = int(values[name] < 0)
            success = int(values[name] >= old)
            delta = old + F(3, 5) * (failed - success)
            trace.append(dict(name=name, y=str(values[name]), old=str(old),
                              failed=failed, success=success, new=str(delta)))
        records.append(dict(order=''.join(order), trace=trace, final=str(delta),
                            accept_q_two_fifths=F(2, 5) >= delta))
    assert [r['final'] for r in records] == ['0', '3/5']
    assert [r['accept_q_two_fifths'] for r in records] == [True, False]
    result = dict(records=records, result='FAIL_LITERAL_BATCH_ORDER_INVARIANCE',
                  biological_fits=0, scope='Independent exact reconstruction of a proposal-supplied witness')
    (OUT / 'MARGIN_CHECK.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
