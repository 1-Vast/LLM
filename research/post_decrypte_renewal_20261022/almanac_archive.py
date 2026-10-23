"""Official archive bytes and header-only inspection; never print data rows."""
import hashlib
import json
import csv
import io
import zipfile
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from datetime import datetime,timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_decrypte_renewal/root/almanac_archive'


def main():
    OUT.mkdir(parents=True,exist_ok=False)
    links = json.loads((OUT.parent/'almanac_metadata/LINKS.json').read_text(encoding='utf-8'))
    selected = [s for s in links if 'ComboDrugGrowth_Nov2017.zip' in s]
    assert len(selected) == 1
    url = urljoin('https://wiki.nci.nih.gov',selected[0])
    receipts = []
    for method in ('HEAD','GET'):
        record = {'method':method,'url':url,'start':datetime.now(timezone.utc).isoformat()}
        received = 0
        digest = hashlib.sha256()
        try:
            try:
                response = urlopen(Request(url,method=method,headers={'User-Agent':'MAESTRO-research/1.0'}),timeout=40)
            except HTTPError as error:
                response = error
            with response:
                record.update({'status':response.code,'final_url':response.url,'headers':dict(response.headers)})
                if method == 'GET':
                    with (OUT/'archive.zip').open('xb') as handle:
                        while block := response.read(1024*1024):
                            handle.write(block)
                            digest.update(block)
                            received += len(block)
                            assert received <= 700_000_000, 'archive resource cap'
            assert record['status'] == 200, 'HTTP failure stops acquisition'
        except Exception as error:
            record['error'] = str(error)
        record.update({'received':received,'sha256':digest.hexdigest() if method=='GET' else None,
                       'finish':datetime.now(timezone.utc).isoformat()})
        receipts.append(record)
        (OUT/'RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
        print(json.dumps({k:record.get(k) for k in ('method','status','received','error')}),flush=True)
        if record.get('error'):
            return
    inventory = []
    with zipfile.ZipFile(OUT/'archive.zip') as archive:
        for info in archive.infolist():
            row = {'name':info.filename,'bytes':info.file_size,'compressed':info.compress_size,'crc':info.CRC}
            if not info.is_dir() and info.filename.lower().endswith(('.csv','.txt')):
                with archive.open(info) as source:
                    header = next(csv.reader(io.TextIOWrapper(source,encoding='utf-8-sig',newline='')))
                row['header_only'] = header
            inventory.append(row)
    (OUT/'INVENTORY.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    print(json.dumps(inventory,indent=2),flush=True)


if __name__ == '__main__':
    main()
