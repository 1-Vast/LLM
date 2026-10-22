"""Extract only the article-declared S2 identity entry from a streamed ZIP.

Other ZIP entries remain compressed and are not interpreted. The response is
closed as soon as S2 is recovered, so the receipt distinguishes a retained
network prefix from a complete response body.
"""
import hashlib
import json
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/az_chemical_identity'
NAME = b'EMS194010-supplement-Table_S2.xlsx'
EXPECTED_SIZE = 19152
EXPECTED_MD5 = '1661f9b51a2e204e9af8a3f6f94ebe80'
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11061612/supplementaryFiles'
PREFIX = OUT / 's2_attempt_04.body'
RECEIPT = OUT / 's2_attempt_04.http.json'
TARGET = OUT / NAME.decode()
if any(path.exists() for path in (PREFIX, RECEIPT, TARGET)):
    raise SystemExit('Refusing to overwrite previous captures')
receipt = {'url': URL, 'utc': datetime.now(timezone.utc).isoformat(),
           'authentication': False, 'automatic_redirects': False,
           'purpose': 'Locate and decode only article-declared S2 chemical metadata',
           'body_cap_bytes': 64 * 1024 * 1024, 'other_entries_decoded': False,
           'body_complete': False, 'target_name': NAME.decode()}
raw = bytearray()
target = None
try:
    with requests.get(URL, timeout=40, allow_redirects=False, stream=True,
                      headers={'User-Agent': 'MAESTRO-primary-metadata-audit/1.0'}) as response:
        receipt.update(status=response.status_code,
                       headers={key: value for key, value in response.headers.items()
                                if key.lower() not in ('set-cookie', 'cookie', 'authorization')})
        for chunk in response.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > receipt['body_cap_bytes']:
                raise ValueError('Bounded ZIP prefix exceeded cap')
            position = 0
            while True:
                position = raw.find(b'PK\x03\x04', position)
                if position < 0 or position + 30 > len(raw):
                    break
                header = struct.unpack_from('<4s5H3I2H', raw, position)
                _, _, flags, method, _, _, crc, compressed, uncompressed, nlen, elen = header
                nstart = position + 30
                name = bytes(raw[nstart:nstart + nlen])
                start = nstart + nlen + elen
                position += 4
                if not (name == NAME or name.endswith(b'/' + NAME)):
                    continue
                if flags & 1:
                    raise ValueError('Encrypted S2 is not an allowed metadata source')
                if method == 0 and compressed and len(raw) >= start + compressed:
                    target = bytes(raw[start:start + compressed])
                elif method == 8:
                    decoder = zlib.decompressobj(-15)
                    candidate = decoder.decompress(bytes(raw[start:]), EXPECTED_SIZE + 1)
                    if decoder.eof:
                        target = candidate
                else:
                    if method not in (0, 8):
                        raise ValueError('Unsupported S2 compression')
                if target is not None:
                    receipt['target_zip_header'] = {'flags': flags, 'method': method,
                        'crc32': crc, 'declared_compressed_size': compressed,
                        'declared_uncompressed_size': uncompressed, 'name': name.decode()}
                    break
            if target is not None:
                receipt['stopped_after_target'] = True
                break
        else:
            receipt['body_complete'] = True
    if target is None:
        raise ValueError('Exact S2 local ZIP entry was not recovered')
    md5 = hashlib.md5(target).hexdigest()
    if len(target) != EXPECTED_SIZE or md5 != EXPECTED_MD5:
        raise ValueError('S2 does not match article-declared byte count and MD5')
    TARGET.write_bytes(target)
    receipt.update(target_bytes=len(target), target_md5=md5,
                   target_sha256=hashlib.sha256(target).hexdigest(),
                   article_declared_size_and_md5_pass=True)
except Exception as error:
    receipt['error'] = repr(error)
finally:
    PREFIX.write_bytes(raw)
    receipt.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=False))
