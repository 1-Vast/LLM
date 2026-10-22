"""Bind the reviewed source-only gate before scalar access."""
import platform
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

from gate import MEMBERS, OUT, ROOT, sha, write


def main():
    assert not (OUT / 'FREEZE.json').exists()
    assert not (OUT / 'RESULT.json').exists()
    names = ['research/mse_source_gate_20261022/' + n for n in
             ('prepare.py', 'gate.py', 'test_gate.py', 'freeze.py')]
    names += ['log/20261022/mse_source_gate/' + n for n in
              ('PATIENT_MENU_MANIFEST.json', 'DRAFT_PROTOCOL.md', 'SCHEMA_AMENDMENT.md',
               'PROTOCOL.md', 'SYNTHETIC_TESTS_READY.txt', 'PREDECODE_ROOT_REPLY.md')]
    names += ['log/20261022/mse_source_gate_audit/' + n for n in
              ('INDEPENDENT_INITIAL.md', 'INDEPENDENT_INITIAL_SEAL.json',
               'MANIFEST_SCHEMA_REVIEW.json', 'PREDECODE_REVIEW.md', 'PREDECODE_REVIEW_SEAL.json')]
    names += ['log/20261022/mse_source_gate_audit/BIOLOGICAL_EXCHANGE.md']
    names += ['log/20261022/mse_source_gate_review/' + n for n in
              ('INDEPENDENT_INITIAL.md', 'INDEPENDENT_INITIAL_SEAL.json', 'PREDECODE_REVIEW.md',
               'PREDECODE_REVIEW_SEAL.json')]
    names += ['log/20261022/biological_decision_scout/sources/' + n for n in
              ('MSE_KEY_AUDIT.json', 'MSE_METHOD_CONTRACT.json', 'mse_primary.body',
               'mse_europepmc_supplements_complete_attempt.body')]
    names += ['log/20261022/contrast_independent_review/MSE_COMMON65_UNIT_QUALIFICATION.json',
              'log/20261022/contrast_gate_check/FINAL_FILE_INVENTORY.json']
    names += [(MEMBERS / f'41467_2024_52694_MOESM{n}_ESM.xlsx').relative_to(ROOT).as_posix() for n in (6, 8)]
    tests = (OUT / 'SYNTHETIC_TESTS_READY.txt').read_text(encoding='utf-8')
    assert 'Ran 6 tests' in tests and '\nOK' in tests
    assert 'gate_sha256=' + sha(ROOT / 'research/mse_source_gate_20261022/gate.py') in tests
    assert 'tests_sha256=' + sha(ROOT / 'research/mse_source_gate_20261022/test_gate.py') in tests
    write('FREEZE.json', {'files': {name: sha(ROOT / name) for name in names},
          'utc': datetime.now(timezone.utc).isoformat(),
          'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
          'numpy': np.__version__, 'random_seed': None, 'randomness': 'none; patient/probe SHA256 ordering fixed in manifest',
          'authorization': 'Source75samples/55patients only, common65pairedraw + raw10composition; one execution',
          'prohibited': 'development/later, earlySTP, nonmenu and scaled scalar access',
          'provider_budget_this_gate': 0, 'predictive_solver_fit_budget': 0,
          'source_required_field_attempts': 10500, 'lopo_descriptive_aggregations_if_valid': 55,
          'on_failure': 'STOP exact frozen task; no threshold/split/probe/data rescue',
          'goal': 'ACTIVE / NOT_ACHIEVED'})
    print('FROZEN: ' + sha(OUT / 'FREEZE.json'))


if __name__ == '__main__':
    main()
