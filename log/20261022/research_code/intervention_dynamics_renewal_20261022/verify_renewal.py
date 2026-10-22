"""Offline integrity/resource audit. Does not interpret measured responses."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/intervention_dynamics_renewal'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []
    receipts = []

    def check(name, condition):
        checks.append({'name': name, 'pass': bool(condition)})
        if not condition:
            raise AssertionError(name)

    def receipt(group, metadata, body):
        raw = body.read_bytes()
        size = metadata.get('bytes', metadata.get('body_bytes'))
        check(f'{group}/{body.name}/bytes', len(raw) == size)
        check(f'{group}/{body.name}/sha256', hashlib.sha256(raw).hexdigest() == metadata['sha256'])
        receipts.append({'group': group, 'status': metadata.get('status'), 'bytes': size,
                         'body': str(body.relative_to(ROOT))})

    for path in sorted((OUT/'root_scout').glob('*.NETWORK.json')):
        receipt('root', read(path), path.with_name(path.name.replace('.NETWORK.json', '.raw.xml')))
    for group in ('functional_scout', 'ap1_code_io'):
        for path in sorted((OUT/group).glob('REQUEST_*.json')):
            r = read(path)
            receipt(group, r, ROOT/Path(r['body_file']))
            if group == 'ap1_code_io':
                content = Path(r['decoded_file']).read_bytes()
                check(f'{group}/{path.name}/decoded_sha256', hashlib.sha256(content).hexdigest() == r['decoded_sha256'])
                check(f'{group}/{path.name}/git_blob', hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest() == r['expected_git_blob_sha1'])
    for r in read(OUT/'skeptic/NETWORK.json'):
        receipt('skeptic', r, ROOT/Path(r['path']))
    for r in read(OUT/'advocate/NETWORK.json'):
        receipt('advocate', r, OUT/'advocate'/r['name'])
    r = read(OUT/'melanoma_sequence/RECEIPT.json')
    receipt('melanoma_sequence', r, ROOT/Path(r['body_file']))
    check('exact_network_request_count', len(receipts) == 36)
    check('root_network_request_count', sum(r['group'] == 'root' for r in receipts) == 17)
    check('retained_http_503', sum(r['status'] == 503 for r in receipts) == 1)
    check('other_http_200', all(r['status'] in (200, 503) for r in receipts))
    check('failed_pdf_is_not_pdf', not read(OUT/'root_scout/SUPPLEMENT_STATUS.json')['pdf_magic'])

    # Authenticate acquired binary sources without interpreting numerical values.
    workbook = read(OUT/'root_scout/AP1_WORKBOOK_STRUCTURE.json')
    raw = Path(workbook['source_path']).read_bytes()
    check('ap1_workbook_sha256', hashlib.sha256(raw).hexdigest() == workbook['sha256'])
    check('ap1_workbook_git_blob', hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest() == workbook['git_blob_sha1'])
    for r in read(OUT/'root_scout/RESPONSE_DYNAMICS_SCHEMA.json')+read(OUT/'root_scout/RESPONSE_DYNAMICS_IO.json'):
        p = Path(r['local_path'])
        raw = p.read_bytes()
        check(f'{p.name}/sha256', hashlib.sha256(raw).hexdigest() == r['sha256'])
        check(f'{p.name}/git_blob', hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest() == r['git_blob_sha1'])
    check('melanoma_md5', hashlib.md5((OUT/'melanoma_sequence/Suppl Data 03.xlsx').read_bytes()).hexdigest() == '61e96850942060d93915800cd08946dc')

    for name in ('FREEZE.json', 'STAGE2_FREEZE.json', 'STAGE3_FREEZE.json'):
        freeze = read(OUT/'ap1_identity'/name)
        for f in freeze['files']:
            check(f'{name}/{Path(f["path"]).name}', digest(Path(f['path'])) == f['sha256'])
    for name in ('FINAL_CHECKS.json', 'STAGE2_FINAL_CHECKS.json', 'STAGE3_FINAL_CHECKS.json'):
        r = read(OUT/'ap1_identity'/name)
        check(f'{name}/source', r['source_hash_matches'])
        check(f'{name}/frozen', r['all_frozen_unchanged'])
    for name in ('SYNTHETIC_TESTS.json', 'STAGE2_SYNTHETIC_TESTS.json'):
        r = read(OUT/'ap1_identity'/name)
        check(f'{name}/success', r['success'] and r['failures'] == r['errors'] == 0)
    check('ap1_stage1_numeric_closed', not read(OUT/'ap1_identity/FINAL_CHECKS.json')['numeric_values_interpreted'])
    check('ap1_stage2_responses_closed', not read(OUT/'ap1_identity/STAGE2_FINAL_CHECKS.json')['response_values_interpreted'])
    check('ap1_stage3_responses_closed', not read(OUT/'ap1_identity/STAGE3_FINAL_CHECKS.json')['response_value_bodies_opened'])
    check('melanoma_responses_closed', not read(OUT/'melanoma_sequence/TIME_IDENTITY_AND_RESPONSE_METADATA.json')['responses_projected'])

    for result_name, code_name, protocol_name in (
        ('LOGIC_RESULT.json', 'selection_null_audit.py', 'LOGIC_PROTOCOL.md'),
        ('JOINT_LOGIC_RESULT.json', 'selection_joint_audit.py', 'JOINT_LOGIC_PROTOCOL.md')):
        result = read(OUT/'mechanism_round2'/result_name)
        check(f'{result_name}/code', result['code_sha256'] == digest(Path(__file__).with_name(code_name)))
        check(f'{result_name}/protocol', result['protocol_sha256'] == digest(OUT/'mechanism_round2'/protocol_name))
        check(f'{result_name}/logic_pass', result['status'].startswith('PASS_EXACT'))
    for path in ('skeptic/CROSS_SKEPTIC.md', 'advocate/CROSS_ADVOCATE.md',
                 'mechanism_round2/CROSS_SKEPTIC.md', 'mechanism_round2/CROSS_ADVOCATE.md',
                 'ap1_identity/REPORT_STAGE3.md', 'DECISION.md'):
        check(f'{path}/exists', (OUT/path).is_file())

    resource = {'GET_count': len(receipts), 'HTTP_status_counts': dict(Counter(r['status'] for r in receipts)),
        'HTTP_body_bytes': sum(r['bytes'] for r in receipts),
        'groups': {g: {'GET_count': sum(r['group'] == g for r in receipts),
                      'HTTP_body_bytes': sum(r['bytes'] for r in receipts if r['group'] == g)}
                   for g in sorted({r['group'] for r in receipts})},
        'model_API_calls': 0, 'author_contact': 0, 'receipts': receipts,
        'note': 'HTTP-body bytes after transport decoding; not wire bytes. HTTP200 failed-PDF HTML included.'}
    with (OUT/'RESOURCES.json').open('x', encoding='utf-8') as f:
        json.dump(resource, f, indent=2)
        f.write('\n')
    result = {'status': 'PASS_INTEGRITY_AND_SCOPE_ONLY', 'checks': checks,
        'check_count': len(checks), 'code_sha256': digest(Path(__file__)),
        'no_new_biological_or_model_performance_result': True}
    with (OUT/'ROOT_VERIFICATION.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({'status': result['status'], 'checks': len(checks),
        'GET_count': resource['GET_count'], 'HTTP_body_bytes': resource['HTTP_body_bytes']}))


if __name__ == '__main__':
    main()
