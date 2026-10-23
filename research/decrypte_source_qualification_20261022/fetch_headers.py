"""Archive the linked workbook; decode bounded text header cells, never numeric payloads."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_source_qualification'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
URL = 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41587-024-02218-y/MediaObjects/41587_2024_2218_MOESM2_ESM.xlsx'


def main():
    dest = OUT / 'supplement.xlsx'
    if dest.exists():
        raise RuntimeError('Do not silently overwrite an archived response')
    receipt = {'url': URL, 'start_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'scope': 'worksheet identities and text-only cells in first four rows; numeric payloads redacted'}
    try:
        with urlopen(Request(URL, headers={'User-Agent': 'MAESTRO-source-qualification/1.0'}), timeout=45) as response:
            receipt.update(status=response.status, final_url=response.geturl(), headers=dict(response.headers))
            digest = hashlib.sha256()
            total = 0
            with dest.open('wb') as target:
                while block := response.read(1024 * 1024):
                    target.write(block)
                    digest.update(block)
                    total += len(block)
                    if total > 256 * 1024 * 1024:
                        raise RuntimeError('Workbook exceeds enlarged 256MiB download bound')
            receipt.update(bytes=total, sha256=digest.hexdigest())
    except Exception as exc:
        receipt['failure'] = str(exc)
        raise
    finally:
        receipt['end_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (OUT / 'SUPPLEMENT_MEDIA_LARGE_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')

    with zipfile.ZipFile(dest) as archive:
        names = archive.namelist()
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        sheets = [dict(e.attrib) for e in workbook.findall('s:sheets/s:sheet', NS)]
        strings = ET.fromstring(archive.read('xl/sharedStrings.xml')) if 'xl/sharedStrings.xml' in names else []
        headers = {}
        for name in names:
            if not (name.startswith('xl/worksheets/sheet') and name.endswith('.xml')):
                continue
            tree = ET.fromstring(archive.read(name))
            cells = []
            for row in tree.findall('s:sheetData/s:row', NS):
                if int(row.attrib['r']) > 4:
                    continue
                for cell in row.findall('s:c', NS):
                    typ = cell.attrib.get('t', 'n')
                    item = {'coordinate': cell.attrib['r'], 'type': typ}
                    value = cell.find('s:v', NS)
                    if cell.find('s:f', NS) is not None:
                        item['text'] = '[FORMULA NOT DECODED]'
                    elif typ == 's' and value is not None:
                        item['text'] = ''.join(strings[int(value.text)].itertext())
                    elif typ == 'inlineStr':
                        item['text'] = ''.join(cell.find('s:is', NS).itertext())
                    else:
                        item['text'] = '[NON-TEXT PAYLOAD NOT DECODED]'
                    cells.append(item)
            headers[name] = cells
        result = {'archive_members': names, 'sheets': sheets, 'text_header_limit_rows': 4, 'headers': headers}
    (OUT / 'WORKBOOK_HEADERS.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'sheets': sheets, 'headers_saved': str(OUT / 'WORKBOOK_HEADERS.json')}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
