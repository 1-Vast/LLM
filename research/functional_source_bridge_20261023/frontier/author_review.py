from pathlib import Path
import hashlib, json, zipfile
source = Path('log/20261023/functional_source_bridge/root/author_source.zip.body')
out = Path('log/20261023/functional_source_bridge/frontier')
records = []
with zipfile.ZipFile(source) as z:
    for suffix, intervals in {
        'src/data_utils.py': [(19, 27), (49, 58)],
        'src/generate.py': [(79, 113), (268, 286)],
    }.items():
        name = next(n for n in z.namelist() if n.endswith(suffix))
        body = z.read(name)
        lines = body.decode().splitlines()
        records.append({'member': name, 'sha256': hashlib.sha256(body).hexdigest(), 'excerpts': [{'first_line': a, 'last_line': b, 'text': '\n'.join(lines[a-1:b])} for a,b in intervals]})
(out / 'AUTHOR_CODE_PASSAGES.json').write_text(json.dumps({'archive': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'records': records, 'execution': 'author code not executed'}, indent=2), encoding='utf8')
paths = [out / 'AUTHOR_CODE_PASSAGES.json', out / 'AUTHOR_SOURCE_ADDENDUM.md', Path(__file__)]
(out / 'ADDENDUM_SEAL.json').write_text(json.dumps([{'path': p.as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths], indent=2), encoding='utf8')
