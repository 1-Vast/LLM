"""DrugComb qualification audit (R190-E1): deterministic data fetcher.

Downloads the frozen inputs for research/2026-10-27-drugcomb-qualification/ and
writes download_receipt.json (URL / bytes / SHA256 / MD5 where published).

Deterministic: fixed URLs, fixed chunk offsets, no timestamps, JSON keys sorted.
Total download budget target <= 300 MB (see PROTOCOL_E1.md section 2).

Run:  D:\anaconda\envs\maestro\python.exe fetch_data.py
Idempotent: existing files with the expected size are reused.
"""
import hashlib
import json
import os
import sys
import time

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
DL = os.path.join(BASE, 'downloads')
CHUNKS = os.path.join(DL, 'v15_chunks')
os.makedirs(CHUNKS, exist_ok=True)

ZEN = 'https://zenodo.org/api/records'
V14_RECORD = 11102665          # "DrugComb - an integrative cancer drug combination data portal", version 1.4
V15_RECORD = 15235991          # "DrugComb update ...", version 1.5
ID_RECORD = 18449193           # "DrugComb Raw Data and Identifiers" (v1.5 identifiers)
EPMC_SUPP = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8218202/supplementaryFiles'

V15_FILE = 'summary_v_1_5.csv'
V15_BYTES = 1421694989
V15_MD5 = 'cd3e24758c10ffaea0124b6e80626c32'
CHUNK_SIZE = 1000000
N_CHUNKS = 60

FILES = [
    {
        'key': 'v1.4_summary_table',
        'url': f'{ZEN}/{V14_RECORD}/files/summary_table_v1.4.csv/content',
        'name': 'summary_table_v1.4.csv',
        'bytes': 193184734,
        'md5_reported': 'c11efbdcae4a860c2374c1505a66599b',
        'note': 'official v1.4 summary-level data (same file md5 as record 18756096)',
    },
    {
        'key': 'v1.5_drug_identifiers',
        'url': f'{ZEN}/{ID_RECORD}/files/DrugComb_drug_identifiers.xlsx/content',
        'name': 'DrugComb_drug_identifiers.xlsx',
        'bytes': 5856350,
        'md5_reported': '06894e63e5e06baa23d2bd59d6bd8808',
        'note': 'v1.5 drug identifier table (drug_id, dname, chembl_id, smiles, target_name, ...)',
    },
    {
        'key': 'v1.5_cell_line_identifiers',
        'url': f'{ZEN}/{ID_RECORD}/files/DrugComb_cell_line_identifiers.xlsx/content',
        'name': 'DrugComb_cell_line_identifiers.xlsx',
        'bytes': 161434,
        'md5_reported': '69c9b1a20cfd36cb57dd539641455534',
        'note': 'v1.5 cell-line identifier table (name, synonyms, depmap_id, cosmic_id, tissue_id, ...)',
    },
    {
        'key': 'epmc_supplementary_pmc8218202',
        'url': EPMC_SUPP,
        'name': 'drugcomb_2021_supplementary_PMC8218202.zip',
        'bytes': 813311,
        'md5_reported': None,
        'note': 'Europe PMC supplementary files for NAR 2021 DrugComb update; contains Supplementary Table S1 (37 studies)',
    },
]

sha256 = lambda b: hashlib.sha256(b).hexdigest()
md5 = lambda b: hashlib.md5(b).hexdigest()


def fetch(url, timeout=1800):
    r = requests.get(url, timeout=timeout, headers={'User-Agent': 'MAESTRO-drugcomb-audit/1.0'})
    r.raise_for_status()
    return r.content


def main():
    receipt = {'protocol': 'PROTOCOL_E1.md', 'generated_by': 'fetch_data.py', 'files': [], 'chunks': None,
               'total_bytes': 0}
    for spec in FILES:
        out = os.path.join(DL, spec['name'])
        if os.path.exists(out) and os.path.getsize(out) == spec['bytes']:
            data = open(out, 'rb').read()
            status = 'reused'
        else:
            t0 = time.time()
            data = fetch(spec['url'])
            open(out, 'wb').write(data)
            status = 'downloaded'
            print('downloaded %s in %.1fs' % (spec['name'], time.time() - t0), flush=True)
        rec = dict(spec)
        rec['saved_as'] = os.path.relpath(out, BASE).replace('\\', '/')
        rec['bytes_actual'] = len(data)
        rec['sha256'] = sha256(data)
        rec['md5_computed'] = md5(data)
        rec['md5_matches_zenodo'] = (spec['md5_reported'] is None) or (rec['md5_computed'] == spec['md5_reported'])
        rec['status'] = status
        receipt['files'].append(rec)
        receipt['total_bytes'] += len(data)

    # v1.5 summary: full file (1,421,694,989 B) exceeds the download budget -> fixed chunk sample.
    S = V15_BYTES
    url = f'{ZEN}/{V15_RECORD}/files/{V15_FILE}/content'
    chunks = []
    t0 = time.time()
    for i in range(N_CHUNKS):
        start = round(i * S / N_CHUNKS)
        end = min(start + CHUNK_SIZE, S) - 1
        out = os.path.join(CHUNKS, 'chunk_%02d_%010d.bin' % (i, start))
        if os.path.exists(out) and os.path.getsize(out) == (end - start + 1):
            data = open(out, 'rb').read()
            status = 'reused'
        else:
            data = None
            for attempt in range(3):
                try:
                    r = requests.get(url, timeout=600, headers={
                        'Range': 'bytes=%d-%d' % (start, end),
                        'User-Agent': 'MAESTRO-drugcomb-audit/1.0'})
                    if r.status_code != 206:
                        raise RuntimeError('expected 206, got %d' % r.status_code)
                    data = r.content
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == 2:
                        raise
                    time.sleep(2 * (attempt + 1))
                    print('retry chunk %d: %s' % (i, exc), flush=True)
            open(out, 'wb').write(data)
            status = 'downloaded'
        assert len(data) == end - start + 1, (i, len(data), end - start + 1)
        chunks.append({'i': i, 'start': start, 'end': end, 'bytes': len(data),
                       'saved_as': os.path.relpath(out, BASE).replace('\\', '/'),
                       'sha256': sha256(data), 'status': status})
    print('v1.5 chunks done in %.1fs' % (time.time() - t0), flush=True)
    receipt['chunks'] = {
        'file': V15_FILE,
        'zenodo_record': V15_RECORD,
        'url': url,
        'file_bytes': S,
        'md5_reported': V15_MD5,
        'full_file_sha256': None,
        'sampling_note': ('full file (%.0f MB) exceeds the task download budget; '
                          'fixed %d x %d B byte-range chunks at k*S/N offsets; '
                          'file-level SHA256 not computed, Zenodo MD5 recorded'
                          % (S / 1e6, N_CHUNKS, CHUNK_SIZE)),
        'chunk_size': CHUNK_SIZE,
        'n_chunks': N_CHUNKS,
        'chunks': chunks,
    }
    receipt['total_bytes'] += sum(c['bytes'] for c in chunks)

    with open(os.path.join(BASE, 'download_receipt.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    print('TOTAL bytes: %d (%.1f MB)' % (receipt['total_bytes'], receipt['total_bytes'] / 1e6), flush=True)
    print('receipt -> download_receipt.json', flush=True)


if __name__ == '__main__':
    sys.exit(main())
