"""Fetch only explicitly scoped official RNA asset metadata, never CEL values."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET
import zipfile

import requests

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/tggates_rna_feedback_pilot'
OUT = LOG/'rna_sources'
CAP = 4*1024*1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    OUT.mkdir(exist_ok=True)
    urls = [('official_compoundlist', 'https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/open_tggates_main.zip'),
            ('official_human_directory', 'https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/Human/')]
    receipts = []
    for name, url in urls:
        receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'url': url, 'method': 'GET',
                   'logical_request': 1, 'numerical_RNA_allowed': False}
        start = time.monotonic()
        try:
            response = requests.get(url, timeout=30, stream=True)
            chunks, total = [], 0
            for chunk in response.iter_content(65536):
                total += len(chunk)
                if total > CAP:
                    raise ValueError('Metadata body cap exceeded')
                chunks.append(chunk)
            body = b''.join(chunks)
            (OUT/(name+'.body')).write_bytes(body)
            receipt.update(status=response.status_code, final_url=response.url, bytes=len(body), sha256=sha(body),
                           content_type=response.headers.get('Content-Type'), headers=dict(response.headers))
        except Exception as exc:
            receipt.update(error_type=type(exc).__name__)
        receipt['elapsed_seconds'] = time.monotonic()-start
        write(OUT/(name+'.http.json'), receipt)
        receipts.append(receipt)
    archive_path = OUT/'official_compoundlist.body'
    archive_metadata = []
    if archive_path.is_file() and zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                item = {'name': member.filename, 'uncompressed_bytes': member.file_size}
                if member.filename.lower().endswith(('.csv', '.tsv', '.txt', '.html')):
                    body = archive.read(member)
                    (OUT/'official_compoundlist.decoded_metadata').write_bytes(body)
                    item['first_line_metadata'] = body.decode('cp932').splitlines()[0]
                archive_metadata.append(item)
    paper = ROOT/'log/20261022/tggates_source_qualification/PAPER.xml'
    xml = ET.fromstring(paper.read_bytes())
    links = []
    for node in xml.iter():
        if node.tag.rsplit('}', 1)[-1] == 'ext-link':
            text = ''.join(node.itertext())
            href = node.attrib.get('{http://www.w3.org/1999/xlink}href')
            links.append({'text': text, 'url': href})
    write(OUT/'INITIAL_METADATA_RESULT.json', {'requests': receipts, 'compoundlist_members': archive_metadata,
          'prior_paper_external_links': links, 'prior_paper_sha256': sha(paper.read_bytes()),
          'CEL_or_expression_payload_downloaded': False})
    print(json.dumps({'requests': [{k:r.get(k) for k in ('status','bytes','error_type')} for r in receipts],
                      'compoundlist_members': archive_metadata, 'paper_external_links': links}, ensure_ascii=False))


if __name__ == '__main__':
    main()
