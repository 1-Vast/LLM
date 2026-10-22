"""Read fixed small primary code and filename inventories; never execute them."""
import base64
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/mechanism_gap/root/source_completion'
PATHS = {
    'author_readme': 'README.md',
    'schedule_code': 'plotScripts/FM06_to_FM10/FM07_25_25_mt_s1s2_integration_scTransForm20210427_V2.R',
    'pretreatment_code': 'plotScripts/FM01_to_FM05/2020.11.12_FM03_barcodeAnalysisV2.R',
}
DIRS = {
    'schedule_image_names': 'ContDiscontDoseCellCount/',
    'holiday_image_names': 'Timelapse/Singlet345_344DrugHoliday/',
}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.links.append(href)


def main():
    tree = {r['path']: r for r in json.loads((OUT / 'code_tree_names.json').read_text())}
    requests = [(name, 'https://api.github.com/repos/arjunrajlaboratory/FateMap_Goyal2023/git/blobs/' + tree[path]['sha'], path)
                for name, path in PATHS.items()]
    requests += [(name, 'https://ftp.ebi.ac.uk/biostudies/fire/S-BIAD/696/S-BIAD696/Files/' + path, None)
                 for name, path in DIRS.items()]
    files = [OUT.parent / 'SOURCE_STATIC_PROTOCOL.md', OUT / 'code_tree_names.json', OUT / 'imaging_index.body', Path(__file__)]
    with (OUT / 'STATIC_FREEZE.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'before_requests': True,
            'requests': requests, 'files': [{'path': p.relative_to(ROOT).as_posix(),
                'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}, handle, indent=2)
    receipts = []
    for name, url, path in requests:
        row = {'name': name, 'url': url, 'source_path': path,
               'utc': datetime.now(timezone.utc).isoformat()}
        try:
            with urlopen(Request(url, headers={'User-Agent': 'MAESTRO-public-research/1.0'}), timeout=45) as response:
                body = response.read(1_000_001)
                row.update(status=response.status, final_url=response.url, bytes=len(body),
                           sha256=hashlib.sha256(body).hexdigest())
            with (OUT / (name + '.response')).open('xb') as handle:
                handle.write(body)
            assert len(body) <= 1_000_000, 'fixed static metadata limit'
            if path is not None:
                record = json.loads(body)
                content = base64.b64decode(record['content'])
                git_sha = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
                assert git_sha == tree[path]['sha'] and len(content) == tree[path]['size']
                with (OUT / (name + '.body')).open('xb') as handle:
                    handle.write(content)
                row.update(git_blob_sha=git_sha, decoded_bytes=len(content),
                           decoded_sha256=hashlib.sha256(content).hexdigest())
            else:
                parser = Links()
                parser.feed(body.decode('utf-8'))
                with (OUT / (name + '.json')).open('x', encoding='utf-8', newline='\n') as handle:
                    json.dump({'directory': url, 'links': parser.links}, handle, indent=2)
                row['links'] = len(parser.links)
        except Exception as exc:
            row.update(error_type=type(exc).__name__, error=str(exc))
        receipts.append(row)
    with (OUT / 'STATIC_RECEIPTS.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(receipts, handle, indent=2)
    print(json.dumps(receipts))


if __name__ == '__main__':
    main()
