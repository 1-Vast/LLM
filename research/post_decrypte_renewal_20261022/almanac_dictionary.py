"""Acquire official text dictionary and compound identities, not responses."""
import json
import hashlib
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urljoin
from datetime import datetime,timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_decrypte_renewal/root/almanac_dictionary'


def main():
    OUT.mkdir(parents=True,exist_ok=False)
    links = json.loads((OUT.parent/'almanac_metadata/LINKS.json').read_text(encoding='utf-8'))
    for name, needle in [('dictionary','ALMANAC_DataFields.txt'),('compounds','ComboCompoundNames_small.txt')]:
        selected = [s for s in links if needle in s]
        assert len(selected) == 1
        url = urljoin('https://wiki.nci.nih.gov',selected[0])
        record = {'url':url,'utc':datetime.now(timezone.utc).isoformat()}
        body = b''
        try:
            try:
                response = urlopen(Request(url,headers={'User-Agent':'MAESTRO-research/1.0'}),timeout=35)
            except HTTPError as error:
                response = error
            with response:
                record['status'],record['final_url'] = response.code,response.url
                body = response.read(1_000_001)
            assert record['status'] == 200 and len(body) <= 1_000_000
        except Exception as error:
            record['error'] = str(error)
        (OUT/(name+'.txt')).write_bytes(body)
        record.update({'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
        (OUT/(name+'.receipt.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
        print(json.dumps(record),flush=True)


if __name__ == '__main__':
    main()
