"""Supplemental frozen-row and endpoint checks; no source access or retuning."""
import json

from .audit import HERE, OLD, PRIOR, read, sha, write


def main():
    plan = read(HERE / 'C45_SELECTION_VERIFIED.json')
    protocol = read(HERE / 'PROTOCOL.json')
    c44 = read(HERE / 'C44_UNION.json')
    c45 = read(HERE / 'C45_NUMERIC_RECONSTRUCTED.json')
    old = next(r['row_ids'] for r in read(OLD / 'RESULTS.json')['files'] if r['file'] == 'c44.h5ad')
    groups = [g for g in read(PRIOR / 'ROW_MANIFEST.json')['groups'] if g['file'] == 'c44.h5ad']
    expected = old + sorted(r for g in groups for r in g['discovery_rows']) + sorted(r for g in groups for r in g['holdout_rows'])
    assert c44['rows'] == expected and len(set(expected)) == 252
    assert c45['discovery_rows'] == plan['existing_discovery_rows'] + plan['rows']
    assert c45['consistency_rows'] == plan['existing_consistency_rows']
    assert not set(c45['discovery_rows']) & set(c45['consistency_rows'])
    assert protocol['c45']['additional_rows'] == plan['rows']
    assert protocol['c45']['existing_discovery_rows'] == plan['existing_discovery_rows']
    assert protocol['c45']['consistency_rows'] == plan['existing_consistency_rows']
    endpoint = protocol['endpoint']
    assert len(endpoint['weights']) == 39 and all(w == 1/39 for w in endpoint['weights'])
    assert endpoint['coordinates'] == read(PRIOR / 'PROTOCOL.json')['endpoint']['coordinates']
    assert endpoint['symbols'] == [r['gene'] for r in c44['records']] == [r['gene'] for r in c45['records']]
    for result in (c44, c45):
        assert result['source_revision'] == protocol['source_revision']
        assert len(result['records']) == 39 and all(r['passed'] for r in result['records'])
        assert not result['fresh_holdout'] and not result['P06_execution_released']
    receipt = dict(status='PASS_FROZEN_ROW_ENDPOINT_SCOPE', c44_rows=252, c45_discovery_rows=43,
                   c45_exposed_consistency_rows=14, protocol_sha256=sha(HERE / 'PROTOCOL.json'),
                   selection_sha256=sha(HERE / 'C45_SELECTION_VERIFIED.json'),
                   code_sha256=sha(HERE / 'scope_check.py'), new_network_requests=0)
    write(HERE / 'SCOPE_VERIFIED.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
