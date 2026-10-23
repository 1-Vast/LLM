"""Source-text extraction and two bounded exact-DOI public metadata lookups."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path('D:/MAESTRO')
OUT = ROOT/'log/20261022/ptpc_late_information/source'
SOURCE = ROOT/'log/20261022/generative_repair_renewal/source/archive_followup'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
now = lambda: datetime.now(timezone.utc).isoformat()


def fetch(item):
    name, url = item
    path = OUT/(name+'.body')
    assert not path.exists()
    receipt = dict(started_utc=now(), url=url, max_bytes=4*1024*1024, retries=0)
    try:
        try:
            response = urlopen(Request(url, headers={'User-Agent': 'PTPC source-definition research/1.0', 'Accept': 'application/json'}), timeout=40)
        except HTTPError as error:
            response = error
        with response:
            body = response.read(4*1024*1024+1)
            assert len(body) <= 4*1024*1024, 'Response cap reached'
            receipt.update(status=response.status, final_url=response.geturl(), content_type=response.headers.get('Content-Type'))
        path.write_bytes(body)
        receipt.update(bytes=len(body), sha256=sha(path))
    except Exception as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    receipt['ended_utc'] = now()
    (OUT/(name+'.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


def main():
    evidence = []
    si = ROOT/'tmp/ptv1_src/si.txt'
    lines = si.read_text(encoding='utf-8', errors='replace').split('\n')
    blocks = [('S1 viability annotation', 30, 38), ('S7 PTNC definition', 133, 147),
              ('S8 PTPC legend', 156, 176), ('S9 prediction cutoff', 178, 188),
              ('Supplementary dose response method', 600, 617)]
    for title, first, last in blocks:
        evidence.append(dict(title=title, path=str(si.relative_to(ROOT)), source_sha256=sha(si),
                             first_line=first, last_line=last,
                             text='\n'.join(lines[first-1:last])))
    article = ROOT/'tmp/ptv1_src/art.txt'
    article_text = article.read_text(encoding='utf-8')
    phrase='This is a preview of subscription content'
    position=article_text.find(phrase)
    assert position >= 0
    evidence.append(dict(title='Main article availability boundary', path=str(article.relative_to(ROOT)),
                         source_sha256=sha(article), start_character=position,
                         text=article_text[position:position+300], contains_literal_Methods_substring='Methods' in article_text))
    legend = json.loads((SOURCE/'S8_ANNOTATION_METADATA.json').read_text(encoding='utf-8'))
    evidence.append(dict(title='Actual S8 workbook DrawingML Legend',
                         path=str((SOURCE/'S8_ANNOTATION_METADATA.json').relative_to(ROOT)),
                         source_sha256=sha(SOURCE/'S8_ANNOTATION_METADATA.json'), text=legend['legend_drawing_text']))
    target = OUT/'TEXT_EVIDENCE.json'
    assert not target.exists()
    target.write_text(json.dumps(dict(created_utc=now(), evidence=evidence), ensure_ascii=False, indent=2), encoding='utf-8')
    requests = [('crossref_exact_doi', 'https://api.crossref.org/works/10.1038%2Fs41586-026-11001-9'),
                ('openalex_exact_doi', 'https://api.openalex.org/works/https://doi.org/10.1038/s41586-026-11001-9')]
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(fetch, requests))
    print(json.dumps(dict(evidence_blocks=len(evidence), lookups=receipts), indent=2))


if __name__ == '__main__':
    main()
