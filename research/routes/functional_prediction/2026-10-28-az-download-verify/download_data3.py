"""R204-DATA3 download/reuse and SHA verification (public data only).

Downloads missing public files (<=500MB each) to tmp/data3_downloads, reuses existing
local copies where present, and recomputes SHA256 for every file.  Does not run effects
and does not bypass login/terms.  Writes data3_manifest.json.
"""
import hashlib
import json
import os
import time
import urllib.request

B = r'D:\MAESTRO'
HERE = os.path.join(B, r'research\2026-10-28-az-download-verify')
TMP = os.path.join(B, 'tmp')
OUTDIR = os.path.join(TMP, 'data3_downloads')
os.makedirs(OUTDIR, exist_ok=True)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest().upper()


def download(url, path, timeout=600):
    last = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (public data verification)'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                status = r.status
                ctype = r.headers.get('content-type')
                clen = r.headers.get('content-length')
            with open(path, 'wb') as f:
                f.write(data)
            return {'http_status': status, 'content_type': ctype, 'content_length': clen, 'bytes': len(data)}
        except Exception as e:
            last = repr(e)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(last)


def entry(logical, url, existing=None, expected_bytes=None, expected_sha=None, license=None,
          source_note=None, required=True):
    p = existing
    used = 'reused_local' if p and os.path.exists(p) and (expected_bytes is None or os.path.getsize(p) == expected_bytes) else None
    if used == 'reused_local':
        h = sha(p)
        if expected_sha and h != expected_sha:
            used = None  # mismatch -> re-download
    if used != 'reused_local':
        p = os.path.join(OUTDIR, logical.replace('/', '_').replace('\\', '_'))
        if os.path.exists(p) and (expected_bytes is None or os.path.getsize(p) == expected_bytes):
            h = sha(p)
            if not expected_sha or h == expected_sha:
                used = 'reused_previous_download'
            else:
                used = None
        if used is None:
            try:
                info = download(url, p)
                used = 'downloaded_now'
                h = sha(p)
                if expected_sha and h != expected_sha:
                    raise RuntimeError(f'sha mismatch for {logical}: {h} != {expected_sha}')
                if expected_bytes and os.path.getsize(p) != expected_bytes:
                    raise RuntimeError(f'bytes mismatch for {logical}: {os.path.getsize(p)} != {expected_bytes}')
                return {'logical': logical, 'url': url, 'path_rel': os.path.relpath(p, B).replace('\\', '/'),
                        'bytes': os.path.getsize(p), 'sha256': h, 'license': license,
                        'state': used, 'http_status': info['http_status'], 'source_note': source_note,
                        'expected_bytes': expected_bytes, 'expected_sha256': expected_sha}
            except Exception as e:
                return {'logical': logical, 'url': url, 'path_rel': None, 'bytes': None, 'sha256': None,
                        'license': license, 'state': 'error', 'error': repr(e),
                        'expected_bytes': expected_bytes, 'expected_sha256': expected_sha}
    return {'logical': logical, 'url': url, 'path_rel': os.path.relpath(p, B).replace('\\', '/'),
            'bytes': os.path.getsize(p), 'sha256': h, 'license': license, 'state': used,
            'source_note': source_note, 'expected_bytes': expected_bytes, 'expected_sha256': expected_sha}


known = json.load(open(os.path.join(TMP, 'data2_github', 'known_repos.json'), encoding='utf-8'))
entries = []

# --- existing large files (reuse + SHA) ---
entries.append(entry('figshare_raw_well_zip', 'https://ndownloader.figshare.com/files/45451363',
                     existing=os.path.join(TMP, 'extq1', 'gsdc_well_stats.zip'),
                     expected_bytes=241088863,
                     expected_sha='E8CB50F6CE860FA17586A555130CB3B019F6011ED1976C0F0D3E00FB072D3259',
                     source_note='R202/X1 local raw ZIP; reuse and recompute SHA'))
entries.append(entry('figshare_nlme_zip', 'https://ndownloader.figshare.com/files/45451366',
                     existing=os.path.join(TMP, 'data1_gdsc', 'matrix_nlme_stats.zip'),
                     expected_bytes=57350378,
                     expected_sha='AD166FF2096C7C16C9C0FD7B85BCCAE67059B36ADE568C1DD935C8ABD5517C90',
                     source_note='DATA2/GDSC code local NLME ZIP; reuse and recompute SHA'))
entries.append(entry('europepmc_supplementary_zip',
                     'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11061612/supplementaryFiles',
                     existing=os.path.join(TMP, 'epmc_supp_list.txt'),
                     expected_bytes=95000784,
                     expected_sha='5CD77E495FA3EAFB249277130D7AA62A40E4997385DC2A88F2728789A433CCC7',
                     source_note='DATA1 local supplementary ZIP; reuse and recompute SHA'))
# matrix results + GDSC2 (reuse)
for name, path, byt, sh in [
    ('gdsc-007_matrix_results.csv', os.path.join(TMP, 'extq1', 'gdsc-007_matrix_results.csv'), 14947830, '8AAE0C26ECF33B734E5B9AE12B4A89889064CFAC8089A3DADA675E7E2AE8CE69'),
    ('gdsc-008_matrix_results.csv', os.path.join(TMP, 'extq1', 'gdsc-008_matrix_results.csv'), 16897258, '6335FE2366D8763AB6B262A49807C8B563243EC4E30256BCBD2CF96561E1342F'),
    ('gdsc-009_matrix_results.csv', os.path.join(TMP, 'extq1', 'gdsc-009_matrix_results.csv'), 15492311, '110FBDBCE37BAE0F33D85697DF58E2B22B6586284EFD363391BCAB4FBAE80CD8'),
    ('gdsc010_matrix_results.csv', os.path.join(TMP, 'extq1', 'gdsc010_matrix_results.csv'), 8026089, '403212F4046EE580FD817F4588531282FC21C32BCB2FE930455BCE1EF0A5F1C5'),
    ('sandpiper-01_matrix_results.csv', os.path.join(TMP, 'extq1', 'sandpiper-01_matrix_results.csv'), 1293674, '29437B41EAFFE7D2BA94E6787DACE3E6EA7DD88A5E15A1A9E28E3BD097B8D49C'),
    ('GDSC2_fitted_dose_response_25Feb20.csv', os.path.join(TMP, 'extq1', 'GDSC2_fitted_dose_response.csv'), 20355833, '0883B3EF6E440603094C43C74044E1D333FCE61E92E3EFA374EA3A54F0B50302'),
]:
    entries.append(entry(name, f'Figshare project 163378 / {name}', existing=path, expected_bytes=byt, expected_sha=sh,
                         source_note='DATA1 local Figshare matrix results/single-agent; reuse and recompute SHA'))
# GDSC docs (reuse)
for name, path, byt, sh in [
    ('Matrix_documentation.pdf', os.path.join(TMP, 'data1_gdsc', 'Matrix_documentation.pdf'), 370819, 'D3392CE4DDD07D4589207F8D922EFDB51A35E85D57BF25E8359756A626621E4F'),
    ('Matrix_glossary.pdf', os.path.join(TMP, 'data1_gdsc', 'Matrix_glossary.pdf'), 181578, '6C4EED666EE0A509307665D6311F6092E259C9A361E9EEAB2851687DFC6389F0'),
    ('Screening_documentation.pdf', os.path.join(TMP, 'data1_gdsc', 'Screening_documentation.pdf'), 217875, 'A3A9579B590F6D5F77111C2169383B67D763EE6440AB638216C9615E18824F30'),
    ('glossary.pdf', os.path.join(TMP, 'data1_gdsc', 'glossary.pdf'), 84942, '601C38C53944F3E819627065920C9620A97C35E92CCF348341CA2A640BD584E9'),
]:
    url = 'https://gdsc-combinations.depmap.sanger.ac.uk/downloads/' + name
    entries.append(entry(name, url, existing=path, expected_bytes=byt, expected_sha=sh,
                         source_note='DATA1 local GDSC docs; reuse and recompute SHA'))
# code tarballs (reuse)
for repo, logical, byt, sh in [
    ('eac54/Large-scale-pan-cancer-screening', 'eac54_Large-scale-pan-cancer-screening_tarball.tar.gz', 23922, '58A5C869962E9CA79541FE26BBD7982F3DB1DB1C2C21B2047EDAE41B4810FE8F'),
    ('CancerRxGene/gdscmatrixanalyser', 'CancerRxGene_gdscmatrixanalyser_tarball.tar.gz', 23643, '84952431F6A060E6D0DC568C63DF9BB62D17DE0082B532983496547D70E8E64A'),
    ('CancerRxGene/gdscmatrixexplorer', 'CancerRxGene_gdscmatrixexplorer_tarball.tar.gz', 5068735, '8D9545674B4B9F7DF37F58EC8160BAE611D43963D83F34C50BD6C994EB2B086A'),
    ('CancerRxGene/gdscIC50', 'CancerRxGene_gdscIC50_tarball.tar.gz', 1207161, '66B1C464B754146D352C317CF7CF819752A4B4A41FCFF4CE9B9F629BFBEE23E6'),
    ('CancerRxGene/gdsctools', 'CancerRxGene_gdsctools_tarball.tar.gz', 6310983, '441B9CE566D398C698E10850EB3072723098DEE5239EAA76C7923C442FF5A9B9'),
]:
    p = os.path.join(TMP, 'data2_github', logical)
    r = known.get(repo, {})
    entries.append(entry(logical, f'https://github.com/{repo}', existing=p, expected_bytes=byt, expected_sha=sh,
                         license=r.get('license'), source_note='DATA2 local code tarball; reuse and recompute SHA'))
# GDSC full matrix summaries/anchors (download now; sizes from DATA1 HEAD)
for logical, path, byt in [
    ('gdsc_full_007_matrix_results.csv', '/downloads/gdsc-007/matrix_results', 4240832),
    ('gdsc_full_008_matrix_results.csv', '/downloads/gdsc-008/matrix_results', 4726121),
    ('gdsc_full_009_matrix_results.csv', '/downloads/gdsc-009/matrix_results', 4365995),
    ('gdsc_full_010_matrix_results.csv', '/downloads/gdsc-010/matrix_results', 2299653),
    ('gdsc_full_sandpiper_matrix_results.csv', '/downloads/sandpiper-01/matrix_results', 418215),
    ('gdsc_full_anchor_colon.csv', '/downloads/colon/anchor_combo', 2559389),
    ('gdsc_full_anchor_pancreas.csv', '/downloads/pancreas/anchor_combo', 2234607),
    ('gdsc_full_anchor_breast.csv', '/downloads/breast/anchor_combo', 5519032),
]:
    url = 'https://gdsc-combinations.depmap.sanger.ac.uk' + path
    entries.append(entry(logical, url, expected_bytes=byt, source_note='GDSC Combos public download; full file'))

manifest = {
    'protocol': 'research/2026-10-28-az-download-verify/PROTOCOL_DATA3.md',
    'generated_by': 'research/2026-10-28-az-download-verify/download_data3.py',
    'download_root': os.path.relpath(OUTDIR, B).replace('\\', '/'),
    'single_file_max_bytes': 500 * 1024 * 1024,
    'entries': entries,
    'summary': {
        'n_entries': len(entries),
        'n_errors': sum(1 for e in entries if e['state'] == 'error'),
        'n_reused_local': sum(1 for e in entries if e['state'] == 'reused_local'),
        'n_downloaded_now': sum(1 for e in entries if e['state'] == 'downloaded_now'),
        'n_sha_expected_mismatch': sum(1 for e in entries if e.get('expected_sha256') and e.get('sha256') and e['sha256'] != e['expected_sha256']),
    },
}
with open(os.path.join(HERE, 'data3_manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(manifest, f, indent=1, sort_keys=True, ensure_ascii=False)
    f.write('\n')
print(json.dumps(manifest['summary'], ensure_ascii=False, indent=1))
for e in entries:
    print(e['state'], e['logical'], e.get('bytes'), e.get('sha256', '')[:12], e.get('error', ''))
