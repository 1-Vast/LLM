"""Bounded readonly schema qualification using APSW's documented VFS interface.

No cell-table or health-value SELECT. Retained blocks may contain state bytes.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import sys
import apsw
import requests

ROOT = Path(__file__).resolve().parents[2]
LOG_SOURCE = ROOT / 'log/20261023/distribution_health_qualification/source'
DATA_SOURCE = ROOT / 'data/external/research_sources/20261023/distribution_health_qualification/source'
LOG_OUT = LOG_SOURCE / 'remote_schema'
DATA_OUT = DATA_SOURCE / 'remote_schema'
MODE = sys.argv[1] if len(sys.argv) > 1 else 'schema'
if MODE not in ('schema', 'image_metadata'):
    raise ValueError(MODE)
if MODE == 'image_metadata':
    LOG_OUT = LOG_SOURCE / 'remote_image_metadata'
    DATA_OUT = DATA_SOURCE / 'remote_image_metadata'
SIZE = 10704232448
BLOCK = 1024 * 1024
URL = 'https://ndownloader.figshare.com/files/18506036'


class RemoteFile:
    def __init__(self):
        self.blocks = {0: (DATA_SOURCE / 'sqlite_prefix.body').read_bytes()}
        self.receipts = []
        if MODE == 'image_metadata':
            previous = LOG_SOURCE / 'remote_schema'
            for receipt in json.loads((previous / 'RANGES.json').read_text(encoding='utf-8')):
                body = (DATA_SOURCE / 'remote_schema' / f"block_{receipt['index']}.body").read_bytes()
                if hashlib.sha256(body).hexdigest() != receipt['sha256']:
                    raise ValueError('Cached range hash mismatch')
                self.blocks[receipt['index']] = body

    def block(self, index):
        if index in self.blocks:
            return self.blocks[index]
        if len(self.receipts) >= 16:
            raise RuntimeError('Schema range budget exhausted')
        start = index * BLOCK
        end = min(start + BLOCK, SIZE) - 1
        receipt = {'index': index, 'utc': datetime.now(timezone.utc).isoformat(),
                   'range': f'bytes={start}-{end}', 'url': URL}
        self.receipts.append(receipt)
        try:
            with requests.get(URL, headers={'Range': receipt['range']},
                              stream=True, timeout=35) as response:
                receipt.update(status=response.status_code,
                               content_range=response.headers.get('Content-Range'),
                               etag=response.headers.get('ETag'))
                body = response.raw.read(end - start + 2)
            if (receipt['status'] != 206
                    or receipt['content_range'] != f'bytes {start}-{end}/{SIZE}'
                    or len(body) != end - start + 1):
                raise ValueError('Unexpected range response')
            receipt.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            (DATA_OUT / f'block_{index}.body').write_bytes(body)
            self.blocks[index] = body
        finally:
            (LOG_OUT / 'RANGES.json').write_text(json.dumps(self.receipts, indent=2), encoding='utf-8')
        return body

    def xRead(self, amount, offset):
        pieces = []
        while amount:
            index, within = divmod(offset, BLOCK)
            length = min(amount, BLOCK - within)
            pieces.append(self.block(index)[within:within + length])
            offset += length
            amount -= length
        return b''.join(pieces)

    def xFileSize(self):
        return SIZE

    def xClose(self):
        pass

    def xLock(self, level):
        pass

    def xUnlock(self, level):
        pass

    def xCheckReservedLock(self):
        return False

    def xFileControl(self, op, pointer):
        return False

    def xDeviceCharacteristics(self):
        return apsw.SQLITE_IOCAP_IMMUTABLE

    def xSectorSize(self):
        return 4096


class RemoteVFS(apsw.VFS):
    def __init__(self, file):
        super().__init__('cellhealth_schema_readonly', '')
        self.file = file

    def xOpen(self, name, flags):
        if not flags[0] & apsw.SQLITE_OPEN_MAIN_DB:
            raise apsw.ReadOnlyError('Only immutable main database allowed')
        flags[1] = apsw.SQLITE_OPEN_READONLY
        return self.file


if __name__ == '__main__':
    if LOG_OUT.exists() or DATA_OUT.exists():
        raise FileExistsError(LOG_OUT if LOG_OUT.exists() else DATA_OUT)
    LOG_OUT.mkdir(parents=True)
    DATA_OUT.mkdir(parents=True)
    started = time.monotonic()
    file = RemoteFile()
    vfs = RemoteVFS(file)
    result = {'scope': 'Public SQ00014613 schema only; cached prefix plus at most16 one-MiB ranges',
              'apsw': apsw.apswversion(), 'sqlite': apsw.sqlitelibversion()}
    try:
        with apsw.Connection('cellhealth', flags=apsw.SQLITE_OPEN_READONLY,
                             vfs='cellhealth_schema_readonly') as connection:
            if MODE == 'schema':
                objects = list(connection.execute('SELECT type,name,tbl_name,rootpage,sql FROM sqlite_master'))
                result.update(status='SCHEMA_READ', objects=[dict(zip(
                    ('type', 'name', 'tbl_name', 'rootpage', 'sql'), row)) for row in objects])
            else:
                query = ('SELECT Image_Metadata_Plate,Image_Metadata_Well,COUNT(*) '
                         'FROM Image INDEXED BY plate_well_image_idx '
                         'GROUP BY Image_Metadata_Plate,Image_Metadata_Well')
                plan = list(connection.execute('EXPLAIN QUERY PLAN ' + query))
                rows = list(connection.execute(query))
                result.update(scope='Public SQ00014613 plate/well/image-count metadata only; no cell-table or health SELECT',
                              status='IMAGE_METADATA_READ', query=query, plan=plan,
                              metadata_rows=rows, well_count=len(rows),
                              total_images=sum(row[2] for row in rows))
    except Exception as error:
        result.update(status='FAILED_RETAINED', error_type=type(error).__name__, error=str(error))
    result.update(new_range_requests=len(file.receipts),
                  retained_new_bytes=sum(r.get('bytes', 0) for r in file.receipts),
                  wall_seconds=time.monotonic() - started)
    (LOG_OUT / 'RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('objects', 'metadata_rows')}, indent=2))
    for obj in result.get('objects', []):
        print(obj['type'], obj['name'], 'rootpage', obj['rootpage'], 'sql_chars', len(obj['sql'] or ''))
