"""Build exact, value-blind RNA sample and primary asset manifest."""
from collections import Counter
import csv
from decimal import Decimal
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/tggates_rna_feedback_pilot'
SOURCES = LOG/'rna_sources'
HEADROOM = ROOT/'log/20261022/tggates_feedback_headroom/MANIFEST.json'
CEL = ROOT/'log/20261022/tggates_source_qualification/HUMAN_CEL_IDENTITIES.json'
SAFE = ROOT/'log/20261022/tggates_functional_qualification/JOINED_IDENTITY_FLAGS.json'
FIELDS = ('EXP_ID', 'GROUP_ID', 'INDIVIDUAL_ID', 'COMPOUND_NAME', 'SPECIES', 'SEX_TYPE',
          'SACRIFICE_PERIOD', 'DOSE', 'DOSE_UNIT', 'DOSE_LEVEL')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def key(row):
    return tuple(row[field] for field in FIELDS[:3])


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            values = dict(attrs)
            if 'href' in values:
                self.links.append(values['href'])


def main():
    headroom, cels, safe = [json.loads(path.read_bytes()) for path in (HEADROOM, CEL, SAFE)]
    by_key = {key(row): row for row in safe}
    assert len(by_key) == len(safe)
    assert len({row['BARCODE'] for row in cels}) == len(cels)
    assert len({key(row) for row in cels}) == len(cels)
    with (SOURCES/'official_compoundlist.decoded_metadata').open(encoding='cp932', newline='') as stream:
        official = list(csv.DictReader(stream))
    by_name = {row['COMPOUND_NAME']: row for row in official}
    assert len(by_name) == len(official)
    parser = Links()
    parser.feed((SOURCES/'official_human_invitro_directory.body').read_text(encoding='utf-8'))
    listed_zip_names = {unquote(href).split('/')[-1] for href in parser.links if href.lower().endswith('.zip')}
    samples, compounds, counts = [], [], Counter()
    for compound in headroom['compounds']:
        role = compound['role']
        if role == 'later':
            continue
        name, exp = compound['compound_label'], compound['experiment']
        desired_levels = ['Middle', 'High', 'Control'] if role == 'source' else ['Middle', 'Control']
        selected = []
        for level in desired_levels:
            rows = [row for row in cels if row['EXP_ID'] == exp and row['COMPOUND_NAME'] == name
                    and row['SACRIFICE_PERIOD'] == '2 hr' and row['DOSE_LEVEL'] == level]
            assert len(rows) == 2, (name, level, 'expected exactly two released replicates')
            assert {row['INDIVIDUAL_ID'] for row in rows} == {'1', '2'}
            assert len({row['GROUP_ID'] for row in rows}) == 1
            for row in sorted(rows, key=key):
                assert row['ARR_DESIGN'] == 'HG-U133_Plus_2'
                assert row['SPECIES'] == 'Human' and row['EXP_TEST_TYPE'] == 'in vitro' and row['ORGAN'] == 'Liver'
                assert all(row[field] == by_key[key(row)][field] for field in FIELDS)
                assert row['BARCODE'] == by_key[key(row)]['BARCODE']
                assert by_key[key(row)]['CEL_identity_and_barcode_match']
                if level == 'Control':
                    assert Decimal(row['DOSE']) == 0
                else:
                    dose = compound['doses'][level]
                    assert Decimal(row['DOSE']) == Decimal(dose['value']) and row['DOSE_UNIT'] == dose['unit']
                sample = {'role': role, 'block_id': compound['block_id'],
                          'purpose': 'matched_control' if level == 'Control' else 'source_state_target' if level == 'High' else 'paid_middle_state',
                          'identity': row, 'expected_CEL_basename': row['BARCODE']+'.CEL'}
                samples.append(sample)
                selected.append(row['BARCODE'])
                counts[role+'_'+level] += 1
        entry = by_name[name]
        source_numbers = {row['COMPOUND_NO'] for row in cels if row['EXP_ID'] == exp and row['COMPOUND_NAME'] == name}
        assert source_numbers == {entry['COMPOUND_NO']}
        ftp = entry['Human - in vitro']
        assert ftp.startswith('ftp://ftp.biosciencedbc.jp/archive/open-tggates/LATEST/Human/in_vitro/')
        basename = unquote(urlparse(ftp).path.rsplit('/',1)[-1])
        assert basename in listed_zip_names
        https = 'https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/Human/in_vitro/'+quote(basename, safe='')
        compounds.append({'compound_label': name, 'experiment': exp, 'role': role,
                          'source_COMPOUND_NO': entry['COMPOUND_NO'], 'source_COMPOUND_ABBREVIATION': entry['COMPOUND_ABBREVIATION'],
                          'exact_official_compoundlist_FTP': ftp, 'official_HTTPS_mirror_URL': https,
                          'URL_derivation': 'Official README HTTPS mirror path + exact compoundlist archive basename confirmed in official Human/in_vitro directory',
                          'expected_allowed_barcodes': selected,
                          'full_archive_may_contain_excluded_RNA': True})
    assert len(compounds) == 31 and len(samples) == 172
    assert len({row['identity']['BARCODE'] for row in samples}) == 172
    assert len({key(row['identity']) for row in samples}) == 172
    assert counts == {'source_Middle':48, 'source_High':48, 'source_Control':48,
                      'development_Middle':14, 'development_Control':14}
    metadata = json.loads((SOURCES/'biostudies_E_MTAB_798.body').read_bytes())
    files = [node for node in walk(metadata) if 'path' in node and ('size' in node or 'attributes' in node)]
    protocols = [node for node in walk(metadata) if node.get('type') == 'Protocols']
    file_names = [str(node['path']) for node in files]
    cells = [path for path in file_names if '.cel' in path.lower()]
    processing = [node for node in protocols if any('normaliz' in str(a).lower() or 'transform' in str(a).lower()
                                                   for a in node.get('attributes', []))]
    write(SOURCES/'BIOSTUDIES_METADATA_PROJECTION.json', {'accno': metadata.get('accno'),
          'files': files, 'file_count': len(files), 'CEL_path_count': len(cells),
          'first_CEL_paths': cells[:5], 'normalization_transformation_protocol_metadata': processing})
    paths = [HEADROOM, CEL, SAFE, LOG/'EXPOSURE_AND_SCOPE.md', LOG/'RNA_METADATA_PROTOCOL.md',
             SOURCES/'official_compoundlist.body', SOURCES/'official_compoundlist.decoded_metadata',
             SOURCES/'official_human_invitro_directory.body', SOURCES/'biostudies_E_MTAB_798.body', Path(__file__)]
    manifest = {'status': 'RNA_IDENTITIES_AND_OFFICIAL_COMPOUND_ARCHIVES_AUTHENTICATED',
                'sample_count': len(samples), 'compound_count': len(compounds), 'sample_counts': dict(counts),
                'platforms': sorted({row['identity']['ARR_DESIGN'] for row in samples}),
                'samples': sorted(samples, key=lambda row: row['identity']['BARCODE']), 'compounds': compounds,
                'excluded': ['All later RNA', 'All Low RNA', 'All development High RNA', 'All non-2h RNA'],
                'numerical_RNA_payload_downloaded_or_parsed': False,
                'raw_route': '31 official compound archives; extract/parse only prelisted172CEL after separate freeze',
                'BioStudies_route_metadata': {'accno': metadata.get('accno'), 'file_count': len(files), 'CEL_path_count': len(cells)},
                'input_sha256': {path.relative_to(ROOT).as_posix(): sha(path) for path in paths},
                'scope': 'Static condition means, fixed exposed source/dev roles; replicates are not independent donors.'}
    write(LOG/'RNA_IDENTITY_MANIFEST.json', manifest)
    print(json.dumps({'sample_count': len(samples), 'compound_count': len(compounds), 'sample_counts': dict(counts),
                      'biostudies_files': len(files), 'biostudies_CEL_paths': len(cells), 'file_examples': file_names[:8],
                      'normalization_protocols': processing}, ensure_ascii=False))


if __name__ == '__main__':
    main()
