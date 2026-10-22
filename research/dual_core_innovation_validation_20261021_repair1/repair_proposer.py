"""Bounded, auditable proposals through the maintained configured client."""
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings, decode_response_object, json_object_from_text

SYSTEM = '''Return exactly one JSON object with program_lines (list of strings) and rationale.
Write a small Python procedure def choose(obs) returning ONE {'kind':'f'|'m','drug':d}
or {'kind':'stop'}. Each invocation is fresh; derive state from the observation.
No imports, filesystem, reflection, classes, decorators or global/nonlocal statements.
Builtins: len range min max sum sorted abs round float int list dict set tuple enumerate
zip any all bool reversed str isinstance. Scalar sqrt log exp isfinite floor ceil exist.
Public collection methods are allowed; no module or arbitrary attribute access.
obs contains drugs, predictions (CURRENT virtual-cell predictions), W (same current
predictions), prior (training drug rate), nn (baseline-similarity prior), sim (nested
drug fingerprint similarities), budget_left, costs {'f':1,'m':0.5}, queried_f (drug to
observed binary label), queried_m (drug to observed molecular payload), available_m,
and step. No hidden outcomes are available. Querying a drug twice with the same kind
is INVALID; querying it once with each kind is allowed. Overspending is INVALID.
A molecular query updates the shared virtual-cell trajectory from real 24h data;
a functional query updates the same model from a real binary label. Current
predictions are recomputed after each query. Updates may hurt. Total budget is 5.
Maximize DISTINCT confirmed positive functional queries, including exploration cost.
Return stop when no useful affordable action remains. No hard-coded drug/cell IDs,
outcome tables or external knowledge. Make a general executable procedure change;
do not merely rename variables or copy a previously proposed policy.
Development evidence is exposed public replay, not independent biology validation.'''


class SingleAttemptClient(DeepSeekChatClient):
    def __init__(self, settings):
        super().__init__(settings)
        self.attempts = 0

    def _send(self, request):
        self.attempts += 1
        with urlopen(request, timeout=self.settings.timeout_seconds) as response:
            return decode_response_object(response.read())


def propose(out, arm, generation, parent, evidence, previous):
    ledger = out / 'api_ledger.jsonl'
    records = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    cached = [r for r in records if r.get('arm') == arm and r.get('generation') == generation]
    if cached:
        if len(cached) != 1:
            raise RuntimeError('Duplicate proposal generation in ledger')
        record = cached[0]
        old_prompt = json.loads(record['messages'][1]['content'])
        if old_prompt['parent_program'] != parent['source'] or old_prompt['development_evidence']['evidence_sha256'] != evidence['evidence_sha256']:
            raise RuntimeError('Cached proposal context mismatch')
        source = None
        if record['status'] == 'ok':
            parsed = json_object_from_text(record['response'])
            source = '\n'.join(parsed['program_lines']) + '\n'
            if hashlib.sha256(source.encode()).hexdigest() != record['source_sha256']:
                raise RuntimeError('Cached proposal source changed')
        return source, record
    goals = [
        'Use a useful feedback-dependent decision rule. Pay for molecular data only when justified by the confirmed-hit objective.',
        'Explore a different control flow from prior candidates; investigate when the world model should be trusted or overridden after feedback.',
        'Improve a retained parent using its observed failures; preserve a useful inherited mechanism if one exists. Distinguish gains from wasted queries.',
    ]
    prompt = {'generation': generation, 'objective': goals[generation],
              'parent_program': parent['source'], 'parent_id': parent['id'],
              'development_evidence': evidence, 'previous_attempts': previous}
    messages = [{'role': 'system', 'content': SYSTEM},
                {'role': 'user', 'content': json.dumps(prompt, sort_keys=True)}]
    request_text = json.dumps(messages, sort_keys=True)
    # UTF-8 byte count is a conservative input-token reservation for this text.
    reservation = len(request_text.encode()) + 1500 + 1024
    used = sum(r.get('total_tokens', 0) for r in records)
    compacted = False
    if used + reservation > 24000:
        # Preserve numeric evidence and parent code; shorten repetitive JSON keys/prose.
        prompt['development_evidence'] = {
            'mean_yield': evidence.get('mean_yield'), 'evidence_sha256': evidence.get('evidence_sha256'),
            'action_columns': ['kind', 'before_p', 'label', 'prediction_change'],
            'episodes': [[e['id'], e['yield'],
                          [[t['kind'], t['before_p'], t['label'], t['prediction_change']] for t in e['actions']]]
                         for e in evidence.get('episodes', [])]}
        prompt['previous_attempts'] = [{k: v for k, v in row.items() if k != 'rationale'} for row in previous]
        messages[1]['content'] = json.dumps(prompt, sort_keys=True, separators=(',', ':'))
        request_text = json.dumps(messages, sort_keys=True)
        reservation = len(request_text.encode()) + 1500 + 1024
        compacted = True
    if len(records) >= 6 or used + reservation > 24000:
        raise RuntimeError('API budget exhausted before request')
    if any(r.get('usage_unknown') for r in records):
        raise RuntimeError('Unknown previous API usage; no further request permitted')
    settings = MAESTROSettings.from_workspace(ROOT)
    client = SingleAttemptClient(settings)
    rec = {'arm': arm, 'generation': generation, 'parent_id': parent['id'],
           'messages': messages, 'prompt_sha256': hashlib.sha256(request_text.encode()).hexdigest(),
           'input_output_reservation_tokens': reservation, 'temperature': .7, 'max_output_tokens': 1500,
           'evidence_compacted_for_budget': compacted}
    started = time.perf_counter()
    source = None
    try:
        response = client.complete(messages, model='deepseek-flash', temperature=.7,
                                   max_tokens=1500, thinking_enabled=False)
        rec.update(response=response.content, model=response.model, usage=dict(response.usage),
                   finish_reason=response.finish_reason)
        parsed = json_object_from_text(response.content)
        lines = parsed.get('program_lines') if isinstance(parsed, dict) else None
        if not isinstance(lines, list) or not lines or not all(isinstance(line, str) for line in lines):
            raise ValueError('Missing program_lines')
        source = '\n'.join(lines) + '\n'
        rec.update(status='ok', rationale=str(parsed.get('rationale', '')),
                   source_sha256=hashlib.sha256(source.encode()).hexdigest())
    except Exception as error:
        # Exception text may contain HTTP request details; retain only its class.
        rec.update(status='failure', error_type=type(error).__name__)
    usage = client.provider_usage
    rec.update(total_tokens=usage.get('total_tokens', usage.get('prompt_tokens', 0) + usage.get('completion_tokens', 0)),
               usage_unknown=not bool(usage.get('total_tokens', 0)),
               http_attempts=client.attempts, wall_seconds=time.perf_counter() - started)
    with ledger.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(rec, allow_nan=False) + '\n')
    return source, rec
