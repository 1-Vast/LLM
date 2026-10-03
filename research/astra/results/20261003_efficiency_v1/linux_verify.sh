#!/usr/bin/env bash
set -eu
# Use new checkout/environment/output directories; do not reuse frozen receipts.
source_repo="${1:?source repository}"
verify_checkout="${2:?new native Linux checkout}"
verify_env="${3:?new isolated environment}"
receipt_root="${4:?new receipt directory}"
bootstrap="${5:?cached get-pip.py}"
mkdir -p "$receipt_root"
git clone --no-local --depth 1 --branch main "$source_repo" "$verify_checkout" > "$receipt_root/clone.txt" 2>&1
cd "$verify_checkout"
git rev-parse HEAD > "$receipt_root/source_commit.txt"
git status --porcelain > "$receipt_root/initial_status.txt"
python3 -m venv --without-pip "$verify_env"
"$verify_env/bin/python" "$bootstrap" > "$receipt_root/bootstrap.txt" 2>&1
"$verify_env/bin/python" -m pip install --quiet -e '.[test]' > "$receipt_root/install.txt" 2>&1
"$verify_env/bin/python" -m pip freeze > "$receipt_root/packages.txt"
"$verify_env/bin/python" -m pytest -o addopts= -q --junitxml="$receipt_root/core.xml" > "$receipt_root/core.txt" 2>&1
git status --porcelain > "$receipt_root/final_status.txt"
