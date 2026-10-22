"""Resume orchestration uses stored checked evidence and spends only missing slots."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from repair_archive import Archive, checked_evidence, digest, source_hash
import run_replay as R
import repair_proposer as P


def source_for(drug):
    return "def choose(obs):\n    return {'kind': 'f', 'drug': '" + drug + "'}\n"


def result_for(source, drug, score):
    return [{
        'status': 'ok', 'error': None, 'episode_id': 'synthetic-resume-cell',
        'source_sha256': source_hash(source),
        'evaluation_context_sha256': digest({'episode': 'fixed', 'model': 'fixed'}),
        'yield': score,
        'trace': [{'kind': 'f', 'drug': drug, 'value': score, 'cost': 1.,
                   'predictions_before': {drug: .7}, 'predictions_after': {drug: .8},
                   'prediction_max_abs_change': .1,
                   'model_before': 'before', 'model_after': 'after'}],
    }]


def checkpoint(path, completed, arm='inherit'):
    archive = Archive(mode=arm, suite_id='original_selection_lineages_exposed')
    results = {R.BASE: result_for(R.BASE, 'a', 0)}
    root = archive.add(R.BASE, results[R.BASE])['id']
    by_node = {root: results[R.BASE]}
    attempts = []
    for generation in range(completed):
        parent = archive.select_parent()
        drug = 'bcd'[generation]
        source = source_for(drug)
        results[source] = result_for(source, drug, int(generation == 0))
        added = archive.add(source, results[source], parent_id=parent['id'])
        by_node[added['id']] = results[source]
        gate = archive.promote(added['id'], results[source], by_node[archive.deployed_id])
        attempts.append({'generation': generation, 'parent_id': parent['id'],
                         'origin': 'api', 'proposal_status': 'ok', 'fallback_reason': None,
                         'archive_status': added['status'], 'node_id': added['id'],
                         'mean_yield': checked_evidence(results[source])['mean_yield'],
                         'accepted': gate['accepted'], 'rationale': 'synthetic stored proposal'})
    archive.save(path / f'{arm}_archive.json')
    (path / f'{arm}_attempts.json').write_text(json.dumps(attempts), encoding='utf-8')
    return archive, attempts, results


@pytest.mark.parametrize('arm', ['inherit', 'restart'])
def test_completed_archive_resume_makes_no_api_or_evaluation_calls(tmp_path, monkeypatch, arm):
    archive, attempts, _ = checkpoint(tmp_path, completed=3, arm=arm)
    before = copy.deepcopy(archive.__dict__)
    def forbidden(*args, **kwargs):
        pytest.fail('completed checkpoint must not spend another API or evaluation call')
    monkeypatch.setattr(R, 'evaluate', forbidden)
    monkeypatch.setattr(R, 'propose', forbidden)
    source, summary = R.search(arm, [], None, tmp_path, api=True)
    assert source == archive.nodes[archive.deployed_id]['source']
    assert summary['attempts'] == attempts
    assert summary['candidate_slots'] == 3
    assert summary['episode_evaluations_including_root'] == 4
    assert Archive.load(tmp_path / f'{arm}_archive.json').__dict__ == before


@pytest.mark.parametrize('arm', ['inherit', 'restart'])
def test_incomplete_archive_spends_only_missing_generation_and_preserves_evidence(tmp_path, monkeypatch, arm):
    archive, attempts, historical_results = checkpoint(tmp_path, completed=2, arm=arm)
    before = copy.deepcopy(archive.__dict__)
    expected_parent = Archive.load(tmp_path / f'{arm}_archive.json').select_parent()
    expected_parent_evidence = expected_parent['evidence']
    expected_deployed_evidence = archive.nodes[archive.deployed_id]['evidence']
    new_source = source_for('d')
    new_results = result_for(new_source, 'd', 1)
    evaluate_calls, propose_calls, promotion_pairs, rehydrated = [], [], [], []
    entries, model = [{'sentinel': 'entries'}], object()
    original_summary = R.evidence_summary
    original_promote = Archive.promote

    def evaluate(source, supplied_entries, mode, supplied_model):
        evaluate_calls.append(source)
        assert source == new_source
        assert supplied_entries is entries and supplied_model is model and mode == 'world'
        return copy.deepcopy(new_results)

    def evidence_summary(results):
        # Rehydration adds status/error only, preserving every archived provenance
        # hash, score and trace; the canonical evidence hash must remain identical.
        checked = checked_evidence(results)
        rehydrated.append(checked)
        assert checked == expected_parent_evidence
        assert all(r['status'] == 'ok' and r['error'] is None for r in results)
        return original_summary(results)

    def propose(out, supplied_arm, generation, parent, evidence, previous):
        propose_calls.append((supplied_arm, generation, parent['id']))
        assert out == tmp_path and supplied_arm == arm and generation == 2
        assert parent['id'] == expected_parent['id']
        assert evidence['evidence_sha256'] == expected_parent_evidence['sha256']
        assert len(previous) == 2
        return new_source, {'status': 'ok', 'rationale': 'synthetic missing generation'}

    def promote(self, node_id, candidate, incumbent):
        candidate_evidence, incumbent_evidence = checked_evidence(candidate), checked_evidence(incumbent)
        promotion_pairs.append((candidate_evidence, incumbent_evidence))
        assert candidate_evidence == checked_evidence(new_results)
        assert incumbent_evidence == expected_deployed_evidence
        return original_promote(self, node_id, candidate, incumbent)

    monkeypatch.setattr(R, 'evaluate', evaluate)
    monkeypatch.setattr(R, 'evidence_summary', evidence_summary)
    monkeypatch.setattr(R, 'propose', propose)
    monkeypatch.setattr(Archive, 'promote', promote)
    deployed, summary = R.search(arm, entries, model, tmp_path, api=True)

    assert evaluate_calls == [new_source]
    assert propose_calls == [(arm, 2, expected_parent['id'])]
    assert len(rehydrated) == len(promotion_pairs) == 1
    assert deployed == archive.nodes[archive.deployed_id]['source']  # Tie never promotes.
    assert summary['attempts'][:2] == attempts
    assert summary['candidate_slots'] == 3
    assert summary['episode_evaluations_including_root'] == 4
    restored = Archive.load(tmp_path / f'{arm}_archive.json')
    for node_id, node in before['nodes'].items():
        assert restored.nodes[node_id]['evidence'] == node['evidence']
        assert restored.nodes[node_id]['source_sha256'] == node['source_sha256']
    assert len(restored.nodes) == 4
    assert len(restored.attempts) == 4
    for source, old_results in historical_results.items():
        assert source not in evaluate_calls
        assert old_results[0]['source_sha256'] == source_hash(source)


def test_invalid_candidate_is_checkpointed_before_next_proposal_interrupts(tmp_path, monkeypatch):
    checkpoint(tmp_path, completed=1)
    invalid_source, final_source = source_for('c'), source_for('d')
    evaluated, proposed = [], []
    def evaluate(source, *args):
        evaluated.append(source)
        if source == invalid_source:
            return [dict(result_for(source, 'c', 0)[0], status='invalid', error='timeout', **{'yield': None})]
        assert source == final_source
        return result_for(source, 'd', 1)
    def interrupted_propose(out, arm, generation, *args):
        proposed.append(generation)
        if generation == 2:
            raise RuntimeError('synthetic pre-request budget interruption')
        assert generation == 1
        return invalid_source, {'status': 'ok', 'rationale': 'synthetic runtime-invalid candidate'}
    monkeypatch.setattr(R, 'evaluate', evaluate)
    monkeypatch.setattr(R, 'propose', interrupted_propose)
    with pytest.raises(RuntimeError, match='pre-request budget'):
        R.search('inherit', [], None, tmp_path, api=True)
    archive = Archive.load(tmp_path / 'inherit_archive.json')
    attempts = json.loads((tmp_path / 'inherit_attempts.json').read_text())
    assert len(archive.attempts) == 3 and len(attempts) == 2
    assert attempts[-1]['archive_status'] == 'invalid' and attempts[-1]['mean_yield'] is None
    assert archive.attempts[-1]['status'] == 'invalid'
    assert all(n['source'] != invalid_source for n in archive.nodes.values())

    def resumed_propose(out, arm, generation, *args):
        proposed.append(generation)
        assert generation == 2
        return final_source, {'status': 'ok', 'rationale': 'only remaining generation'}
    monkeypatch.setattr(R, 'propose', resumed_propose)
    _, summary = R.search('inherit', [], None, tmp_path, api=True)
    assert evaluated == [invalid_source, final_source]
    assert proposed == [1, 2, 2]  # The interrupted generation made no API request.
    assert summary['candidate_slots'] == 3
    assert summary['episode_evaluations_including_root'] == 4
    assert summary['attempts'][1]['archive_status'] == 'invalid'


def test_inconsistent_checkpoint_refuses_before_spending_resources(tmp_path, monkeypatch):
    _, attempts, _ = checkpoint(tmp_path, completed=2)
    (tmp_path / 'inherit_attempts.json').write_text(json.dumps(attempts[:1]), encoding='utf-8')
    def forbidden(*args, **kwargs):
        pytest.fail('inconsistent checkpoint must fail before resource use')
    monkeypatch.setattr(R, 'evaluate', forbidden)
    monkeypatch.setattr(R, 'propose', forbidden)
    with pytest.raises(RuntimeError, match='Inconsistent selection checkpoint'):
        R.search('inherit', [], None, tmp_path, api=True)


def test_recorded_api_response_is_reused_without_network_even_at_budget_limit(tmp_path, monkeypatch):
    source = source_for('d')
    evidence = {'evidence_sha256': digest('same-evidence')}
    parent = {'source': R.BASE, 'id': 'p0'}
    record = {'arm': 'inherit', 'generation': 2, 'status': 'ok', 'total_tokens': 24000,
              'messages': [{'role': 'system', 'content': ''},
                           {'role': 'user', 'content': json.dumps({'parent_program': R.BASE,
                                                                 'development_evidence': evidence})}],
              'source_sha256': source_hash(source),
              'response': json.dumps({'program_lines': source.rstrip('\n').split('\n')}),
              'rationale': 'already paid proposal'}
    ledger = tmp_path / 'api_ledger.jsonl'
    ledger.write_text(json.dumps(record) + '\n', encoding='utf-8')
    before = ledger.read_bytes()
    def forbidden(*args, **kwargs):
        pytest.fail('cached response must never initialize a network client')
    monkeypatch.setattr(P, 'SingleAttemptClient', forbidden)
    cached_source, cached_record = P.propose(tmp_path, 'inherit', 2, parent, evidence, [])
    assert cached_source == source and cached_record == record
    assert ledger.read_bytes() == before
    with pytest.raises(RuntimeError, match='context mismatch'):
        P.propose(tmp_path, 'inherit', 2, parent, {'evidence_sha256': digest('changed')}, [])
    assert ledger.read_bytes() == before
