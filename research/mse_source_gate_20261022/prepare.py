"""Create an outcome-blind patient split and fixed assay menu; no workbook values."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/mse_source_gate'
KEYS = ROOT / 'log/20261022/biological_decision_scout/sources/MSE_KEY_AUDIT.json'
UNITS = ROOT / 'log/20261022/contrast_independent_review/MSE_COMMON65_UNIT_QUALIFICATION.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank(namespace, value):
    return hashlib.sha256((namespace + '\n' + value).encode('utf-8')).hexdigest()


def main():
    keys = json.loads(KEYS.read_text(encoding='utf-8'))
    identity = {r['sample']: r for r in keys['clinical_identity']}
    experiments = {r['sample']: r for r in keys['experiment_identity']}
    samples = sorted(r['sample'] for r in keys['response_masks']['RCN raw']['rows']
                     if experiments[r['sample']]['plate'].startswith(tuple(f'{i}STP' for i in range(2, 8))))
    patients = sorted({identity[s]['patient'] for s in samples},
                      key=lambda p: rank('MSE-source-gate-20261022-patient-v1', p))
    assert len(samples) == 135 and len(patients) == 95
    split = {p: 'source' if i < 55 else 'development' if i < 75 else 'later'
             for i, p in enumerate(patients)}
    drugs = json.loads(UNITS.read_text(encoding='utf-8'))['whitelist']
    assert len(drugs) == len(set(drugs)) == 65
    probes = sorted(drugs, key=lambda d: rank('MSE-source-gate-20261022-fixed-probe-v1', d))[:8]
    manifest = {'split_namespace': 'MSE-source-gate-20261022-patient-v1',
                'split_rule': 'ascending SHA256(namespace + newline + patient); first55/next20/last20',
                'rows': [{'sample': s, 'patient': identity[s]['patient'], 'partition': split[identity[s]['patient']],
                          'design': experiments[s]['plate']} for s in samples],
                'drugs': sorted(drugs), 'fixed_probe_namespace': 'MSE-source-gate-20261022-fixed-probe-v1',
                'probes': probes, 'terminal_drugs': sorted(set(drugs) - set(probes)),
                'clinical_covariates_allowed': [], 'composition_available_only_at_checkpoint': True,
                'input_hashes': {str(p.relative_to(ROOT).as_posix()): sha(p) for p in (KEYS, UNITS)}}
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'PATIENT_MENU_MANIFEST.json').open('x', encoding='utf-8') as handle:
        json.dump(manifest, handle, indent=2)
    counts = {part: {'patients': len({r['patient'] for r in manifest['rows'] if r['partition'] == part}),
                     'samples': sum(r['partition'] == part for r in manifest['rows'])}
              for part in ('source', 'development', 'later')}
    print(json.dumps({'partitions': counts, 'probes': probes, 'endpoint_scalar_accesses': 0}))


if __name__ == '__main__':
    main()
