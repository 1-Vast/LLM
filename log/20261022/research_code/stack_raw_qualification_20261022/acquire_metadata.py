"""Fetch registered metadata or manifest-derived bytes without inspecting cells."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'research/functional_dynamics_gate_20261022'))
import root_data_scout as fetch

fetch.OUT = ROOT / 'log/20261022/stack_raw_qualification/network'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('url')
    parser.add_argument('--cap', type=int, default=8_000_000)
    args = parser.parse_args()
    receipt, _ = fetch.get(args.name, args.url, cap=args.cap)
    print({key: value for key, value in receipt.items() if key != 'body_path'})
    return 0 if receipt.get('status') == 200 and 'error_type' not in receipt else 1


if __name__ == '__main__':
    raise SystemExit(main())
