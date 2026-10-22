"""Synthetic execution-boundary tests; no biological-effect assertion."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import repair_runner as R


TOP = '''def choose(obs):
    remaining = [d for d in obs['drugs'] if d not in obs['queried_f']]
    if not remaining or obs['budget_left'] < 1:
        return {'kind': 'stop'}
    return {'kind': 'f', 'drug': max(remaining, key=lambda d: obs['predictions'][d])}
'''


def episode(budget=2, lam=.5):
    return dict(drugs=['a', 'b', 'c'], W={'a': .9, 'b': .8, 'c': .1},
                prior={}, nn={}, sim={}, labels={'a': 0, 'b': 1, 'c': 1},
                mol={'a': {'score': .2, 'z': [1., 0.]}}, budget=budget, lam=lam)


def test_authoritative_score_and_budget_are_recomputed():
    ep = dict(episode(), episode_id='synthetic-a')
    result = R.checked_result(R.run_program(TOP, ep))
    assert result['episode_id'] == 'synthetic-a'
    assert result['yield'] == 1
    assert result['spent'] == 2
    assert result['f_used'] == 2 and result['m_used'] == 0
    assert [r['drug'] for r in result['trace']] == ['a', 'b']


def test_evaluation_context_binds_inputs_but_not_candidate_source():
    original = R.checked_result(R.run_program(TOP, episode()))
    same_context = R.checked_result(R.run_program(TOP + '# different source\n', episode()))
    other_budget = R.checked_result(R.run_program(TOP, episode(budget=1)))
    other_outcomes = R.checked_result(R.run_program(TOP, dict(episode(), labels={'a': 1, 'b': 1, 'c': 1})))
    assert original['source_sha256'] != same_context['source_sha256']
    assert original['evaluation_context_sha256'] == same_context['evaluation_context_sha256']
    assert original['evaluation_context_sha256'] != other_budget['evaluation_context_sha256']
    assert original['evaluation_context_sha256'] != other_outcomes['evaluation_context_sha256']


def test_no_hidden_labels_or_unqueried_molecular_payload_enters_worker(monkeypatch):
    seen = []
    original = R._choose
    def inspect(source, obs, timeout):
        seen.append(json.loads(json.dumps(obs)))
        assert 'labels' not in obs and 'mol' not in obs
        assert 'model' not in obs and 'backend' not in obs
        return original(source, obs, timeout)
    monkeypatch.setattr(R, '_choose', inspect)
    R.checked_result(R.run_program(TOP, episode()))
    assert seen[0]['queried_f'] == {} and seen[0]['queried_m'] == {}
    assert seen[1]['queried_f'] == {'a': 0}
    assert seen[0]['available_m'] == ['a']


def test_detached_observation_mutation_cannot_forge_result_or_budget():
    source = '''def choose(obs):
    obs['budget_left'] = 1000
    obs['labels'] = {'a': 1}
    obs['queried_f']['forged'] = 1
    obs['result'] = {'yield': 999}
    return {'kind': 'f', 'drug': 'a'}
'''
    result = R.checked_result(R.run_program(source, episode(budget=1)))
    assert result['yield'] == 0 and result['spent'] == 1
    assert result['f_used'] == 1


@pytest.mark.parametrize('source', [
    "def run(env):\n    env.result = lambda: {'yield': 999}\n",
    "def choose(obs):\n    obs.result = lambda: {'yield': 999}\n",
    "def choose(obs):\n    return open('secret').read()\n",
    "import os\ndef choose(obs):\n    return {'kind': 'stop'}\n",
    "def choose(obs):\n    return obs.__class__\n",
    "def choose(obs):\n    return getattr(obs, '__class__')\n",
    "def choose(obs):\n    return '{0.__class__}'.format(obs)\n",
    "def choose(obs):\n    return np.load('secret')\n",
])
def test_old_evaluator_overwrite_and_file_or_reflection_apis_are_invalid(source):
    result = R.run_program(source, episode())
    assert result['status'] == 'invalid' and result['yield'] is None
    with pytest.raises(RuntimeError):
        R.checked_result(result)


@pytest.mark.parametrize('body', [
    "return {'kind': 'f', 'drug': 'missing'}",
    "return {'kind': 'm', 'drug': 'c'}",
    "return {'kind': 'f', 'drug': 'a', 'cost': 0}",
    "return {'kind': 'stop', 'drug': 'a'}",
    "return {'kind': 'f', 'drug': float('nan')}",
    "return {'yield': 999}",
    "return None",
    "return [1, 2]",
])
def test_malformed_and_illegal_actions_have_no_numeric_score(body):
    result = R.run_program('def choose(obs):\n    ' + body + '\n', episode())
    assert result['yield'] is None and result['status'] == 'invalid'
    assert result['spent'] == 0


def test_duplicate_query_invalidates_the_whole_evaluation():
    result = R.run_program("def choose(obs):\n    return {'kind': 'f', 'drug': 'a'}\n", episode())
    assert result['yield'] is None and 'duplicate' in result['error']
    assert result['spent'] == 1 and result['f_used'] == 1


def test_authoritative_budget_rejects_overspend():
    source = '''def choose(obs):
    if not obs['queried_m']:
        return {'kind': 'm', 'drug': 'a'}
    obs['budget_left'] = 100
    return {'kind': 'f', 'drug': 'b'}
'''
    # After the first molecular query, a second molecular query remains affordable,
    # but the requested functional query does not.
    ep = episode(budget=1, lam=.5)
    ep['mol']['b'] = {'score': .3, 'z': [0., 1.]}
    result = R.run_program(source, ep)
    assert result['yield'] is None and 'budget' in result['error']
    assert result['spent'] == .5 and result['m_used'] == 1


def test_timeout_is_invalid_not_zero_evidence():
    result = R.run_program('def choose(obs):\n    while True:\n        pass\n', episode(), timeout=.3)
    assert result['yield'] is None and result['error'] == 'timeout'


@pytest.mark.parametrize('response', [
    subprocess.CompletedProcess([], 1, '', 'failed'),
    subprocess.CompletedProcess([], 0, 'not json', ''),
    subprocess.CompletedProcess([], 0, '{"ok":true,"action":{"kind":"stop"},"yield":99}', ''),
])
def test_runner_failures_are_invalid(monkeypatch, response):
    monkeypatch.setattr(R.subprocess, 'run', lambda *a, **kw: response)
    result = R.run_program(TOP, episode())
    assert result['yield'] is None and result['status'] == 'invalid'
    with pytest.raises(RuntimeError):
        R.checked_result(result)


def test_missing_executable_is_invalid(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError('synthetic launch failure')
    monkeypatch.setattr(R.subprocess, 'run', fail)
    result = R.run_program(TOP, episode())
    assert result['yield'] is None and 'launch failure' in result['error']


@pytest.mark.parametrize('value', [None, float('nan'), float('inf'), -1])
def test_checked_evidence_rejects_missing_or_nonfinite_scores(value):
    with pytest.raises(RuntimeError):
        R.checked_result({'status': 'ok', 'error': None, 'yield': value})


class UpdatingBackend:
    model_id = 'v0'

    def __init__(self):
        self.p = {'a': .9, 'b': .8, 'c': .1}
        self.observed = []

    def predict(self):
        return dict(self.p)

    def observe(self, kind, drug, value):
        self.observed.append((kind, drug, value))
        self.p['c'] = .99
        self.model_id = 'v' + str(len(self.observed))
        return {'updated': True, 'support': len(self.observed)}


def test_functional_feedback_updates_before_the_next_choice():
    backend = UpdatingBackend()
    result = R.checked_result(R.run_program(TOP, episode(), backend=backend))
    assert [r['drug'] for r in result['trace']] == ['a', 'c']
    assert backend.observed == [('f', 'a', 0), ('f', 'c', 1)]
    first = result['trace'][0]
    assert first['model_before'] == 'v0' and first['model_after'] == 'v1'
    assert first['predictions_before']['c'] == .1 and first['predictions_after']['c'] == .99
    assert first['prediction_max_abs_change'] == pytest.approx(.89)


def test_molecular_observation_updates_and_is_charged_before_next_choice():
    source = '''def choose(obs):
    if not obs['queried_m']:
        return {'kind': 'm', 'drug': 'a'}
    remaining = [d for d in obs['drugs'] if d not in obs['queried_f']]
    return {'kind': 'f', 'drug': max(remaining, key=lambda d: obs['predictions'][d])}
'''
    backend = UpdatingBackend()
    ep = episode(budget=1.5)
    result = R.checked_result(R.run_program(source, ep, backend))
    assert [(r['kind'], r['drug']) for r in result['trace']] == [('m', 'a'), ('f', 'c')]
    assert result['spent'] == 1.5 and result['yield'] == 1
    assert backend.observed[0] == ('m', 'a', ep['mol']['a'])


def test_backend_failure_or_nan_invalidates_evidence():
    class BadBackend(UpdatingBackend):
        def observe(self, *args):
            self.p['a'] = float('nan')
            return {}
    result = R.run_program(TOP, episode(), BadBackend())
    assert result['yield'] is None and 'finite' in result['error']


def test_child_environment_does_not_inherit_api_credentials(monkeypatch):
    monkeypatch.setenv('TEST_API_SECRET', 'do-not-inherit')
    original = R.subprocess.run
    def inspect(*args, **kwargs):
        assert 'TEST_API_SECRET' not in kwargs['env']
        assert '-I' in args[0] and '-S' in args[0]
        return original(*args, **kwargs)
    monkeypatch.setattr(R.subprocess, 'run', inspect)
    R.checked_result(R.run_program(TOP, episode(budget=1)))
