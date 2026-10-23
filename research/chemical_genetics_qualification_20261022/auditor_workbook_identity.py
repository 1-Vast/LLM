"""One-request source acquisition and conservative, read-only OOXML projection."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/chemical_genetics_qualification/workbook_identity'
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11726442/supplementaryFiles'
CAP = 60_000_000
TARGETS = ('41564_2024_1857_MOESM3_ESM.xlsx', '41564_2024_1857_MOESM7_ESM.xlsx')
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_NS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
HEADER_LABELS = {
    'drug', 'drugs', 'drug name', 'drug names', 'antibiotic', 'antibiotics',
    'antibiotic name', 'antibiotic names', 'compound', 'compound name',
    'abbreviation', 'abbreviations', 'acronym', 'acronyms', 'class', 'drug class',
    'antibiotic class', 'mode of action', 'mechanism of action', 'moa',
    'concentration', 'concentrations', 'dose', 'doses', 'units', 'unit',
    'selection drug', 'challenge drug', 'evolution drug', 'evolved drug',
    'evolved in', 'selected in', 'tested drug', 'test drug', 'treatment',
    'condition', 'conditions', 'sample', 'sample id', 'sample name',
    'strain', 'strain id', 'strain name', 'genotype', 'gene', 'gene name',
    'drug pair', 'drug pairs', 'pair', 'pair id', 'combination', 'combinations',
    'lineage', 'lineages', 'lineage id', 'replicate', 'replicates',
    'biological replicate', 'technical replicate', 'day', 'days', 'time',
    'time point', 'timepoint', 'passage', 'passages', 'ancestor', 'ancestors',
    'parent', 'founder', 'control', 'controls', 'wild type', 'wildtype', 'wt',
    'name', 'names', 'id', 'identifier', 'description', 'supplier', 'catalogue',
    'catalog', 'catalogue number', 'catalog number', 'reference', 'source',
}
RESPONSE = re.compile(
    r'(?i)(\b(?:xr|cs|neutral|phenotypes?|fitness|growth|responses?|resistant|'
    r'resistance|sensitive|sensitivity|susceptible|susceptibility|synergy|'
    r'synergistic|antagonism|antagonistic|potentiation|suppression|inhibition|'
    r'inhibitory|ic\s*\d+|ec\s*\d+|mic|auc|od\s*\d+|score|scores|'
    r'predicted|prediction|measured|measurement|measurements|observed|'
    r'fold[ -]?change|p[ -]?value|significant|non[ -]?significant)\b|'
    r'cross[ -]?resistan|collateral[ -]?sensitiv)')
NUMBER = re.compile(r'^[\s<>=≤≥~±+−-]*(?:\d|[.,]\d)[\d\s.,eE+−*/^%()\[\]:;<>≤≥=~±-]*$')
DOSE = re.compile(r'(?i)(?:\d.*(?:µg|μg|ug|mg|ng|nm|mm|µm|μm|um|mol|ml|µl|μl)|(?:µg|μg|ug|mg|ng)/ml)')
IDENTITY = re.compile(r'(?i)^(?:lineage|replicate|biological replicate|technical replicate|day|passage|ancestor|founder|control|drug|antibiotic|pair)\s*(?:id\s*)?[#:_-]?\s*\d+$')
MISSING = {'', 'na', 'n/a', 'nan', 'none', 'null', 'nd', 'n.d.', '-', '--', '.', '#n/a'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False)
        handle.write('\n')


def filter_label(raw):
    value = ' '.join(unicodedata.normalize('NFKC', raw).split())
    low = value.lower()
    if low in MISSING:
        return None, 'missing_or_empty_string'
    if NUMBER.fullmatch(value):
        return None, 'numeric_string'
    if RESPONSE.search(value):
        return None, 'suspected_response_text'
    if low in HEADER_LABELS or IDENTITY.fullmatch(value):
        return value, None
    if DOSE.search(value):
        return None, 'dose_or_unit_text_deferred'
    return None, 'unqualified_entity_or_text_deferred'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def acquire():
    OUT.mkdir(parents=True, exist_ok=True)
    body_path = OUT / 'supplementaryFiles.raw.zip'
    # Refuse a second request if any prior status or body exists.
    if body_path.exists() or (OUT / 'NETWORK.json').exists():
        raise RuntimeError('acquisition_already_recorded')
    record = {'url': URL, 'started_utc': utc(), 'max_body_bytes': CAP,
              'request_count': 1, 'redirects_followed': 0, 'retries': 0}
    response = None
    try:
        request = urllib.request.Request(URL, headers={'User-Agent': 'MAESTRO-source-qualification/1.0'})
        try:
            response = urllib.request.build_opener(NoRedirect()).open(request, timeout=60)
        except urllib.error.HTTPError as error:
            response = error
        record['status'] = response.code
        record['content_type'] = response.headers.get('Content-Type')
        record['declared_content_length'] = response.headers.get('Content-Length')
        received = 0
        with body_path.open('xb') as handle:
            while received < CAP:
                chunk = response.read(min(65_536, CAP - received))
                if not chunk:
                    break
                handle.write(chunk)
                received += len(chunk)
        record['cap_reached'] = received == CAP
    except Exception as error:
        record['error_type'] = type(error).__name__
        # Do not expose arbitrary exception contents or response bodies.
        if not body_path.exists():
            body_path.touch(exist_ok=False)
    finally:
        if response is not None:
            response.close()
        record.update({'ended_utc': utc(), 'body_path': str(body_path),
                       'received_bytes': body_path.stat().st_size, 'sha256': sha(body_path)})
        write_json(OUT / 'NETWORK.json', record)
    if record.get('status') != 200 or record.get('cap_reached') or record.get('error_type'):
        print(json.dumps({'acquisition': 'FAILED_RETAINED', 'status': record.get('status'),
                          'bytes': record['received_bytes'], 'error_type': record.get('error_type')}))
        return 1
    try:
        with zipfile.ZipFile(body_path) as archive:
            infos = archive.infolist()
            write_json(OUT / 'ZIP_MANIFEST.json', [{'path': i.filename,
                'compressed_bytes': i.compress_size, 'uncompressed_bytes': i.file_size,
                'crc32': f'{i.CRC:08x}', 'is_directory': i.is_dir()} for i in infos])
            selected = []
            for target in TARGETS:
                matches = [i for i in infos if PurePosixPath(i.filename).name == target and not i.is_dir()]
                if len(matches) != 1:
                    raise RuntimeError('whitelist_member_absent_or_ambiguous')
                selected.append(matches[0])
            if sum(i.file_size for i in selected) > CAP:
                raise RuntimeError('selected_uncompressed_size_over_cap')
            extracted = []
            destination = OUT / 'workbooks'
            destination.mkdir(exist_ok=False)
            for member in selected:
                target_path = destination / PurePosixPath(member.filename).name
                with archive.open(member, 'r') as source, target_path.open('xb') as handle:
                    while True:
                        chunk = source.read(65_536)
                        if not chunk:
                            break
                        handle.write(chunk)
                extracted.append({'zip_member': member.filename, 'path': str(target_path),
                                  'bytes': target_path.stat().st_size, 'sha256': sha(target_path)})
            write_json(OUT / 'EXTRACTED_WORKBOOKS.json', extracted)
    except Exception as error:
        write_json(OUT / 'EXTRACTION_FAILURE.json', {'utc': utc(), 'error_type': type(error).__name__})
        print(json.dumps({'acquisition': 'ZIP_OR_EXTRACTION_FAILED_RETAINED', 'error_type': type(error).__name__}))
        return 1
    print(json.dumps({'acquisition': 'SUCCESS', 'bytes': record['received_bytes'], 'extracted_workbooks': len(extracted)}))
    return 0


def string_content(node):
    return ''.join(t.text or '' for t in node.iter('{'+NS['m']+'}t'))


def project_workbook(path):
    before = sha(path)
    with zipfile.ZipFile(path, 'r') as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.attrib['Id']: r.attrib['Target'] for r in rels
                   if r.attrib.get('TargetMode') != 'External'}
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [string_content(si) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        sheets = []
        for sheet in workbook.findall('m:sheets/m:sheet', NS):
            target = targets[sheet.attrib[REL_NS]]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            xml = ET.fromstring(archive.read(target))
            dimension = xml.find('m:dimension', NS)
            counts = Counter()
            labels = []
            for cell in xml.findall('m:sheetData/m:row/m:c', NS):
                ctype = cell.attrib.get('t', 'n')
                counts[ctype] += 1
                formula = cell.find('m:f', NS) is not None
                if formula:
                    counts['formula_cells'] += 1
                coordinate = cell.attrib.get('r', '')
                match = re.fullmatch(r'[A-Z]+([0-9]+)', coordinate)
                if not match or not 1 <= int(match[1]) <= 30 or ctype not in {'s', 'inlineStr', 'str'}:
                    continue
                item = {'coordinate': coordinate}
                if formula:
                    item['withheld'] = 'formula_or_cached_result'
                else:
                    raw = ''
                    if ctype == 'inlineStr':
                        inline = cell.find('m:is', NS)
                        raw = string_content(inline) if inline is not None else ''
                    else:
                        value = cell.find('m:v', NS)
                        if value is not None:
                            raw = shared[int(value.text)] if ctype == 's' else (value.text or '')
                    label, reason = filter_label(raw)
                    item.update({'label': label} if reason is None else {'withheld': reason})
                labels.append(item)
            sheets.append({'sheet_name': sheet.attrib['name'], 'sheet_state': sheet.attrib.get('state', 'visible'),
                'declared_dimension': dimension.attrib.get('ref') if dimension is not None else None,
                'merged_ranges': [m.attrib['ref'] for m in xml.findall('m:mergeCells/m:mergeCell', NS)],
                'cell_type_counts': dict(counts), 'first_30_row_string_labels': labels})
    after = sha(path)
    if before != after:
        raise RuntimeError('source_changed_during_read')
    return {'source_path': str(path), 'source_sha256': before, 'source_sha256_after': after,
            'value_scope': 'generic_headers_and_explicit_identity_labels_only',
            'filter_caveat': 'Filtering does not prove that unknown strings cannot encode endpoints.', 'sheets': sheets}


def project():
    records = []
    try:
        for name in TARGETS:
            records.append(project_workbook(OUT / 'workbooks' / name))
        write_json(OUT / 'STRUCTURE_AND_LABELS.json', records)
    except Exception as error:
        write_json(OUT / 'PROJECTION_FAILURE.json', {'utc': utc(), 'error_type': type(error).__name__})
        print(json.dumps({'projection': 'FAILED_RETAINED', 'error_type': type(error).__name__}))
        return 1
    print(json.dumps({'projection': 'SUCCESS', 'workbooks': len(records),
                      'sheets': sum(len(r['sheets']) for r in records)}))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['acquire', 'project'])
    args = parser.parse_args()
    sys.exit(acquire() if args.operation == 'acquire' else project())
