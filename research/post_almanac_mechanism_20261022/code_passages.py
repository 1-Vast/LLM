"""Exact line ranges from pinned official source; no execution of author code."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_almanac_mechanism/root/assay_code'


def main():
    path = OUT / 'SELECTED_CODE_PASSAGES.json'
    assert not path.exists()
    lines = (OUT / 'src_assayloop_amortized_rl.body').read_text(encoding='utf-8').splitlines()
    ranges = ((334, 350), (392, 404), (450, 480), (490, 520), (650, 710), (1085, 1105))
    output = {f'{a}-{b}': '\n'.join(f'{i}: {lines[i - 1]}' for i in range(a, b + 1)) for a, b in ranges}
    path.write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(output['490-520'])
    print(output['650-710'])


if __name__ == '__main__':
    main()
