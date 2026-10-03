#!/usr/bin/env bash
set -eu
# Run in WSL/Ubuntu; all receipts go to a new directory supplied by the caller.
study_root="${1:?source repository}"
verify_checkout="${2:?new Linux checkout directory}"
verify_env="${3:?isolated Python environment directory}"
receipt_root="${4:?new output directory}"
mkdir -p "$receipt_root"
git clone --no-local --depth 1 --branch main "$study_root" "$verify_checkout" > "$receipt_root/linux_clone.txt" 2>&1
cd "$verify_checkout"
git rev-parse HEAD > "$receipt_root/linux_source_commit.txt"
git status --porcelain > "$receipt_root/linux_initial_status.txt"
"$verify_env/bin/python" -m pip install --quiet -e '.[test]' > "$receipt_root/linux_core_install.txt" 2>&1
"$verify_env/bin/python" -m pip freeze > "$receipt_root/linux_core_packages.txt"
"$verify_env/bin/python" -m pytest -o addopts= -q --junitxml="$receipt_root/core_linux_clean.xml" > "$receipt_root/core_linux_clean.txt" 2>&1
"$verify_env/bin/python" -m pip install --quiet pandas > "$receipt_root/linux_regression_install.txt" 2>&1
"$verify_env/bin/python" -m pip freeze > "$receipt_root/linux_regression_packages.txt"
set +e
"$verify_env/bin/python" -m pytest research/case_memory_integration/test_external_evaluation.py research/astra/test_reproducibility_audit.py -m regression -o addopts= -q --junitxml="$receipt_root/regression_linux_unprepared.xml" > "$receipt_root/regression_linux_unprepared.txt" 2>&1
regression_unprepared_status=$?
set -e
printf '%s\n' "$regression_unprepared_status" > "$receipt_root/regression_linux_unprepared_exit.txt"
"$verify_env/bin/python" - "$receipt_root" <<'PY'
import json, sys
from pathlib import Path
from research.astra.reproducibility_audit import restore_fixtures
root = Path.cwd()
base = root / 'research/astra/results/20261003_prediction_audit_fix_v1'
receipts = [restore_fixtures(base / name, root) for name in
            ('replay_fixture_bundle.zip', 'legacy_fixtures_v3/replay_fixture_bundle.zip')]
with (Path(sys.argv[1]) / 'linux_restoration.json').open('x') as stream:
    json.dump({'published_packages_only': True, 'restoration': receipts}, stream, indent=2)
    stream.write('\n')
PY
"$verify_env/bin/python" -m pytest research/case_memory_integration/test_external_evaluation.py research/astra/test_reproducibility_audit.py -m regression -o addopts= -q --junitxml="$receipt_root/regression_linux_restored.xml" > "$receipt_root/regression_linux_restored.txt" 2>&1
git status --porcelain > "$receipt_root/linux_restored_status.txt"
