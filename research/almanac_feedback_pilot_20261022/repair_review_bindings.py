"""Preserve and disclose a review-only drift after extraction, before any fitting."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/almanac_feedback_pilot'
OUT = PHASE / 'root'


def main():
    original = OUT / 'PRE_RESPONSE_FREEZE.json'
    manifest = json.loads(original.read_text())
    allowed = {'log/20261022/almanac_feedback_pilot/skeptic/IMPLEMENTATION_REVIEW.md',
               'log/20261022/almanac_feedback_pilot/skeptic/IMPLEMENTATION_REVIEW.seal.json'}
    changed = {}
    for rel, old in manifest['bindings'].items():
        new = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if new != old:
            changed[rel] = {'before_sha256': old, 'after_sha256': new}
    assert set(changed) == allowed, changed
    assert (OUT / 'VALUES.npz').exists()
    assert not (OUT / 'PREDICTIONS.npz').exists() and not (OUT / 'RESULTS.json').exists()
    preserved = OUT / 'PRE_RESPONSE_FREEZE_AT_VALUE_READ.json'
    assert not preserved.exists()
    original.rename(preserved)
    for rel, item in changed.items():
        manifest['bindings'][rel] = item['after_sha256']
    manifest['stage'] = 'post-extraction review-only administrative rebind; models/protocol/split unchanged; before fitting'
    manifest['previous_manifest'] = preserved.relative_to(ROOT).as_posix()
    original.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (OUT / 'POST_EXTRACTION_REVIEW_REBIND.json').write_text(json.dumps({
        'scope': manifest['stage'], 'changed': changed, 'original_manifest_preserved': True,
        'values_already_prepared': True, 'models_protocol_split_and_all_other_old_bindings_unchanged': True,
        'fitting_started': False, 'old_manifest_sha256': hashlib.sha256(preserved.read_bytes()).hexdigest()}, indent=2), encoding='utf-8')
    print('Preserved original freeze; only two reviewer-document bindings updated before model fitting.')


if __name__ == '__main__':
    main()
