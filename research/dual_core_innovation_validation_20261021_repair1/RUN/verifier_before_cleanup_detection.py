"""Verify stored repair artifacts; no training, candidate execution or API calls."""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    checks = []
    def check(condition, name):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    original = read(HERE / 'ORIGINAL_SNAPSHOT.json')
    old = HERE.parents[1] / original['source']
    current = {p.relative_to(old).as_posix(): sha(p) for p in old.rglob('*')
               if p.is_file() and '__pycache__' not in p.parts}
    check(current == original['files'], 'original package byte-identical and no added files')
    out = HERE / 'RUN'
    freeze = read(out / 'REGRESSION_FREEZE.json')
    for name, value in freeze['files'].items():
        check(sha(HERE / name) == value, 'regression freeze: ' + name)
    if (HERE / 'MANIFEST.json').exists():
        for name, value in read(HERE / 'MANIFEST.json')['files'].items():
            check(sha(HERE / name) == value, 'manifest: ' + name)
    check(read(out / 'REPRODUCIBILITY.json')['same_seed_full_30_epoch_cuda_training_bitwise_equal'], 'full seeded CUDA retraining identical')
    preparation = read(out / 'preparation.json')
    train = set(preparation['train_lineages'])
    sel = {r['lineage'] for r in preparation['episodes']['sel']}
    reg = {r['lineage'] for r in preparation['episodes']['final_regression']}
    check(not train & sel and not train & reg and not sel & reg, 'lineage allocations disjoint within this replay')
    summary = read(out / 'RESULTS.json')
    programs = read(out / 'chosen_programs.json')
    hashes = {hashlib.sha256(s.encode()).hexdigest() for s in programs.values()}
    expected = [r['cell'] for r in preparation['episodes']['final_regression']]
    stored_results = {}
    for arm, mean in summary['mean_hits'].items():
        results = read(out / f'regression_{arm}.json')
        stored_results[arm] = results
        check([r['episode_id'] for r in results] == expected, 'regression coverage: ' + arm)
        for result in results:
            tag = arm + ':' + result['episode_id']
            trace = result['trace']
            check(result['status'] == 'ok' and result['error'] is None, 'valid execution: ' + tag)
            check(result['source_sha256'] in hashes, 'chosen program: ' + tag)
            check(len({(t['kind'], t['drug']) for t in trace}) == len(trace), 'unique actions: ' + tag)
            check(result['spent'] == sum(t['cost'] for t in trace) <= 5., 'budget: ' + tag)
            check(result['yield'] == sum(t['value'] for t in trace if t['kind'] == 'f'), 'external score: ' + tag)
            check(result['f_used'] == sum(t['kind'] == 'f' for t in trace), 'functional count: ' + tag)
            check(result['m_used'] == sum(t['kind'] == 'm' for t in trace), 'molecular count: ' + tag)
            for i, event in enumerate(trace):
                check(event['cost'] == (1. if event['kind'] == 'f' else .5), 'query cost: ' + tag + ':' + str(i))
                if i:
                    check(event['model_before'] == trace[i-1]['model_after'], 'model chain: ' + tag + ':' + str(i))
                    check(event['predictions_before'] == trace[i-1]['predictions_after'], 'prediction refresh: ' + tag + ':' + str(i))
                support = event['update']['support_keys']
                check(support == [[t['kind'], t['drug']] for t in trace[:i+1]], 'paid support only: ' + tag + ':' + str(i))
        check(abs(float(np.mean([r['yield'] for r in results])) - mean) < 1e-12, 'mean hits: ' + arm)
    for name, a, b in [
        ('world_update_vs_static', 'world_updating', 'world_static'),
        ('world_update_vs_kernel', 'world_updating', 'kernel'),
        ('inherited_vs_fixed_updating', 'inherited_world', 'world_updating'),
        ('inherited_vs_restart', 'inherited_world', 'restart_world'),
        ('inherited_vs_conventional', 'inherited_world', 'conventional_world'),
        ('inherited_vs_b1', 'inherited_world', 'b1')]:
        pairs = list(zip(stored_results[a], stored_results[b]))
        differences = [x['yield'] - y['yield'] for x, y in pairs]
        check(abs(np.mean(differences) - summary['contrasts'][name]['mean_difference_hits']) < 1e-12, 'paired contrast: ' + name)
        groups = {}
        for (x, _), difference in zip(pairs, differences):
            groups.setdefault(x['lineage'], []).append(difference)
        rng = np.random.default_rng(0); lineages = sorted(groups)
        draws = [np.mean([v for lin in rng.choice(lineages, len(lineages)) for v in groups[lin]]) for _ in range(2000)]
        check(np.allclose(np.percentile(draws, [2.5, 97.5]), summary['contrasts'][name]['descriptive_cluster_interval95']), 'cluster interval: ' + name)
    transfer = read(out / 'transfer.json')
    check(len(transfer) == 3 * len(expected), 'all transfer modes evaluated')
    for row in transfer:
        check(not set(row['support_reserved']) & set(row['target_drugs']), 'transfer excludes all support: ' + row['cell'] + row['mode'])
        check(all(d in row['support_reserved'] for u in row['updates'] for _, d in u['support_keys']), 'transfer paid support provenance: ' + row['cell'] + row['mode'])
    for arm in ('inherit', 'restart'):
        archive = read(out / f'{arm}_archive.json')
        attempts = read(out / f'{arm}_attempts.json')
        selection = summary['selection'][arm]
        check(len(attempts) == 3, 'three candidate slots: ' + arm)
        check(sum(a['episode_evaluations'] for a in archive['attempts']) == selection['episode_evaluations_including_root'], 'actual evaluation accounting: ' + arm)
        check(selection['episode_evaluations_including_root'] == 4 * len(preparation['episodes']['sel']), 'equal evaluated suite size: ' + arm)
        if arm == 'restart':
            check(all(a['parent_id'] == archive['root_id'] for a in attempts), 'restart inherits root only')
    ledger = [json.loads(line) for line in (out / 'api_ledger.jsonl').read_text().splitlines()]
    check(len(ledger) == 6 and sum(r['http_attempts'] for r in ledger) == 6, 'bounded API requests and attempts')
    check(all(sum(r['arm'] == arm for r in ledger) == 3 for arm in ('inherit', 'restart')), 'matched API request counts')
    check(sum(r['total_tokens'] for r in ledger) <= 24000 and not any(r['usage_unknown'] for r in ledger), 'known bounded provider usage')
    check(len({r['prompt_sha256'] for r in ledger}) == 6 and all(r['temperature'] == .7 for r in ledger), 'diverse prompt contexts and explicit sampling')
    for record in ledger:
        check(hashlib.sha256(json.dumps(record['messages'], sort_keys=True).encode()).hexdigest() == record['prompt_sha256'], 'stored full prompt hash')
    print(f'VERIFY OK: {len(checks)} checks; no training, programs or API executed')
    return len(checks)


if __name__ == '__main__':
    verify()
