"""Budget, sampling and audit-record contracts without network access."""
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

import repair_proposer as P


def test_direct_cli_help_without_pytest_pythonpath(tmp_path):
    script = P.Path(P.__file__).with_name('run_replay.py')
    result = subprocess.run([sys.executable, '-B', str(script), '--help'], cwd=tmp_path,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert '--api' in result.stdout


def test_proposal_records_full_text_nonzero_sampling_and_one_attempt(tmp_path, monkeypatch):
    class Client:
        def __init__(self, settings):
            self.attempts = 0
            self.provider_usage = {'total_tokens': 41}

        def complete(self, messages, **kwargs):
            assert kwargs['temperature'] == .7
            assert kwargs['max_tokens'] == 1500
            self.attempts += 1
            return SimpleNamespace(content=json.dumps({'program_lines': ["def choose(obs):", "    return {'kind': 'stop'}"]}),
                                   model='fixture', usage={'total_tokens': 41}, finish_reason='stop')

    monkeypatch.setattr(P, 'SingleAttemptClient', Client)
    monkeypatch.setattr(P.MAESTROSettings, 'from_workspace', lambda root: None)
    source, result = P.propose(tmp_path, 'inherit', 1, {'id': 'p1', 'source': 'parent'}, {'valid': True}, [])
    saved = json.loads((tmp_path / 'api_ledger.jsonl').read_text())
    assert source.startswith('def choose')
    assert saved['messages'] == result['messages']
    assert saved['http_attempts'] == 1 and saved['total_tokens'] == 41
    assert not saved['usage_unknown']
    assert saved['response'] and saved['prompt_sha256'] and saved['source_sha256']


@pytest.mark.parametrize('records', [
    [{'total_tokens': 1}] * 6,
    [{'total_tokens': 23999}],
    [{'total_tokens': 0, 'usage_unknown': True}],
])
def test_no_call_when_request_token_or_unknown_usage_limit_reached(tmp_path, monkeypatch, records):
    (tmp_path / 'api_ledger.jsonl').write_text('\n'.join(json.dumps(r) for r in records))
    monkeypatch.setattr(P.MAESTROSettings, 'from_workspace', lambda root: pytest.fail('Unexpected credential access'))
    with pytest.raises(RuntimeError):
        P.propose(tmp_path, 'restart', 0, {'id': 'p0', 'source': 'code'}, {}, [])
