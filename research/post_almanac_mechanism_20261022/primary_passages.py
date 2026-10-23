"""Bounded root re-reading of already authenticated AssayLoop primary passages."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/post_almanac_mechanism'


def main():
    source = PHASE / 'frontier/sources/biology_loop.readable.txt'
    text = source.read_text(encoding='utf-8')
    passages = {}
    for label, length in (('4.5 Training procedure', 7000), ('RL context-delta reward.', 6500),
                          ('D.2 GRPO', 6500), ('D.4.2 GRPO', 4500)):
        start = text.rfind(label)
        assert start >= 0, label
        passages[label] = text[start:start + length]
    output = PHASE / 'root/ASSAYLOOP_PASSAGES.json'
    assert not output.exists()
    output.write_text(json.dumps({'source': source.relative_to(ROOT).as_posix(),
                                  'scope': 'bounded primary passages, not full paper/code replication',
                                  'passages': passages}, indent=2), encoding='utf-8')
    for label, passage in passages.items():
        print(label)
        print(passage)


if __name__ == '__main__':
    main()
