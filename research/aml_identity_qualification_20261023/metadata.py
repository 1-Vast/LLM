"""Project official library metadata and file identities from a retained GEO SOFT."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'log/20261023/post_anchor_mechanism/root_sources/aml_samples.body'
OUT = ROOT/'log/20261023/aml_identity_qualification'
samples = []
series_files = []
current = None
for line in SOURCE.read_text(encoding='utf-8').splitlines():
    if line.startswith('^SAMPLE = '):
        current = dict(id=line.split(' = ', 1)[1], metadata=[])
        samples.append(current)
    elif line.startswith('^'):
        current = None
    elif line.startswith('!Series_supplementary_file = '):
        series_files.append(line.split(' = ', 1)[1])
    elif current and line.startswith('!Sample_') and ' = ' in line:
        key, value = line.split(' = ', 1)
        if any(part in key for part in ['title', 'source_name', 'organism', 'characteristics',
               'treatment_protocol', 'extract_protocol', 'library', 'data_processing',
               'supplementary_file', 'relation', 'description', 'molecule']):
            current['metadata'].append(dict(field=key, value=value))
payload = dict(source=str(SOURCE.relative_to(ROOT)), samples=samples, series_files=series_files,
               scope='Official metadata and declared filenames only; no biological matrix or phenotype payloads.')
(OUT/'LIBRARY_METADATA.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
for sample in samples:
    print(sample['id'])
    for row in sample['metadata']:
        print(row['field'], '=', row['value'])
