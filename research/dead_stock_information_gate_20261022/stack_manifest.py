"""One registered landing-page metadata GET; no response-array access."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'research/functional_dynamics_gate_20261022'))
import root_data_scout as fetch

fetch.OUT = ROOT/'log/20261022/dead_stock_information_gate/root_stack'


def main():
    receipt, raw = fetch.get('stack_landing', 'https://data.mendeley.com/datasets/3pnv5wh5jm/2')
    text = raw.decode('utf-8', errors='replace')
    snippets = [m.group(0) for m in re.finditer(
        r'.{0,100}(?:download_url|filename|file_name|downloadUrl|__INITIAL_STATE__|__NEXT_DATA__).{0,400}',
        text)]
    projection = {'status': receipt.get('status'), 'bytes': len(raw),
                  'manifest_snippets': snippets[:20], 'response_values_accessed': False}
    fetch.write(fetch.OUT/'PROJECTION.json', projection)
    print(json.dumps(projection, ensure_ascii=False))


if __name__ == '__main__':
    main()
