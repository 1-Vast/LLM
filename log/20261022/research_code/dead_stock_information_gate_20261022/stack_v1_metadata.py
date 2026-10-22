"""One primary-linked v1 landing metadata request, never response arrays."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'research/functional_dynamics_gate_20261022'))
import root_data_scout as fetch
fetch.OUT = ROOT/'log/20261022/dead_stock_information_gate/root_stack'


def main():
    receipt, raw = fetch.get('stack_v1_landing', 'https://data.mendeley.com/datasets/3pnv5wh5jm/1')
    result = {'http_status': receipt.get('status'), 'bytes': len(raw)}
    if receipt.get('status') == 200:
        text = raw.decode('utf-8')
        pos = text.find('window.INITIAL_STATE')
        if pos >= 0:
            state, _ = json.JSONDecoder().raw_decode(text[pos:].partition('=')[2].lstrip())
            fetch.write(fetch.OUT/'V1_INITIAL_STATE.json', state)
            result.update(dataset=state.get('dataset'), files=state.get('files'))
    fetch.write(fetch.OUT/'V1_PROJECTION.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
