"""Offline exact initial state, not browser execution or another request."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/dead_stock_information_gate/root_stack'
raw = (OUT/'stack_landing.body').read_text(encoding='utf-8')
position = raw.index('window.INITIAL_STATE')
tail = raw[position:].partition('=')[2].lstrip()
state, _ = json.JSONDecoder().raw_decode(tail)
with (OUT/'INITIAL_STATE.json').open('x', encoding='utf-8') as f:
    json.dump(state, f, indent=2, ensure_ascii=False)
print(json.dumps({k: v for k, v in state.items() if k in ['dataset', 'files', 'config', 'error']}, ensure_ascii=False))
