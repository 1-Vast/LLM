"""One official request followed by nonnumerical OOXML source qualification."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import posixpath
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/efaecalis_dynamic_qualification'
URL = 'https://journals.plos.org/plosbiology/article/file?id=10.1371/journal.pbio.3002970.s001&type=supplementary'
CAP = 30_000_000
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
NUMERIC = re.compile(r'^[\s<>=≤≥~±+−-]*(?:\d|[.,]\d)[\d\s.,eE+−*/^%()\[\]:;<>≤≥=~±-]*$')
MISSING = {'', 'na', 'n/a', 'nan', 'none', 'null', 'nd', 'n.d.', '-', '--', '.', '#n/a'}
HEADERS_CONTROLS = {'drug', 'drug name', 'antibiotic', 'antibiotics', 'selection drug', 'selecting drug',
    'evolution drug', 'challenge drug', 'testing drug', 'lineage', 'lineage id', 'population',
    'population id', 'sample', 'sample id', 'strain', 'strain id', 'gene', 'gene id', 'day', 'days',
    'time', 'timepoint', 'time point', 'replicate', 'biological replicate', 'technical replicate',
    'concentration', 'dose', 'units', 'unit', 'ic50', 'ic 50', 'od600', 'od 600', 'auc',
    'control', 'controls', 'ancestor', 'ancestral', 'wild type', 'wildtype', 'wt', 'blank',
    'no drug', 'no antibiotic', 'no cells', 'drug-free control', 'growth control'}
OUTCOME = re.compile(r'(?i)(?:^|[\s_:/,;()\-])(?:yes|no|true|false|positive|negative|xr|cr|cs|neutral|'
    r'neutrality|phenotypes?|class(?:es)?|validated|validation|bidirectional|bi-directional|monochromatic|'
    r'resistant|resistance|sensitive|sensitivity|susceptible|susceptibility|increased|decreased|'
    r'increasing|decreasing|high|low|success|failure|synergy|synergistic|antagonism|antagonistic|'
    r'extinct|extinction|eradicated|alive|dead|killed|survived|survival)(?:$|[\s_:/,;()\-])')
QUANTITY = re.compile(r'(?i)\d\s*(?:[µμu]g|mg|ng|[µμu]m|mm|nm|[µμu]l|ml|mol|fold|x)(?:\b|/)')
MEASUREMENT = re.compile(r'(?i)(fold|\bfc\b|\bod\b|od\s*600|ic\s*50|\bauc\b|\bgrowth\b|\bfitness\b|\bresponse\b|\bratio\b|\bmeasurement\b)')


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(obj, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def filter_text(raw):
    value = ' '.join(unicodedata.normalize('NFKC', raw).split())
    low = value.lower()
    if low in MISSING:
        return {'withheld': 'missing_or_empty_string'}
    if NUMERIC.fullmatch(value):
        return {'withheld': 'numeric_string'}
    if low in HEADERS_CONTROLS:
        return {'text': raw, 'exposure': 'generic_schema_or_control_design_exposed'}
    if OUTCOME.search(value):
        return {'withheld': 'suspected_categorical_or_qualitative_outcome'}
    if QUANTITY.search(value):
        return {'withheld': 'numeric_quantity_or_dose_deferred'}
    stripped = re.sub(r'(?i)(ic\s*50|od\s*600(?:nm)?|log\s*2)', '', value)
    if MEASUREMENT.search(value.replace('_', ' ')) and re.search(r'\d', stripped):
        return {'withheld': 'ambiguous_numeric_measurement_text'}
    return {'text': raw, 'exposure': 'unclassified_string_design_exposed_not_sealed_evidence'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def acquire():
    OUT.mkdir(parents=True, exist_ok=True)
    raw_path = OUT / 'pbio.3002970.s001.raw.xlsx'
    if raw_path.exists() or (OUT / 'NETWORK.json').exists():
        raise RuntimeError('request_already_recorded')
    record = {'url': URL, 'started_utc': utc(), 'request_count': 1, 'redirects_followed': 0,
              'retries': 0, 'max_body_bytes': CAP}
    response = None
    try:
        try:
            request = urllib.request.Request(URL, headers={'User-Agent': 'MAESTRO-source-qualification/1.0'})
            response = urllib.request.build_opener(NoRedirect()).open(request, timeout=60)
        except urllib.error.HTTPError as error:
            response = error
        record.update({'status': response.code, 'content_type': response.headers.get('Content-Type'),
            'content_disposition': response.headers.get('Content-Disposition'),
            'location': response.headers.get('Location'), 'declared_content_length': response.headers.get('Content-Length')})
        received = 0
        with raw_path.open('xb') as handle:
            while received < CAP:
                chunk = response.read(min(65_536, CAP - received))
                if not chunk:
                    break
                handle.write(chunk)
                received += len(chunk)
        record['cap_reached'] = received == CAP
    except Exception as error:
        record['error_type'] = type(error).__name__
        if not raw_path.exists():
            raw_path.touch(exist_ok=False)
    finally:
        if response is not None:
            response.close()
        record.update({'ended_utc': utc(), 'raw_path': str(raw_path), 'received_bytes': raw_path.stat().st_size,
                       'sha256': sha(raw_path)})
        write_json(OUT / 'NETWORK.json', record)
    ok = record.get('status') == 200 and not record.get('cap_reached') and not record.get('error_type')
    print(json.dumps({'acquisition': 'RESPONSE_RETAINED' if ok else 'FAILED_OR_REDIRECT_RETAINED',
        'status': record.get('status'), 'bytes': record['received_bytes'], 'location': record.get('location'),
        'error_type': record.get('error_type')}))
    return 0 if ok else 1


def string_content(node):
    return ''.join(t.text or '' for t in node.iter('{' + NS['m'] + '}t')) if node is not None else ''


def project(path):
    before = sha(path)
    with zipfile.ZipFile(path, 'r') as archive:
        manifest = [{'path': i.filename, 'compressed_bytes': i.compress_size, 'uncompressed_bytes': i.file_size,
                     'crc32': f'{i.CRC:08x}'} for i in archive.infolist()]
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.attrib['Id']: r.attrib['Target'] for r in rels if r.attrib.get('TargetMode') != 'External'}
        shared = [string_content(si) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in archive.namelist() else []
        sheets = []
        for sheet in workbook.findall('m:sheets/m:sheet', NS):
            target = targets[sheet.attrib[RID]]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            counts = Counter()
            strings, merged, dimension = [], [], None
            with archive.open(target) as source:
                for _, node in ET.iterparse(source, events=('end',)):
                    if node.tag == '{' + NS['m'] + '}dimension':
                        dimension = node.attrib.get('ref')
                    elif node.tag == '{' + NS['m'] + '}mergeCell':
                        merged.append(node.attrib['ref'])
                    elif node.tag == '{' + NS['m'] + '}c':
                        ctype = node.attrib.get('t', 'n')
                        counts[ctype] += 1
                        formula = node.find('m:f', NS) is not None
                        if formula:
                            counts['formula_cells'] += 1
                        if ctype in {'s', 'inlineStr', 'str'}:
                            item = {'coordinate': node.attrib.get('r', '')}
                            if formula:
                                item['withheld'] = 'formula_or_cached_result'
                            else:
                                if ctype == 'inlineStr':
                                    raw = string_content(node.find('m:is', NS))
                                else:
                                    value = node.find('m:v', NS)
                                    raw = (shared[int(value.text)] if ctype == 's' else value.text or '') if value is not None else ''
                                item.update(filter_text(raw))
                            strings.append(item)
                        node.clear()
            sheets.append({'sheet_name': sheet.attrib['name'], 'sheet_state': sheet.attrib.get('state', 'visible'),
                'declared_dimension': dimension, 'merged_ranges': merged, 'cell_type_counts': dict(counts),
                'string_schema_identity_cells': strings})
    if sha(path) != before:
        raise RuntimeError('workbook_changed_during_projection')
    return {'source_path': str(path), 'source_sha256': before,
        'scope': 'DESIGN_SCHEMA_EXPOSED_NONNUMERIC_STRINGS_WITH_OUTCOME_GUARD',
        'caveat': 'Unknown pure strings can encode unrecognized qualitative outcomes. Exposure annotations are not proof of outcome blindness.',
        'sheets': sheets}, manifest


def main_project():
    try:
        network = json.loads((OUT / 'NETWORK.json').read_text(encoding='utf-8'))
        if network.get('status') != 200 or network.get('cap_reached') or network.get('error_type'):
            raise RuntimeError('prior_response_not_successful')
        path = Path(network['raw_path'])
        if sha(path) != network['sha256']:
            raise RuntimeError('response_hash_mismatch')
        result, manifest = project(path)
        write_json(OUT / 'XLSX_MANIFEST.json', manifest)
        write_json(OUT / 'SCHEMA_AND_STRING_IDENTITIES.json', result)
        summary = []
        for s in result['sheets']:
            approved = [c for c in s['string_schema_identity_cells'] if 'text' in c]
            summary.append({k: s[k] for k in ['sheet_name', 'sheet_state', 'declared_dimension', 'merged_ranges', 'cell_type_counts']})
            summary[-1].update({'first_30_approved_strings': approved[:30],
                'emitted_string_count': len(approved),
                'withholding_counts': dict(Counter(c['withheld'] for c in s['string_schema_identity_cells'] if 'withheld' in c))})
        write_json(OUT / 'SCHEMA_SUMMARY.json', summary)
        frozen = json.loads((OUT / 'FREEZE.json').read_text(encoding='utf-8-sig'))
        checks = [{'path': f['path'], 'unchanged': sha(f['path']) == f['sha256']} for f in frozen['files']]
        checks.append({'path': str(path), 'unchanged': sha(path) == result['source_sha256']})
        passed = all(c['unchanged'] for c in checks)
        write_json(OUT / 'VERIFICATION.json', {'utc': utc(), 'all_passed': passed, 'checks': checks})
        print(json.dumps({'verification_passed': passed, 'sheets': summary}, ensure_ascii=False))
        return 0 if passed else 1
    except Exception as error:
        write_json(OUT / 'PROJECTION_FAILURE.json', {'utc': utc(), 'error_type': type(error).__name__})
        print(json.dumps({'projection': 'FAILED_RETAINED', 'error_type': type(error).__name__}))
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['acquire', 'project'])
    args = parser.parse_args()
    sys.exit(acquire() if args.operation == 'acquire' else main_project())
