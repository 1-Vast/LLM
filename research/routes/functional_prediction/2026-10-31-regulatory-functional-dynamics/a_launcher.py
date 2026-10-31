"""Hash-checked single-matrix launcher with a hard process timeout."""
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import time

HERE = pathlib.Path(__file__).resolve().parent
PYTHON = 'D:/anaconda/envs/maestro/python.exe'


def main():
    freeze = json.loads((HERE / 'a_freeze.json').read_text(encoding='utf-8'))
    for name, expected in freeze['files'].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == expected, name
    assert freeze['scientific_admission'] == 'ADMITTED_NARROW_RAW_ENDPOINT_PROBE'
    assert freeze['arithmetic_access_review'] == 'PASS_SYNTHETIC_AND_STATIC_ONLY'
    receipt = HERE / 'a_launch_receipt.json'
    assert not receipt.exists(), 'Original launcher cannot be rerun; preserve any failed attempt.'
    env = os.environ.copy()
    env.update(json.loads((HERE / 'runtime_environment.json').read_text())['launcher_thread_caps'])
    started = time.monotonic()
    status = {'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'timeout_seconds': 1800, 'thread_caps': {k: env[k] for k in
                  json.loads((HERE / 'runtime_environment.json').read_text())['launcher_thread_caps']},
              'matrix_number': 1, 'spare_used': False, 'status': 'RUNNING'}
    receipt.write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
    with (HERE / 'a_run_stdout.txt').open('wb') as stdout, (HERE / 'a_run_stderr.txt').open('wb') as stderr:
        try:
            run = subprocess.run([PYTHON, '-X', 'utf8', str(HERE / 'a_experiment.py')],
                                 cwd=HERE.parents[3], env=env, stdout=stdout, stderr=stderr, timeout=1800)
            status.update(status='COMPLETE' if run.returncode == 0 else 'FAILED', returncode=run.returncode)
        except subprocess.TimeoutExpired:
            status.update(status='TIMEOUT', returncode=None)
    status.update(elapsed_seconds=time.monotonic() - started,
                  finished_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    receipt.write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(status, indent=2))
    if status['status'] != 'COMPLETE':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
