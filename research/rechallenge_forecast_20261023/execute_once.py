"""Bind final reviewed inputs and retain the single actual execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/rechallenge_forecast'

if __name__ == '__main__':
    names = [
        'log/20261023/rechallenge_forecast/PROTOCOL.md',
        'research/rechallenge_forecast_20261023/forecast.py',
        'research/rechallenge_forecast_20261023/test_isolation.py',
        'research/rechallenge_forecast_20261023/execute_once.py',
        'log/20261023/rechallenge_forecast/TEST_RECORD.json',
        'log/20261023/rechallenge_forecast/critic/CODE_PRE_REVIEW.md',
        'log/20261023/rechallenge_forecast/source/PARSER_PRE_REVIEW.md',
        'log/20261023/rechallenge_task/root/transition_exp3.body',
        'log/20261023/rechallenge_task/root/transition_exp4.body',
    ]
    assert not (OUT / 'FREEZE.json').exists()
    assert not (OUT / 'pilot').exists()
    files = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}
    (OUT / 'FREEZE.json').write_text(json.dumps(dict(files=files, utc=datetime.now(timezone.utc).isoformat()), indent=2), encoding='utf-8', newline='\n')
    run = subprocess.run([sys.executable, '-B', str(ROOT / 'research/rechallenge_forecast_20261023/forecast.py')],
                         cwd=ROOT, text=True, capture_output=True)
    (OUT / 'EXECUTION.json').write_text(json.dumps(dict(returncode=run.returncode, stdout=run.stdout, stderr=run.stderr,
                                                       utc=datetime.now(timezone.utc).isoformat()), indent=2), encoding='utf-8', newline='\n')
    print(run.stdout)
    print(run.stderr)
    sys.exit(run.returncode)
