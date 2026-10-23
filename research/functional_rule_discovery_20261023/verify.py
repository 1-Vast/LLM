"""Local file/source/call-accounting audit; not a scientific performance test."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261023/functional_rule_discovery'
checks = []


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, passed):
    checks.append({'name': name, 'passed': bool(passed)})


def binding(name, path, expected, size=None):
    check(name, path.exists() and sha(path) == expected and
          (size is None or path.stat().st_size == size))


for relative, expected in read(ROOT / 'log/20261023/feedback_sufficiency_renewal/VERIFICATION.json')['files'].items():
    binding('predecessor:' + relative, ROOT / relative, expected)

for role in ['constructive', 'critic']:
    receipts = list((BASE / role).glob('*.receipt.json'))
    check(role + ':four source receipts', len(receipts) == 4)
    for path in receipts:
        record = read(path)
        body = path.with_name(path.name.removesuffix('.receipt.json') + '.body')
        binding('source:' + str(path.relative_to(BASE)), body, record['sha256'], record['bytes'])
        check('HTTP200:' + str(path.relative_to(BASE)), record['status'] == 200)

for name in ['SEARCH_RECEIPTS.json', 'PRIMARY_RECEIPTS.json']:
    records = read(BASE / 'frontier' / name)
    check('frontier:' + name + ':two requests', len(records) == 2)
    for record in records:
        body = BASE / 'frontier' / ((record.get('name') or record['id']) + '.html')
        binding('frontier source:' + body.name, body, record['sha256'], record['bytes'])
        check('HTTP200:' + body.name, record['status'] == 200)

memory = read(BASE / 'root/AUTHOR_MEMORY_RECEIPT.json')
source = BASE / 'root/author_memory_source.txt'
binding('root memory source', source, memory['sha256'], memory['bytes'])
blob_sha = hashlib.sha1(b'blob ' + str(source.stat().st_size).encode() + b'\0' + source.read_bytes()).hexdigest()
check('root pinned Git blob', blob_sha == memory['git_blob_sha1'] == 'c2a62c14c630b4a0385c394b5995797571b24670')
check('root HTTP200', memory['status'] == 200)

for seal_path in BASE.rglob('*SEAL.json'):
    seal = read(seal_path)
    if 'path' in seal and 'sha256' in seal:
        records = [{'path': seal['path'], 'sha256': seal['sha256']}]
    elif isinstance(seal.get('files'), list):
        records = seal['files']
    else:
        records = [{'path': path, 'sha256': digest} for path, digest in seal.get('files', {}).items()]
    check('nonempty seal:' + str(seal_path.relative_to(BASE)), bool(records))
    for record in records:
        path = Path(record['path'])
        if not path.is_absolute():
            path = (seal_path.parent if len(path.parts) == 1 else ROOT) / path
        binding('seal:' + str(seal_path.relative_to(BASE)) + ':' + record['path'],
                path, record['sha256'], record.get('bytes'))

api = read(BASE / 'api/RECEIPT.json')
check('API retained completed response', api['status'] == 'RESPONSE_RETAINED' and api['finish_reason'] == 'stop')
check('one API logical/provider-reported call', api['logical_requests'] == 1 and api['provider_usage']['calls'] == 1)
check('API token sum', api['provider_usage']['prompt_tokens'] == 641 and api['provider_usage']['completion_tokens'] == 1200
      and api['provider_usage']['total_tokens'] == 1841)
check('API prompt binding', api['prompt_sha256'] == sha(BASE / 'api/PROMPT.md'))
check('API response length', len((BASE / 'api/PROPOSAL.md').read_text(encoding='utf-8')) == api['content_chars'])
check('no generated code execution recorded', not api['generated_code_executed'])
for relative in ['constructive/INDEPENDENT.md', 'constructive/CROSS.md', 'critic/INDEPENDENT.md',
                 'critic/CROSS.md', 'critic/HISTORY_SCOPE_CORRECTION.md', 'frontier/INDEPENDENT.md',
                 'frontier/CROSS.md', 'root/PRIOR_COMPARISON.md', 'root/MEMORY_CODE_ASSESSMENT.md',
                 'api/ROOT_ASSESSMENT.md', 'DECISION.md']:
    check('artifact:' + relative, (BASE / relative).is_file())

files = sorted(p for folder in [BASE, ROOT / 'research/functional_rule_discovery_20261023']
               for p in folder.rglob('*') if p.is_file() and p.name != 'VERIFICATION.json'
               and '__pycache__' not in p.parts)
report = {'utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'Local byte/source/review/call continuity only, not biological validity, novelty or goal completion',
          'logical_public_GETs': 13, 'logical_model_API_calls': 1,
          'checks': checks, 'failures': sum(not x['passed'] for x in checks),
          'files': {str(p.relative_to(ROOT)): sha(p) for p in files}}
(BASE / 'VERIFICATION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'checks': len(checks), 'failures': report['failures'], 'files': len(files)}))
for item in checks:
    if not item['passed']:
        print(json.dumps(item))
raise SystemExit(bool(report['failures']))
