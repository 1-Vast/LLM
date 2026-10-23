"""Read official NCI design/download page only, retaining redirects and links."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/post_decrypte_renewal/root/almanac_metadata'


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.words = [], []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.extend(v for k,v in attrs if k == 'href')

    def handle_data(self, data):
        self.words.append(data)


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    url = 'https://wiki.nci.nih.gov/spaces/NCIDTPdata/pages/338237347/NCI-ALMANAC'
    record = {'url':url,'utc':datetime.now(timezone.utc).isoformat()}
    body = b''
    try:
        try:
            response = urlopen(Request(url,headers={'User-Agent':'MAESTRO-research/1.0'}),timeout=35)
        except HTTPError as error:
            response = error
        with response:
            record['status'], record['final_url'] = response.code, response.url
            body = response.read(5_000_001)
        assert record['status'] == 200 and len(body) <= 5_000_000
        parser = Page()
        parser.feed(body.decode('utf-8'))
        (OUT / 'LINKS.json').write_text(json.dumps(parser.links,indent=2),encoding='utf-8')
        (OUT / 'NARRATIVE.txt').write_text('\n'.join(parser.words),encoding='utf-8')
    except Exception as error:
        record['error'] = str(error)
    (OUT / 'SOURCE.body').write_bytes(body)
    record.update({'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
    (OUT / 'RECEIPT.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
