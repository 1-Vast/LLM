"""Complete bounded repair replay: selection, code archive, freeze, regression."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch

from repair_model import build_model, FeedbackBackend, KernelBackend, StaticBackend
from repair_runner import run_program, checked_result, check_source
from repair_archive import Archive, checked_evidence, source_hash
from repair_proposer import propose
from prepare_replay import save_json

HERE = Path(__file__).resolve().parent
BASE = '''def choose(obs):
    remaining = [d for d in obs['drugs'] if d not in obs['queried_f']]
    if obs['budget_left'] < 1 or not remaining:
        return {'kind': 'stop'}
    drug = max(remaining, key=lambda d: (obs['predictions'][d], d))
    return {'kind': 'f', 'drug': drug}
'''
MOLECULAR = '''def choose(obs):
    if not obs['queried_m'] and obs['step'] == 0:
        drug = min(obs['available_m'], key=lambda d: (abs(obs['predictions'][d] - 0.5), d))
        return {'kind': 'm', 'drug': drug}
    remaining = [d for d in obs['drugs'] if d not in obs['queried_f']]
    if obs['budget_left'] < 1 or not remaining:
        return {'kind': 'stop'}
    return {'kind': 'f', 'drug': max(remaining, key=lambda d: (obs['predictions'][d], d))}
'''
PRIOR = BASE.replace("obs['predictions'][d]", "obs['nn'][d]")
BLEND = BASE.replace("obs['predictions'][d]", "0.5 * obs['predictions'][d] + 0.5 * obs['nn'][d]")
FALLBACKS = [MOLECULAR, PRIOR, BLEND]


def backend_for(mode, model, entry):
    episode = entry['episode']; drugs = episode['drugs']
    if mode == 'world':
        return FeedbackBackend(model, entry['inputs'], dict(zip(drugs, range(len(drugs)))))
    if mode == 'kernel':
        return KernelBackend(episode['nn'], dict(zip(drugs, entry['features'])))
    return StaticBackend(episode['nn'] if mode == 'b1' else episode['W'])


def evaluate(source, entries, mode, model):
    results = []
    for entry in entries:
        ep = dict(entry['episode'], episode_id=entry['cell'])
        result = run_program(source, ep, backend_for(mode, model, entry), timeout=15)
        if result['source_sha256'] != source_hash(source):
            raise RuntimeError('Runner evaluated a different source')
        result.update(cell=entry['cell'], lineage=entry['lineage'])
        results.append(result)
    return results


def evidence_summary(results):
    evidence = checked_evidence(results)
    return {'mean_yield': evidence['mean_yield'], 'evidence_sha256': evidence['sha256'],
            'episodes': [{'id': i, 'yield': r['yield'],
                          'actions': [{'kind': t['kind'], 'before_p': round(t['predictions_before'][t['drug']], 4),
                                       'label': t['value'] if t['kind'] == 'f' else None,
                                       'prediction_change': round(t['prediction_max_abs_change'], 6)} for t in r['trace']]}
                         for i, r in enumerate(results)]}


def search(arm, entries, model, out, api):
    path = out / f'{arm}_archive.json'
    if path.exists():
        archive = Archive.load(path)
        attempts = json.loads((out / f'{arm}_attempts.json').read_text())
        if len(archive.attempts) != len(attempts) + 1:
            raise RuntimeError('Inconsistent selection checkpoint; refuse repeated evaluation')
        # Saved authoritative evidence contains every score, trace and source/context hash.
        # Rehydrate that evidence, without rerunning an episode or replacing any value.
        by_node = {key: [dict(row, status='ok', error=None) for row in node['evidence']['episodes']]
                   for key, node in archive.nodes.items()}
    else:
        archive = Archive(mode=arm, suite_id='original_selection_lineages_exposed')
        root_results = evaluate(BASE, entries, 'world', model)
        archive.add(BASE, root_results)
        by_node = {archive.root_id: root_results}
        attempts = []
        save_json(out / f'{arm}_root_results.json', root_results)
    for generation in range(len(attempts), 3):
        parent = archive.select_parent()
        evidence = evidence_summary(by_node[parent['id']])
        previous = [{'status': a['archive_status'], 'mean_yield': a['mean_yield'],
                     'rationale': a['rationale']} for a in attempts]
        rec = {'status': 'offline', 'rationale': 'Predeclared conventional fallback'}
        source = None
        if api:
            source, rec = propose(out, arm, generation, parent, evidence, previous)
        reason = None
        if source is not None:
            try:
                check_source(source)
                if not archive.needs_evaluation(source):
                    reason = 'duplicate_source'
            except (ValueError, SyntaxError):
                reason = 'invalid_source'
        else:
            reason = 'no_api_program'
        origin = 'api'
        if reason:
            source = next((s for s in FALLBACKS if archive.needs_evaluation(s)), None)
            if source is None:
                raise RuntimeError('No distinct predeclared fallback remains')
            origin = 'conventional_fallback'
        results = evaluate(source, entries, 'world', model)
        tag = f'{arm}_g{generation + 1}'
        (out / f'{tag}.py').write_text(source, encoding='utf-8')
        save_json(out / f'{tag}_results.json', results)
        try:
            added = archive.add(source, results, parent_id=parent['id'])
        except ValueError:
            if all(r['status'] == 'ok' and r['error'] is None for r in results):
                raise  # Source/context mismatches are harness defects, not candidate failures.
            # A runtime-invalid candidate spent its slot but provides no score/evidence.
            attempts.append({'generation': generation, 'parent_id': parent['id'], 'origin': origin,
                             'proposal_status': rec['status'], 'fallback_reason': reason,
                             'archive_status': 'invalid', 'mean_yield': None, 'accepted': False,
                             'rationale': rec.get('rationale', ''), 'errors': [r['error'] for r in results]})
            archive.save(out / f'{arm}_archive.json')
            save_json(out / f'{arm}_attempts.json', attempts)
            continue
        accepted = False
        if added['status'] == 'added':
            by_node[added['id']] = results
            gate = archive.promote(added['id'], results, by_node[archive.deployed_id])
            accepted = gate['accepted']
        attempts.append({'generation': generation, 'parent_id': parent['id'], 'origin': origin,
                         'proposal_status': rec['status'], 'fallback_reason': reason,
                         'archive_status': added['status'], 'node_id': added['id'],
                         'mean_yield': checked_evidence(results)['mean_yield'], 'accepted': accepted,
                         'rationale': rec.get('rationale', '')})
        archive.save(out / f'{arm}_archive.json')
        save_json(out / f'{arm}_attempts.json', attempts)
        print(tag, attempts[-1]['archive_status'], 'score', attempts[-1]['mean_yield'], flush=True)
    archive.save(out / f'{arm}_archive.json')
    save_json(out / f'{arm}_attempts.json', attempts)
    return archive.nodes[archive.deployed_id]['source'], {
        'deployed_id': archive.deployed_id, 'ancestry': archive.lineage(archive.deployed_id),
        'retained': len(archive.nodes), 'attempts': attempts,
        'episode_evaluations_including_root': archive.evaluation_count,
        'candidate_slots': len(attempts), 'deployment_selection_mean': archive.nodes[archive.deployed_id]['mean_yield']}


def transfer(entries, model):
    """Fixed support on ranking-independent prior uncertainty; exclude all support."""
    records = []
    for entry in entries:
        ep = entry['episode']; drugs = ep['drugs']
        support = sorted(drugs, key=lambda d: (abs(ep['prior'][d] - .5), d))[:2]
        target = [d for d in drugs if d not in support]
        for mode in ('f', 'm', 'both'):
            backend = backend_for('world', model, entry)
            before = backend.predict(); updates = []
            if mode in ('f', 'both'):
                updates.append(backend.observe('f', support[0], ep['labels'][support[0]]))
            if mode in ('m', 'both'):
                updates.append(backend.observe('m', support[1], ep['mol'][support[1]]))
            after = backend.predict()
            brier = lambda p: float(np.mean([(p[d] - ep['labels'][d]) ** 2 for d in target]))
            precision = lambda p: float(np.mean([ep['labels'][d] for d in sorted(target, key=lambda d: (-p[d], d))[:5]]))
            records.append({'cell': entry['cell'], 'lineage': entry['lineage'], 'mode': mode,
                            'support_reserved': support, 'target_drugs': target, 'updates': updates,
                            'target_brier_before': brier(before), 'target_brier_after': brier(after),
                            'target_precision5_before': precision(before), 'target_precision5_after': precision(after)})
    return records


def contrast(a, b):
    pairs = list(zip(a, b))
    if any(x['episode_id'] != y['episode_id'] for x, y in pairs) or len(a) != len(b):
        raise ValueError('Unpaired replay contrast')
    for x, y in pairs:
        checked_result(x); checked_result(y)
    groups = {}
    for x, y in pairs:
        groups.setdefault(x['lineage'], []).append(x['yield'] - y['yield'])
    keys = sorted(groups); rng = np.random.default_rng(0)
    draws = [float(np.mean([value for lin in rng.choice(keys, len(keys)) for value in groups[lin]])) for _ in range(2000)]
    return {'mean_difference_hits': float(np.mean([x['yield'] - y['yield'] for x, y in pairs])),
            'descriptive_cluster_interval95': np.percentile(draws, [2.5, 97.5]).tolist(),
            'lineages': len(keys), 'episodes': len(a)}


def main(api, resume=False):
    out = HERE / 'RUN'
    if (out / 'selection.json').exists() or ((out / 'api_ledger.jsonl').exists() and not resume):
        raise RuntimeError('Selection already started; refuse silently repeated proposals')
    torch.set_num_threads(4)
    data = torch.load(out / 'prepared.pt', weights_only=False)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = build_model(5585, 935, seed=0, device=device)
    model.load_state_dict(torch.load(out / 'model.pt', map_location=device, weights_only=True))
    started = time.perf_counter()
    inherited, a1 = search('inherit', data['sel'], model, out, api)
    restarted, a2 = search('restart', data['sel'], model, out, api)
    conventional = []
    for source in FALLBACKS:
        results = evaluate(source, data['sel'], 'world', model)
        conventional.append({'source': source, 'results': results,
                             'mean_yield': checked_evidence(results)['mean_yield']})
    fixed_results = evaluate(BASE, data['sel'], 'world', model)
    best = max(conventional, key=lambda r: r['mean_yield'])
    conventional_source = best['source'] if best['mean_yield'] > checked_evidence(fixed_results)['mean_yield'] else BASE
    save_json(out / 'conventional_selection.json', conventional)
    selection = {'inherit': a1, 'restart': a2, 'conventional_candidates': 3,
                 'conventional_episode_evaluations_including_root': 4 * len(data['sel']),
                 'api_enabled': api, 'selection_seconds_this_invocation': time.perf_counter() - started,
                 'resumed': resume}
    save_json(out / 'selection.json', selection)
    programs = {'base': BASE, 'molecular_first': MOLECULAR, 'inherited': inherited,
                'restart': restarted, 'conventional': conventional_source}
    save_json(out / 'chosen_programs.json', programs)
    frozen = [p for p in HERE.glob('*.py') if not p.name.startswith('test_')] + [HERE / 'PROTOCOL.md', out / 'model.pt', out / 'prepared.pt',
                                       out / 'chosen_programs.json', out / 'selection.json']
    save_json(out / 'REGRESSION_FREEZE.json', {
        'claim': 'Freeze before this regression; all outcomes exposed historically',
        'files': {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen}})
    print('Selections frozen; starting exposed old-final regression', flush=True)
    arms = {'b1': (BASE, 'b1'), 'kernel': (BASE, 'kernel'), 'world_static': (BASE, 'static'),
            'world_updating': (BASE, 'world'), 'molecular_first': (MOLECULAR, 'world'),
            'inherited_world': (inherited, 'world'), 'restart_world': (restarted, 'world'),
            'conventional_world': (conventional_source, 'world'), 'inherited_static': (inherited, 'static')}
    results = {}
    for name, (source, mode) in arms.items():
        results[name] = evaluate(source, data['final_regression'], mode, model)
        checked_evidence(results[name])
        save_json(out / f'regression_{name}.json', results[name])
        print(name, 'mean hits', checked_evidence(results[name])['mean_yield'], flush=True)
    transfers = transfer(data['final_regression'], model)
    save_json(out / 'transfer.json', transfers)
    summary = {'decision': 'ENGINEERING_REPAIR_REPLAY_COMPLETE_INNOVATION_NOT_ESTABLISHED',
               'exposure': 'Previously exposed data; development/regression only',
               'mean_hits': {k: checked_evidence(v)['mean_yield'] for k, v in results.items()},
               'contrasts': {name: contrast(results[a], results[b]) for name, a, b in [
                   ('world_update_vs_static', 'world_updating', 'world_static'),
                   ('world_update_vs_kernel', 'world_updating', 'kernel'),
                   ('inherited_vs_fixed_updating', 'inherited_world', 'world_updating'),
                   ('inherited_vs_restart', 'inherited_world', 'restart_world'),
                   ('inherited_vs_conventional', 'inherited_world', 'conventional_world'),
                   ('inherited_vs_b1', 'inherited_world', 'b1')]},
               'all_program_errors': sum(bool(r['error']) for values in results.values() for r in values),
               'selection': selection, 'replay_seconds_this_invocation': time.perf_counter() - started}
    save_json(out / 'RESULTS.json', summary)
    print(json.dumps(summary['contrasts']), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--api', action='store_true', help='Run at most six authorized bounded API proposals')
    parser.add_argument('--resume', action='store_true', help='Resume incomplete selection from checked archive evidence without repeated proposals')
    args = parser.parse_args()
    main(args.api, args.resume)
