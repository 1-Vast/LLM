"""Freeze executable contract and prior source before numerical biological access."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'log/20261023/depmap_state_increment'

if __name__=='__main__':
    target=OUT/'FREEZE.json';assert not target.exists()
    assert (OUT/'methods/SOURCE_VERSION_ADDENDUM.md').exists()
    assert (OUT/'skeptic/CODE_REVIEW_ADDENDUM.md').exists()
    paths=[p for base in [ROOT/'research/depmap_state_increment_20261023',OUT/'methods',OUT/'skeptic'] for p in base.rglob('*') if p.is_file()]
    paths += [OUT/x for x in ['PROTOCOL_DRAFT.md','PROTOCOL_RESOLUTION.md','ACQUISITION.json','ACQUISITION_RECEIPT.json','SYNTHETIC_TESTS_FINAL.txt']]
    paths += [OUT/'pseudobulk.csv',ROOT/'log/20261023/functional_source_bridge/root/crispr_table.csv',
              ROOT/'log/20261023/functional_source_bridge/root/IDENTITY_JOIN.json',
              ROOT/'log/20261023/functional_source_bridge/VERIFICATION.json']
    files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
    target.write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),
        scope='before biological numeric parsing/fit; source bytes previously acquired',files=files),indent=2),encoding='utf-8')
    print(json.dumps(dict(frozen=len(files))))
