"""Freeze protocol, implementation, raw inputs and metadata before one run."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from source import ROOT, OUT

if __name__ == '__main__':
    target = OUT/'PREDICTION_FREEZE.json'
    assert not target.exists() and not (OUT/'PREDICTION_RESULTS.json').exists()
    paths = [OUT/'PREDICTION_PROTOCOL.md', OUT/'SCHEMA_LITERAL.json', OUT/'commit.json',
             ROOT/'research/cxcl9_source_feasibility_20261023/predict.py',
             ROOT/'research/cxcl9_source_feasibility_20261023/source.py',
             Path(__file__)]
    paths += sorted((OUT/'raw').glob('*.csv'))
    paths += sorted((OUT/'source').rglob('metadata.md'))
    files = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in paths}
    target.write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'files': files,
                                  'scope': 'Pre-outcome source/target pilot freeze'}, indent=2), encoding='utf-8')
    print(json.dumps({'frozen_files': len(files)}))
