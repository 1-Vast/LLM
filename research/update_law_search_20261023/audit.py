"""Independent arithmetic/source continuity audit, no biological values or refits."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/update_law_search'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sealed = 0
    for role in ['mechanism', 'skeptic', 'task']:
        receipt = json.loads((OUT / role / 'INDEPENDENT_SEAL.json').read_text(encoding='utf-8'))
        for name, expected in receipt.get('files', receipt).items():
            assert digest(ROOT / name) == expected, name
            sealed += 1
        assert (OUT / role / 'CROSS.md').is_file()
    assert (OUT / 'mechanism/TASK_CROSS.md').is_file()
    assert (OUT / 'skeptic/API_REVIEW.md').is_file()
    witness = json.loads((OUT / 'mechanism/WITNESS.json').read_text())
    checks = []
    for model in witness['models']:
        c = Fraction(str(model['c']))
        expected = float(1 / (1 - c) + 1)
        pair = model['regimes'][-1]
        assert abs(pair['function'] - expected) < 1e-14
        inferred_c = (Fraction(str(expected)) - 2) / (Fraction(str(expected)) - 1)
        assert abs(float(inferred_c) - float(c)) < 1e-14
        assert max(pair['eigenvalues']) < 0
        checks.append({'c': float(c), 'pair_function': expected, 'mixed_probe_identifies_known_toy_c': True})
    gauge = json.loads((OUT / 'skeptic/GAUGE_CHECK.json').read_text())
    exact_rotated_ratio = float(Fraction(400, 10201))
    assert np.allclose(gauge['original']['pure_decoupling_ratio'], [1, 1], rtol=0, atol=1e-14)
    assert np.allclose(gauge['rotated']['pure_decoupling_ratio'], exact_rotated_ratio, rtol=0, atol=1e-14)
    assert abs(gauge['original']['a_optimal_trace'] - gauge['rotated']['a_optimal_trace']) < 1e-13
    api = json.loads((OUT / 'api/RECEIPT.json').read_text())
    assert api['status'] == 'RESPONSE_RETAINED' and api['finish_reason'] == 'stop'
    assert digest(OUT / 'api/PROMPT.md') == api['prompt_sha256']
    for name, expected in api['context_hashes'].items():
        assert digest(OUT / name) == expected
    predecessor = json.loads((ROOT / 'log/20261023/reciprocity_resolution/VERIFICATION.json').read_text())
    for name, expected in predecessor['files'].items():
        assert digest(ROOT / name) == expected, name
    report = {'status': 'PASS_LOCAL', 'independent_sealed_files_checked': sealed,
              'predecessor_files_unchanged': len(predecessor['files']), 'toy_arithmetic': checks,
              'exact_rotated_ratio': exact_rotated_ratio, 'api_provider_usage': api['provider_usage'],
              'scope': 'Saved mathematical arithmetic, source/report/prompt hashes and local continuity only; not biological utility or global provenance repair'}
    (OUT / 'AUDIT.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    files = {}
    for folder in [OUT, Path(__file__).resolve().parent]:
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.name != 'VERIFICATION.json':
                files[path.relative_to(ROOT).as_posix()] = digest(path)
    (OUT / 'VERIFICATION.json').write_text(json.dumps({'files': files, **report}, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
