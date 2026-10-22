"""Small complete-loop regressions with a real PPODE backend and known oracle.

The synthetic labels establish execution correctness, not biological efficacy.
"""
from pathlib import Path
import sys

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).parent))
from repair_archive import Archive, checked_evidence
from repair_model import FeedbackBackend, build_model, parameter_id
from repair_runner import checked_result, run_program


FUNCTIONAL_ONLY = '''def choose(obs):
    remaining = [d for d in obs['drugs'] if d not in obs['queried_f']]
    if obs['budget_left'] < obs['costs']['f'] or not remaining:
        return {'kind': 'stop'}
    return {'kind': 'f', 'drug': max(remaining, key=lambda d: obs['predictions'][d])}
'''

MOLECULAR_THEN_FUNCTIONAL = '''def choose(obs):
    if not obs['queried_m']:
        return {'kind': 'm', 'drug': obs['available_m'][0]}
    remaining = [d for d in obs['drugs'] if d not in obs['queried_f'] and d not in obs['queried_m']]
    if obs['budget_left'] < obs['costs']['f'] or not remaining:
        return {'kind': 'stop'}
    return {'kind': 'f', 'drug': max(remaining, key=lambda d: obs['predictions'][d])}
'''


@pytest.fixture
def synthetic_loop():
    old_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    rng = np.random.default_rng(121)
    inputs = {k: rng.normal(size=(3, n)).astype('float32')
              for k, n in [('x', 8), ('pert', 8), ('fpA', 4), ('fpB', 4)]}
    model = build_model(8, 4, seed=19, hidden=4)
    mask = np.zeros((3, 8), dtype=bool)
    mask[1] = True
    molecular = {'y': np.full((3, 8), .75).tolist(), 'mask': mask.tolist()}
    def make_backend():
        return FeedbackBackend(model, inputs, {'a': 0, 'b': 1, 'c': 2}, steps=2, lr=.001)
    initial = make_backend().predict()
    episode = {'episode_id': 'synthetic-complete-loop', 'drugs': ['a', 'b', 'c'],
               'W': initial, 'prior': initial, 'nn': initial, 'sim': {},
               'labels': {'a': 1, 'b': 1, 'c': 1}, 'mol': {'a': molecular},
               'lam': .5, 'budget': 1.5}
    yield model, make_backend, episode
    torch.set_num_threads(old_threads)


def test_complete_real_model_feedback_action_scoring_and_archive_roundtrip(synthetic_loop, tmp_path):
    model, make_backend, episode = synthetic_loop
    frozen_id = parameter_id(model)
    baseline = checked_result(run_program(FUNCTIONAL_ONLY, episode, make_backend()))
    backend = make_backend()
    result = checked_result(run_program(MOLECULAR_THEN_FUNCTIONAL, episode, backend))

    first, second = result['trace']
    assert first['kind'] == 'm' and second['kind'] == 'f'
    assert first['model_before'] == frozen_id
    assert first['model_after'] != first['model_before']
    assert second['model_before'] == first['model_after']
    assert second['model_after'] == backend.model_id
    assert first['predictions_after'] == second['predictions_before']
    assert first['update']['support_keys'] == [['m', 'a']]
    assert first['update']['max_unqueried_prediction_delta'] > 1e-8
    assert second['drug'] == max(('b', 'c'), key=lambda d: first['predictions_after'][d])
    assert set(backend.observations) == {('m', 'a'), ('f', second['drug'])}
    assert parameter_id(model) == frozen_id
    assert result['spent'] == 1.5 and result['f_used'] == result['m_used'] == 1
    assert result['yield'] == 1  # Oracle labels are all positive by construction.

    archive = Archive(suite_id='synthetic-complete-loop')
    root = archive.add(FUNCTIONAL_ONLY, [baseline])['id']
    child = archive.add(MOLECULAR_THEN_FUNCTIONAL, [result], parent_id=root)['id']
    assert child != root
    assert not archive.promote(child, [result], [baseline])['accepted']
    path = tmp_path / 'archive.json'
    archive.save(path)
    restored = Archive.load(path)
    assert restored.__dict__ == archive.__dict__
    assert restored.lineage(child) == [root, child]
    assert restored.nodes[child]['evidence'] == checked_evidence([result])
    assert restored.evaluation_count == 2
    result['trace'][0]['model_after'] = 'tampered-after-evaluation'
    assert restored.nodes[child]['evidence']['episodes'][0]['trace'][0]['model_after'] == first['update']['after_model_id']


def test_known_functional_oracle_changes_score_without_affecting_prequery_action(synthetic_loop):
    _, make_backend, episode = synthetic_loop
    negative = dict(episode, labels={'a': 0, 'b': 0, 'c': 0})
    positive_run = checked_result(run_program(MOLECULAR_THEN_FUNCTIONAL, episode, make_backend()))
    negative_run = checked_result(run_program(MOLECULAR_THEN_FUNCTIONAL, negative, make_backend()))
    assert positive_run['yield'] == 1 and negative_run['yield'] == 0
    assert [(r['kind'], r['drug']) for r in positive_run['trace']] == [
        (r['kind'], r['drug']) for r in negative_run['trace']]
    assert positive_run['trace'][1]['predictions_before'] == negative_run['trace'][1]['predictions_before']
    assert positive_run['trace'][1]['model_before'] == negative_run['trace'][1]['model_before']


def test_archive_rejects_scores_from_a_different_program_or_incumbent(synthetic_loop):
    _, make_backend, episode = synthetic_loop
    baseline = checked_result(run_program(FUNCTIONAL_ONLY, episode, make_backend()))
    candidate = checked_result(run_program(MOLECULAR_THEN_FUNCTIONAL, episode, make_backend()))
    wrong_source_archive = Archive()
    with pytest.raises(ValueError, match='source'):
        wrong_source_archive.add(MOLECULAR_THEN_FUNCTIONAL, [baseline])
    archive = Archive()
    root = archive.add(FUNCTIONAL_ONLY, [baseline])['id']
    child = archive.add(MOLECULAR_THEN_FUNCTIONAL, [candidate], parent_id=root)['id']
    with pytest.raises(ValueError, match='source'):
        archive.promote(child, [baseline], [baseline])
    with pytest.raises(ValueError, match='source'):
        archive.promote(child, [candidate], [candidate])
    assert not archive.promotions and archive.deployed_id == root


@pytest.mark.parametrize('changed', ['outcomes', 'budget', 'feedback_config', 'model_inputs'])
def test_same_episode_id_cannot_mix_different_full_evaluation_policies(synthetic_loop, changed):
    _, make_backend, episode = synthetic_loop
    baseline = checked_result(run_program(FUNCTIONAL_ONLY, episode, make_backend()))
    new_episode, new_backend = dict(episode), make_backend()
    if changed == 'outcomes':
        new_episode['labels'] = {'a': 0, 'b': 0, 'c': 0}
    elif changed == 'budget':
        new_episode['budget'] = 2
    elif changed == 'feedback_config':
        new_backend.steps += 1
    else:
        new_backend.inputs['x'][0, 0, 0] += .1
    different_context = checked_result(run_program(MOLECULAR_THEN_FUNCTIONAL, new_episode, new_backend))
    assert baseline['episode_id'] == different_context['episode_id']
    assert baseline['evaluation_context_sha256'] != different_context['evaluation_context_sha256']
    archive = Archive()
    root = archive.add(FUNCTIONAL_ONLY, [baseline])['id']
    with pytest.raises(ValueError, match='context|suite'):
        archive.add(MOLECULAR_THEN_FUNCTIONAL, [different_context], parent_id=root)
    assert archive.evaluation_count == 2
    assert len(archive.nodes) == 1 and archive.deployed_id == root
