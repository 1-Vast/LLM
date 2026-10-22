"""Fetch an explicitly authorized publisher Location without printing its query."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

import source_schema as source

OUT = source.OUT / 'redirect_followup'
EXPECTED_LOCATION_SHA = '485d91988f47a927c8847605491c583fd399f648ea19d9970589e616be94553a'


def acquire():
    original = json.loads((source.OUT / 'NETWORK.json').read_text(encoding='utf-8'))
    url = original['location']
    url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
    if original['status'] != 302 or url_hash != EXPECTED_LOCATION_SHA:
        raise RuntimeError('authorized_location_provenance_mismatch')
    raw_path = OUT / 'pbio.3002970.s001.raw.xlsx'
    if raw_path.exists() or (OUT / 'NETWORK.json').exists():
        raise RuntimeError('request_already_recorded')
    record = {'url': url, 'url_sha256': url_hash, 'source_redirect_network': str(source.OUT / 'NETWORK.json'),
        'started_utc': source.utc(), 'request_count': 1, 'retries': 0, 'redirects_followed': 0,
        'max_body_bytes': source.CAP}
    response = None
    try:
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-source-qualification/1.0'})
            response = urllib.request.build_opener(source.NoRedirect()).open(request, timeout=60)
        except urllib.error.HTTPError as error:
            response = error
        record.update({'status': response.code, 'content_type': response.headers.get('Content-Type'),
            'content_disposition': response.headers.get('Content-Disposition'),
            'location': response.headers.get('Location'), 'declared_content_length': response.headers.get('Content-Length')})
        received = 0
        with raw_path.open('xb') as handle:
            while received < source.CAP:
                chunk = response.read(min(65_536, source.CAP - received))
                if not chunk:
                    break
                handle.write(chunk)
                received += len(chunk)
        record['cap_reached'] = received == source.CAP
    except Exception as error:
        record['error_type'] = type(error).__name__
        if not raw_path.exists():
            raw_path.touch(exist_ok=False)
    finally:
        if response is not None:
            response.close()
        record.update({'ended_utc': source.utc(), 'raw_path': str(raw_path),
                       'received_bytes': raw_path.stat().st_size, 'sha256': source.sha(raw_path)})
        source.write_json(OUT / 'NETWORK.json', record)
    ok = record.get('status') == 200 and not record.get('cap_reached') and not record.get('error_type')
    print(json.dumps({'acquisition': 'RESPONSE_RETAINED' if ok else 'FAILED_OR_REDIRECT_RETAINED',
        'status': record.get('status'), 'bytes': record['received_bytes'],
        'request_host': urllib.parse.urlparse(url).hostname, 'request_basename': 'pbio.3002970.s001.xlsx',
        'request_location_sha256': url_hash, 'error_type': record.get('error_type')}))
    return 0 if ok else 1


def project():
    try:
        network = json.loads((OUT / 'NETWORK.json').read_text(encoding='utf-8'))
        if network.get('status') != 200 or network.get('cap_reached') or network.get('error_type'):
            raise RuntimeError('prior_response_not_successful')
        path = Path(network['raw_path'])
        if source.sha(path) != network['sha256']:
            raise RuntimeError('response_hash_mismatch')
        result, manifest = source.project(path)
        source.write_json(OUT / 'XLSX_MANIFEST.json', manifest)
        source.write_json(OUT / 'SCHEMA_AND_STRING_IDENTITIES.json', result)
        summary = []
        for sheet in result['sheets']:
            approved = [c for c in sheet['string_schema_identity_cells'] if 'text' in c]
            summary.append({k: sheet[k] for k in ['sheet_name', 'sheet_state', 'declared_dimension', 'merged_ranges', 'cell_type_counts']})
            summary[-1].update({'first_30_approved_strings': approved[:30], 'emitted_string_count': len(approved),
                'withholding_counts': dict(Counter(c['withheld'] for c in sheet['string_schema_identity_cells'] if 'withheld' in c))})
        source.write_json(OUT / 'SCHEMA_SUMMARY.json', summary)
        frozen = json.loads((OUT / 'FREEZE.json').read_text(encoding='utf-8-sig'))
        checks = [{'path': f['path'], 'unchanged': source.sha(f['path']) == f['sha256']} for f in frozen['files']]
        checks.append({'path': str(path), 'unchanged': source.sha(path) == result['source_sha256']})
        passed = all(c['unchanged'] for c in checks)
        source.write_json(OUT / 'VERIFICATION.json', {'utc': source.utc(), 'all_passed': passed, 'checks': checks})
        print(json.dumps({'verification_passed': passed, 'sheets': summary}, ensure_ascii=False))
        return 0 if passed else 1
    except Exception as error:
        source.write_json(OUT / 'PROJECTION_FAILURE.json', {'utc': source.utc(), 'error_type': type(error).__name__})
        print(json.dumps({'projection': 'FAILED_RETAINED', 'error_type': type(error).__name__}))
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['acquire', 'project'])
    args = parser.parse_args()
    raise SystemExit(acquire() if args.operation == 'acquire' else project())
