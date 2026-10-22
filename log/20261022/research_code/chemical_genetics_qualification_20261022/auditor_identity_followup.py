"""Offline identity/schema string projection, with no numerical response output."""
from collections import Counter
import json
from pathlib import PurePosixPath
import posixpath
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

import auditor_workbook_identity as base

OUT = base.OUT.parent / 'identity_followup'
EXTRA = '41564_2024_1857_MOESM9_ESM.xlsx'
CATEGORY = re.compile(r'(?i)(?:^|[\s_:/,;()\-])(?:xr|cs|neutral|neutrality)(?:$|[\s_:/,;()\-])')
PURE_CATEGORIES = {'cross resistance', 'cross resistant', 'collateral sensitivity',
                   'collateral sensitive', 'resistant', 'sensitive', 'susceptible',
                   'resistance', 'sensitivity', 'no interaction', 'synergy', 'synergistic',
                   'antagonism', 'antagonistic'}
MEASUREMENT = re.compile(r'(?i)(fold(?:[ _-]?change)?|\bfc\b|\bfitness\b|\bgrowth\b|\bresponse\b|'
                         r'\bratio\b|\bmeasurement\b|\bmeasured\b|\bmic\b|\bic\s*90\b|\bauc\b|\bod\s*600\b)')
QUANTITY = re.compile(r'(?i)(?:\d\s*(?:[µμu]g|mg|ng|[µμu]m|mm|nm|[µμu]l|ml|mol)(?:\b|/))')


def filter_string(raw):
    value = ' '.join(unicodedata.normalize('NFKC', raw).split())
    low = value.lower()
    if low in base.MISSING:
        return None, 'missing_or_empty_string'
    if base.NUMBER.fullmatch(value):
        return None, 'numeric_string'
    if CATEGORY.search(value) or re.sub(r'[_-]+', ' ', low) in PURE_CATEGORIES:
        return None, 'categorical_response_text'
    if QUANTITY.search(value):
        return None, 'numeric_quantity_or_dose'
    stripped = re.sub(r'(?i)(ic\s*90|od\s*600(?:nm)?|log\s*2)', '', value)
    if (MEASUREMENT.search(value.replace('_', ' ')) and re.search(r'\d', stripped)) or re.search(r'(?i)\d\s*x\b', value):
        return None, 'numeric_measurement_text'
    return raw, None


def project(path, axis_only=False):
    before = base.sha(path)
    with zipfile.ZipFile(path, 'r') as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.attrib['Id']: r.attrib['Target'] for r in rels if r.attrib.get('TargetMode') != 'External'}
        shared = [base.string_content(si) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in archive.namelist() else []
        sheets = []
        for sheet in workbook.findall('m:sheets/m:sheet', base.NS):
            target = targets[sheet.attrib[base.REL_NS]]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            xml = ET.fromstring(archive.read(target))
            dimension = xml.find('m:dimension', base.NS)
            counts = Counter()
            strings = []
            for cell in xml.findall('m:sheetData/m:row/m:c', base.NS):
                ctype = cell.attrib.get('t', 'n')
                counts[ctype] += 1
                formula = cell.find('m:f', base.NS) is not None
                if formula:
                    counts['formula_cells'] += 1
                coord = cell.attrib.get('r', '')
                if ctype not in {'s', 'inlineStr', 'str'} or (axis_only and not (re.fullmatch(r'[A-Z]+1', coord) or re.fullmatch(r'A\d+', coord))):
                    continue
                item = {'coordinate': coord}
                if formula:
                    item['withheld'] = 'formula_or_cached_result'
                else:
                    node = cell.find('m:is' if ctype == 'inlineStr' else 'm:v', base.NS)
                    if ctype == 'inlineStr':
                        raw = base.string_content(node) if node is not None else ''
                    else:
                        raw = (shared[int(node.text)] if ctype == 's' else node.text or '') if node is not None else ''
                    text, reason = filter_string(raw)
                    item.update({'text': text} if reason is None else {'withheld': reason})
                strings.append(item)
            sheets.append({'sheet_name': sheet.attrib['name'], 'sheet_state': sheet.attrib.get('state', 'visible'),
                'declared_dimension': dimension.attrib.get('ref') if dimension is not None else None,
                'merged_ranges': [m.attrib['ref'] for m in xml.findall('m:mergeCells/m:mergeCell', base.NS)],
                'cell_type_counts': dict(counts), 'string_cells': strings})
    if base.sha(path) != before:
        raise RuntimeError('source_changed')
    return {'source_path': str(path), 'source_sha256': before,
            'scope': 'DESIGN_SCHEMA_EXPOSED_AXIS_STRINGS' if axis_only else 'DESIGN_SCHEMA_EXPOSED_ALL_STRINGS',
            'sheets': sheets}


def extract():
    network = json.loads((base.OUT / 'NETWORK.json').read_text(encoding='utf-8'))
    archive_path = base.OUT / 'supplementaryFiles.raw.zip'
    if base.sha(archive_path) != network['sha256']:
        raise RuntimeError('original_archive_hash_mismatch')
    with zipfile.ZipFile(archive_path) as archive:
        matches = [i for i in archive.infolist() if PurePosixPath(i.filename).name == EXTRA and not i.is_dir()]
        if len(matches) != 1:
            raise RuntimeError('extra_member_absent_or_ambiguous')
        destination = OUT / 'workbooks'
        destination.mkdir(exist_ok=False)
        path = destination / EXTRA
        with archive.open(matches[0]) as source, path.open('xb') as handle:
            while True:
                chunk = source.read(65_536)
                if not chunk:
                    break
                handle.write(chunk)
    base.write_json(OUT / 'EXTRACTION.json', {'utc': base.utc(), 'http_requests': 0,
        'archive_path': str(archive_path), 'archive_sha256': base.sha(archive_path),
        'member': matches[0].filename, 'path': str(path), 'bytes': path.stat().st_size,
        'sha256': base.sha(path)})
    return path


def main():
    try:
        extra_path = extract()
        records = [project(base.OUT / 'workbooks' / base.TARGETS[0], axis_only=True),
                   project(base.OUT / 'workbooks' / base.TARGETS[1]), project(extra_path)]
        base.write_json(OUT / 'STRING_IDENTITIES.json', records)
        summary = []
        for book in records:
            for sheet in book['sheets']:
                available = [c for c in sheet['string_cells'] if 'text' in c]
                summary.append({'workbook': base.Path(book['source_path']).name,
                    **{k: sheet[k] for k in ['sheet_name', 'declared_dimension', 'merged_ranges', 'cell_type_counts']},
                    'row1_strings': [c for c in available if re.fullmatch(r'[A-Z]+1', c['coordinate'])],
                    'nonrow1_first20': [c for c in available if not re.fullmatch(r'[A-Z]+1', c['coordinate'])][:20],
                    'emitted_strings': len(available),
                    'withholding_counts': dict(Counter(c['withheld'] for c in sheet['string_cells'] if 'withheld' in c))})
        base.write_json(OUT / 'SCHEMA_SUMMARY.json', summary)
        frozen = json.loads((OUT / 'FREEZE.json').read_text(encoding='utf-8-sig'))
        checks = [{'path': f['path'], 'sha256_unchanged': base.sha(f['path']) == f['sha256']} for f in frozen['files']]
        checks.extend({'path': r['source_path'], 'sha256_unchanged': base.sha(r['source_path']) == r['source_sha256']} for r in records)
        passed = all(c['sha256_unchanged'] for c in checks)
        base.write_json(OUT / 'VERIFICATION.json', {'utc': base.utc(), 'all_passed': passed, 'checks': checks, 'http_requests': 0})
        print(json.dumps({'verification_passed': passed, 'summaries': summary}, ensure_ascii=False))
        return 0 if passed else 1
    except Exception as error:
        base.write_json(OUT / 'FAILURE.json', {'utc': base.utc(), 'error_type': type(error).__name__, 'http_requests': 0})
        print(json.dumps({'followup': 'FAILED_RETAINED', 'error_type': type(error).__name__}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
