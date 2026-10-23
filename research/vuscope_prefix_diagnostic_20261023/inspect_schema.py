"""Inspect release headers and source text without decoding trajectory rows."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/vuscope_prefix_diagnostic'
ARCHIVE = ROOT / 'log/20261023/functional_transition_law/root_sources/release.zip.body'

if __name__ == '__main__':
    target = OUT / 'SCHEMA_METADATA_ONLY.json'
    assert not target.exists()
    metadata = dict(archive_sha256=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(), headers={}, source_text={})
    with ZipFile(ARCHIVE) as archive:
        for name in archive.namelist():
            if '/input/data/' in name and name.endswith('.txt'):
                # Stop on the known header before reading any trajectory row.
                lines = []
                with archive.open(name) as stream:
                    for raw in stream:
                        text = raw.decode('utf-8-sig', errors='replace').rstrip('\r\n')
                        lines.append(text)
                        if 'Elapsed' in text.split('\t'):
                            break
                        if len(lines) >= 12:
                            break
                metadata['headers'][name] = lines
            if name.endswith(('/scripts/preprocessing.py', '/scripts/utils.py', '/scripts/fit_surface.py', '/configfiles/config.yaml')):
                metadata['source_text'][name] = archive.read(name).decode('utf-8')
    target.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(headers=metadata['headers'], sources=list(metadata['source_text'])), ensure_ascii=False, indent=2))
