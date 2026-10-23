"""Metadata-only join of functional identities to standard molecular downloads."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_feedback_pilot'


def main():
    partition = json.loads((OUT / 'PARTITIONS.json').read_text(encoding='utf-8'))
    inventory = json.loads((OUT / 'molecular/STANDARD_JURKAT_DOWNLOADS.json').read_text(encoding='utf-8'))
    ids = set(d for drugs in partition['partitions'].values() for d in drugs)
    repo = {r['drug_repository_identity']: r for r in inventory}
    assert len(repo) == len(inventory) == 144
    normalize = lambda name: name.strip().replace('-', '')
    normalized = {normalize(name): name for name in repo}
    assert len(normalized) == len(repo), 'Do not merge ambiguous punctuation-normalized identities'
    matched = []
    for drug in sorted(ids):
        repository_drug = drug if drug in repo else normalized.get(normalize(drug))
        assert repository_drug is not None, drug
        split = next(k for k, v in partition['partitions'].items() if drug in v)
        matched.append({'drug': drug, 'repository_drug': repository_drug, 'partition': split, **repo[repository_drug]})
    assert len({r['repository_drug'] for r in matched}) == len(ids) == 144
    result = {'join_level': 'metadata identity and nominal protocol only; molecular row drug fields still unchecked',
              'scope': 'No molecular response values decoded; no extra molecular download', 'records': matched,
              'nonexact_aliases': [{'functional': r['drug'], 'repository': r['repository_drug']} for r in matched if r['drug'] != r['repository_drug']]}
    (OUT / 'MOLECULAR_DOWNLOAD_JOIN.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'matched': len(matched), 'nonexact_aliases': result['nonexact_aliases'],
                      'development': sum(r['partition'] == 'development' for r in matched)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
