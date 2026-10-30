"""Download linked supplements and register recovered sources through the library tool."""
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'sources'
LIBRARY = ROOT.parents[1] / 'reference'
TOOL = Path(r'D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py')
SUPPLEMENTS = [
    ('erk_supplement.docx', 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41598-021-94941-8/MediaObjects/41598_2021_94941_MOESM1_ESM.docx'),
    ('subclones_supplement.pdf', 'https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs12964-024-01742-3/MediaObjects/12964_2024_1742_MOESM1_ESM.pdf'),
]


def supplement(spec):
    name, url = spec
    out = {'name': name, 'url': url, 'retrieved_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-Research/1.0'})
        with urllib.request.urlopen(req, timeout=35) as response:
            body = response.read(15_000_001)
            out.update(status=response.status, content_type=response.headers.get('Content-Type'))
        if len(body) > 15_000_000:
            raise ValueError('bounded supplement size exceeded')
        if not body.startswith(b'%PDF-' if name.endswith('.pdf') else b'PK'):
            raise ValueError('wrong document signature')
        path = SOURCES / name
        path.write_bytes(body)
        out.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        if name.endswith('.docx'):
            with zipfile.ZipFile(path) as package:
                out['members'] = package.namelist()
                (SOURCES / 'erk_supplement_document.xml').write_bytes(package.read('word/document.xml'))
        else:
            try:
                import fitz
                with fitz.open(path) as document:
                    out['pages'] = len(document)
                    text = '\n\n'.join(f'=== page {i+1} ===\n{page.get_text()}' for i, page in enumerate(document))
                    (SOURCES / 'subclones_supplement_text.txt').write_text(text, encoding='utf-8')
            except ImportError:
                out['pdf_text_extraction'] = 'fitz unavailable; not installed'
    except Exception as exc:
        out['error'] = str(exc)
    return out


def run_library(*args):
    result = subprocess.run([sys.executable, '-X', 'utf8', str(TOOL), *map(str, args)],
                            capture_output=True, text=True, encoding='utf-8')
    return {'args': list(map(str, args)), 'exit_code': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def main():
    if '--register-only' not in sys.argv:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            received = list(pool.map(supplement, SUPPLEMENTS))
        (SOURCES / 'supplement_receipts.json').write_text(json.dumps(received, ensure_ascii=False, indent=2), encoding='utf-8')
        for row in received:
            print(json.dumps({k: v for k, v in row.items() if k != 'members'}, ensure_ascii=False))
    logs = []
    papers = [
        ('arxiv-2610.16346', 'CellChain: Benchmarking Cross-Scale Evidence Use for Perturbation Reasoning',
         '10.48550/arXiv.2610.16346', '2026-10-12', 'https://arxiv.org/abs/2610.16346',
         'Selected paragraphs main2.1-2.3,3.1-3.2; AppendixD Drug Reference-History Construction,Signal Diagnostic,Condition-Level opening. AppendixE and tables not fully read; no reproduction.'),
        ('doi-10.1038-s41598-021-94941-8',
         'Rapid signaling reactivation after targeted BRAF inhibition predicts the proliferation of individual melanoma cells from an isogenic population',
         '10.1038/s41598-021-94941-8', '2021-07-29', 'https://doi.org/10.1038/s41598-021-94941-8',
         'Original JATS Sec3,6,9,11,12,14 selected; raw XML and linked DOCX acquisition record in agent-a-program-evidence; no raw trajectory availability established.'),
        ('doi-10.1186-s12964-024-01742-3',
         'Signaling dynamics in coexisting monoclonal cell subpopulations unveil mechanisms of resistance to anti-cancer compounds',
         '10.1186/s12964-024-01742-3', '2024-07-26', 'https://doi.org/10.1186/s12964-024-01742-3',
         'Original JATS Sec6,7,10,12 selected; raw XML and linked PDF in agent-a-program-evidence; baseline RPPA not assumed drug engagement.'),
    ]
    for pid, title, doi, date, url, scope in papers:
        logs.append(run_library('record', LIBRARY, 'paper', pid,
            'title=' + title, 'doi=' + doi, 'first_public_date=' + date,
            'date_basis=Official primary-source metadata', 'landing_page=' + url,
            'reading_level=P', 'reading_scope=' + scope,
            'note=2026-10-28 resource/closest-prior inspection; actual reading scope partial. Episode preserves original XML where not stored as library HTML/PDF.'))
        if pid == 'arxiv-2610.16346':
            logs.append(run_library('paper', LIBRARY, pid, '--file', SOURCES / 'cellchain.html', '--html', '--version', 'arxiv-v1'))
        logs.append(run_library('record', LIBRARY, 'code', pid,
            'note=No official implementation or raw-data repository verified in the inspected source passages; not an exhaustive absence claim.'))
    result = run_library('verify', LIBRARY, '--json')
    (ROOT / 'library_verify.json').write_text(result['stdout'], encoding='utf-8')
    logs.append(result)
    (ROOT / 'library_actions_v1.json').write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'library_steps': len(logs), 'failed_steps': [x['stderr'] for x in logs if x['exit_code']]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
