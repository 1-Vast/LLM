"""Audit only saved five-column development results; never reopen the workbook."""
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/interaction_error_diagnostic'
DEV = ['MCF7', 'MDAMB231', 'MCF10A', 'CAL27', 'CAL33']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = json.loads((OUT/'RESULTS.json').read_text())
    freeze = json.loads((OUT/'RUN_FREEZE.json').read_text())
    checked = 0

    def check(condition):
        nonlocal checked
        assert condition
        checked += 1

    for relative, expected in freeze['files'].items():
        check(digest(ROOT/relative) == expected)
    for key, name in [('prediction_sha256', 'PREDICTIONS.npz'),
                      ('pair_ids_sha256', 'PAIR_IDS.json'),
                      ('plan_sha256', 'PLAN.md'),
                      ('amendment_sha256', 'AMENDMENT_BEFORE_VALUES.md')]:
        check(result[key] == digest(OUT/name))
    check(result['code_sha256'] == digest(ROOT/'research/interaction_error_diagnostic_20261023/run.py'))
    check(result['data']['parsed_score_columns'] == DEV)
    check(result['data']['unparsed_score_columns'] == ['A549', 'A427'])
    pairs = [tuple(pair) for pair in json.loads((OUT/'PAIR_IDS.json').read_text())]
    check(len(pairs) == 11621 and len(set(pairs)) == len(pairs))
    check(all(a < b and not {a, b} & {'AAVS', 'nontargeting'} for a, b in pairs))
    genes = {g for pair in pairs for g in pair}
    check(len(genes) == 225)
    check(result['data']['canonical'] - sum(result['data']['exclusions'].values()) == len(pairs))
    with np.load(OUT/'PREDICTIONS.npz', allow_pickle=False) as arrays:
        check(arrays['development_scores'].shape == (11621, 5))
        check(arrays['gene_incidence'].shape == (11621, 225))
        check(not any('A549' in key or 'A427' in key for key in arrays.files))
        saved = {}
        for record in result['records']:
            context, salt, budget = (record[k] for k in ('context', 'salt', 'budget'))
            prefix = f'{context}_{salt}_{budget}'
            support, query = (arrays[prefix+'_'+k] for k in ('support', 'query'))
            train, valid = (arrays[prefix+'_'+k] for k in ('inner_train', 'inner_valid'))
            check(len(support) == budget and len(query) == 11621-512)
            check(not set(support) & set(query))
            check(set(train) | set(valid) == set(support) and not set(train) & set(valid))
            check(np.array_equal(arrays[prefix+'_truth'], arrays['development_scores'][query, DEV.index(context)]))
            check(record['support_hash'] == hashlib.sha256(support.tobytes()).hexdigest())
            check(record['query_hash'] == hashlib.sha256(query.tobytes()).hexdigest())
            check(all(np.isfinite(arrays[prefix+'_'+method]).all() for method in record['metrics']))
            saved[context, salt, budget] = (support, query)
        for context in DEV:
            for salt in (0, 1):
                small, q_small = saved[context, salt, 128]
                large, q_large = saved[context, salt, 512]
                check(np.array_equal(small, large[:128]) and np.array_equal(q_small, q_large))
    wins = []
    for summary in result['aggregate']:
        count = 0
        for row in summary['contexts']:
            comparison = row['comparison']
            win = all(comparison[m]['identity_ordinary'] < comparison[m]['score_direct']
                      for m in ('mse', 'bottom20_regret'))
            check(win == row['joint_win'])
            count += win
        check(count == summary['joint_wins'])
        wins.append(count)
    check(wins == [0, 2] and result['screening_gate'] is False)
    report = dict(status='PASS', checks=checked, freeze_files=len(freeze['files']),
                  eligible=len(pairs), genes=len(genes), records=len(result['records']),
                  joint_wins=wins, gate=False, workbook_reopened=False,
                  fitting_or_metric_reproduction=False,
                  scope='Saved-result identity/split/hash boundary audit, not original assay authentication.',
                  code_sha256=digest(Path(__file__)))
    destination = OUT/'source/RESULT_BOUNDARY_AUDIT.json'
    assert not destination.exists()
    destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
