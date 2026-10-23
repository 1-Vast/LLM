"""Inspect nested source archive structure and first CSV lines with numeric masking."""
import io
import json
from pathlib import Path
import re
import zipfile

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/rechallenge_task/root'

if __name__ == '__main__':
    results = []
    with zipfile.ZipFile(OUT / 'transition_supplements.body') as outer:
        for name in ('44320_2025_150_MOESM4_ESM.zip', '44320_2025_150_MOESM6_ESM.zip'):
            with zipfile.ZipFile(io.BytesIO(outer.read(name))) as inner:
                files = []
                for entry in inner.infolist():
                    item = dict(name=entry.filename, bytes=entry.file_size)
                    if '__MACOSX/' in entry.filename or entry.filename.rsplit('/', 1)[-1].startswith('._'):
                        item['scope'] = 'Archive operating-system metadata, not a CSV assay file'
                    elif entry.filename.endswith('.csv'):
                        # Decode at most the first physical line; numeric fields
                        # are never converted to response values or displayed.
                        raw_line = inner.read(entry.filename).splitlines()[0]
                        try:
                            first = raw_line.decode('utf-8-sig')
                            item['header_encoding'] = 'utf-8-sig'
                        except UnicodeDecodeError:
                            first = raw_line.decode('cp1252')
                            item['header_encoding'] = 'cp1252'
                        item['first_line_numeric_masked'] = re.sub(r'(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)?(?:[Ee][-+]?\d+)?', '[NUMBER]', first)
                    files.append(item)
                results.append(dict(archive=name, files=files))
    destination = OUT / 'SUPPLEMENT_STRUCTURE.json'
    assert not destination.exists()
    destination.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
