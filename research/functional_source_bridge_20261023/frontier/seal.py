from pathlib import Path
import hashlib, json
root = Path('log/20261023/functional_source_bridge/frontier')
sources = []
for name, start, stop in (
    ('ttte2e', '2.2 Learning to (Learn at Test Time)', '2.3 Mini-Batch'),
    ('centaur', '2 Centaur', '3 navsafe'),
):
    text = (root / (name + '.text')).read_text(encoding='utf-8')
    first = text.find(start)
    begin = text.find(start, first + len(start))
    end = text.find(stop, begin + len(start))
    if begin < 0 or end < 0:
        raise ValueError((name, begin, end))
    sources.append({'source': name + '.body', 'text_source': name + '.text', 'start_character': begin, 'end_character': end, 'text': text[begin:end]})
(root / 'METHOD_PASSAGES.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding='utf-8')
paths = list(root.rglob('*')) + list(Path('research/functional_source_bridge_20261023/frontier').rglob('*'))
records = [{'path': p.as_posix(), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths) if p.is_file() and p.name != 'VERIFICATION.json']
(root / 'VERIFICATION.json').write_text(json.dumps({'files': records, 'scope': 'Local frontier artifacts only, not global historical provenance', 'http_requests': 3, 'fits': 0, 'model_api_calls': 0}, indent=2), encoding='utf-8')
print({'sealed_files': len(records)})
