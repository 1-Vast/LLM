"""Read existing paper text and source only; never load assays or checkpoints."""
import hashlib
import json
from pathlib import Path

out = Path('log/20261022/revision_value_operation/frontier')
base = Path('log/20261022/post_almanac_mechanism/frontier/sources')
queries = {
    'biology_loop.readable.txt': [('RL fine-tuning. The supervised policy', -1, 3700), ('4.2 Dataset and benchmark construction', -1, 2200)],
    'amortized_reasoning.readable.txt': [('4.1 How should', -1, 6500), ('Decoupling the Generative Model', -1, 2500)],
    'deep_screening.readable.txt': [('3.2 Analytical Marginalisation', -1, 3800), ('5.6 Limitations', -1, 1700)],
}
records = []
for name, selections in queries.items():
    path = base / name
    text = path.read_text(encoding='utf8')
    for needle, last, length in selections:
        start = text.rfind(needle) if last else text.find(needle)
        passage = text[start:start+length] if start >= 0 else 'NOT_FOUND'
        records.append({'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'needle': needle, 'start_character': start, 'passage': passage})
(out / 'SOURCE_PASSAGES.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf8')
for record in records:
    print(record['path'], record['needle'], '\n', record['passage'], '\n')
