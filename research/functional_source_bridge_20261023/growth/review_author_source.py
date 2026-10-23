"""Read pinned author source only; never import or execute it or inspect outputs."""
import hashlib
import json
from pathlib import Path
import zipfile

root = Path('log/20261023/functional_source_bridge')
source = root / 'root/author_source.zip.body'
ranges = {
    'src/data_utils.py': [(13, 59)],
    'src/generate.py': [(81, 113), (1333, 1410), (1413, 1494),
                        (1654, 1707), (1710, 1754), (1777, 1838), (1914, 1978)],
    'src/figure1.py': [(51, 76)],
    'src/sceptre_benchmark.R': [(39, 100)],
}
records = {}
with zipfile.ZipFile(source) as archive:
    for suffix, selections in ranges.items():
        name = next(n for n in archive.namelist() if n.endswith('/' + suffix))
        payload = archive.read(name)
        lines = payload.decode('utf-8').splitlines()
        records[suffix] = {
            'sha256': hashlib.sha256(payload).hexdigest(),
            'ranges': [
                {'start': lo, 'end': hi,
                 'lines': [{'number': i + 1, 'text': lines[i]}
                           for i in range(lo - 1, hi)]}
                for lo, hi in selections],
        }
result = {'archive_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'executed_author_code': False, 'read_dataset_values': False,
          'source_only': records}
(root / 'growth/AUTHOR_SOURCE_EXCERPTS.json').write_text(
    json.dumps(result, indent=2), encoding='utf-8')
