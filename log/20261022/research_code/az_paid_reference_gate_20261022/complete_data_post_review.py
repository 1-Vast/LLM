"""Append actual cross-review and verify the three pre-target artifact bindings."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/az_paid_reference_gate'
PATH = LOG / 'DATA_POST_RESULT_REVIEW.json'
MD = LOG / 'DATA_POST_RESULT_REVIEW.md'
BEFORE = LOG / 'DATA_POST_RESULT_REVIEW_PRE_CROSS_SHA.json'
if BEFORE.exists():
    raise SystemExit('Final cross append already recorded; refusing to repeat')
def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()
def read(name):
    return json.loads((LOG / name).read_text(encoding='utf-8'))
BEFORE.write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
    'before_cross_append_sha256': {PATH.name: sha(PATH), MD.name: sha(MD)}}, indent=2) + '\n', encoding='utf-8')
result = read(PATH.name)
receipt, started, seal, evaluation, inputs = (read(name) for name in
    ('TEST_TARGETS_RECEIPT.json', 'TEST_TARGETS_STARTED.json', 'PREDICTIONS_SEAL.json',
     'EVALUATION_STARTED.json', 'INPUTS_RECEIPT.json'))
binding = {}
for field, name in (('predictions_sha256', 'TEST_PREDICTIONS.npz'),
                    ('actions_sha256', 'TEST_ACTIONS.json'), ('selection_sha256', 'SELECTION.json')):
    actual = sha(LOG / name)
    result['checks']['seal_actual_' + field] = actual == seal[field] == started[field] == receipt[field]
    binding[name] = actual
for field, path in (('code_sha256', ROOT / 'research/az_paid_reference_gate_20261022/prepare.py'),
                    ('protocol_sha256', LOG / 'MEASURED_PROTOCOL.md'),
                    ('design_sha256', LOG / 'DESIGN.json'), ('schema_sha256', LOG / 'FEATURE_SCHEMA.json')):
    result['checks']['frozen_stage_' + field] = sha(path) == inputs[field] == started[field] == receipt[field]
result['checks']['archive_binding_receipts_only'] = inputs['archive_expected_sha256'] == started['archive_expected_sha256'] == receipt['archive_expected_sha256']
result['checks']['evaluation_target_binding'] = evaluation['test_targets_sha256'] == receipt['outputs_sha256']['TEST_TARGETS.npz'] == sha(LOG / 'TEST_TARGETS.npz')
result['checks']['seal_fit_count_metadata'] = seal['pipeline_fits'] == result['reported_compute_costs']['pipeline_fits'] == 53 and seal['selection_fits'] == 48 and seal['unique_final_fits'] == 5
result['access']['predictions_actions_selection_bytes_hashed'] = True
result['access']['predictions_actions_selection_numerical_values_loaded'] = False
result['seal_check'] = {'artifact_hashes': binding,
    'source_archive_reopened': False, 'raw_source_order_forensically_reconstructed': False,
    'basis': 'Current bytes equal three artifact seals in PREDICTIONS_SEAL, TEST_TARGETS_STARTED and TEST_TARGETS_RECEIPT. Inspected prepare.verify_predictions runs before target scan. Local receipts are not an external audit attestation.'}
result['cross_review'] = {'status': 'COMPLETED', 'unresolved_directional_disagreements': [], 'responses': [
    {'peer': 'mechanism_advocate', 'auditor_question': 'Can unresolved chemical mapping, CTG endpoint limits, conditional MASTER bootstrap or resource differences change the primary STOP?',
     'peer_answer': 'No. Source-ID separation does not establish chemical independence; unknown is not proved alias leakage. CTG is not death/efficacy. Bootstrap is internal conditional evidence. Resource differences cannot rescue a failed registered gate.',
     'peer_counterquestion': 'Can a small full-vs-without_mono input-package MAE difference and uncertain utility tradeoff be retained without erasing all mono input value?',
     'auditor_answer': 'Yes as pipeline-level descriptive input-package comparison; not pure mono causal attribution because representation dimensions and validation choices differ. Other-pair attached mono fields are not independent target monotherapy gold standards. Plateau diagnostics without replicate-noise decomposition cannot rule out all functional world models.',
     'peer_final_confirmation': 'Accepted. Peer reports MAE gain +0.00116134 CI [-0.000363916,0.00268744], utility gain -0.00338165 CI [-0.00728317,0.000515178]; both cross zero. Only an uncertain descriptive tradeoff is retained, not proven mono usefulness.'},
    {'peer': 'scientific_skeptic', 'auditor_question': 'Does chemical unknown invalidate this source-ID pilot or prove leakage? Do CTG or MASTER CIs establish death, external independence or permit resource-based gate revision?',
     'peer_answer': 'No. The source-ID task remains legitimate; only the stronger unpurchased chemical-pair claim is unestablished. CTG is not direct death. MASTER bootstrap is source-internal conditional uncertainty. Registered STOP does not change.',
     'peer_counterquestion': 'Confirm chemical unknown cannot authorize pool changes/ID merges/target reselection, and this negative family result cannot disprove every static world/mono/RSI approach.',
     'auditor_answer': 'Confirmed. No pool changes, merges or reselection. Preserve uncertain pipeline-level package differences, not global mechanism or mono-value conclusions. Independently align MASTER contributions with TEST_METRICS lexsorted assigned_masters.',
     'peer_final_confirmation': 'No unresolved disagreement. Peer disclosed initial independent verification CI mismatch from DESIGN order versus production lexsorted MASTER order; original failure retained, corrected verification reportedly PASS with zero differences. This data audit independently checks lexsorted contribution counts/macros; it does not rewrite that audit history.'}
]}
result['status'] = 'PASS' if all(result['checks'].values()) else 'FAIL'
result['completion_utc'] = datetime.now(timezone.utc).isoformat()
result['completion_code_sha256'] = sha(Path(__file__))
PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
text = MD.read_text(encoding='utf-8')
text = text.replace('Cross-review is pending actual peer responses. Numerical and access details are in DATA_POST_RESULT_REVIEW.json.',
    'Actual cross-review and seal verification are complete. Numerical, access and bidirectional response records are in DATA_POST_RESULT_REVIEW.json.')
text += '''

## Three seals and access boundary

Byte-hashed TEST_PREDICTIONS.npz, TEST_ACTIONS.json and SELECTION.json without loading their prediction/action values. Each current hash equals PREDICTIONS_SEAL, TEST_TARGETS_STARTED and TEST_TARGETS_RECEIPT. Preparation code, measured protocol, design and feature schema hashes agree with the original input and target stages. Evaluation binds to the same target artifact hash. The inspected target reader verifies these three artifacts before scanning source targets. Source archive hash is bound by receipts, not independently recomputed here; local artifacts do not provide an external forensic attestation.

No read failed in this post-result audit. The first terminal displays of TEST_MISSINGNESS/TEST_METRICS exceeded display limits; the files were intact and later fully parsed with recorded SHA256 for the 171-check independent numerical core. The final seal append adds ten checks. No additional source download, fitting, target conversion or reserve numerical access was performed. New audit files and code do not alter historical qualification or frozen results.

## Actual bidirectional post-result cross-review

Both advocate and skeptic accepted the three scope limits and unchanged STOP. I challenged any interpretation that chemical uncertainty proves leakage, CTG proves death, or internal CIs imply external assay independence; neither maintains those claims. They also accepted that resource advantages cannot change either registered performance failure.

The advocate challenged overreading the candidate failure as proving all mono inputs useless. I accepted only a descriptive full-versus-without_mono pipeline comparison, with representation/selection confounding and attached-other-pair reference limits. Both peers then pointed out that its MAE and utility CIs cross zero: no established mono improvement follows. We retain an uncertain endpoint tradeoff, not a new positive claim. I also rejected using the approximate-coordinate plateau diagnostic without replicate noise to dismiss all functional world models.

The skeptic challenged any future chemical-mapping-driven pool change, ID merge or target reselection, and any universal inference against static world models or RSI. I accepted those limits. The skeptic disclosed a separate initial CI verification failure due to MASTER vector ordering, retained that history, and reported corrected pure verification PASS. My independently computed MASTER counts and macros use the result's lexsorted assigned_masters order and pass. No method, endpoint, panel or registered decision was changed. No directional dispute remains; chemical identity and external scientific generalization remain unresolved empirical limitations.
'''
MD.write_text(text, encoding='utf-8')
print(json.dumps({'status': result['status'], 'checks': len(result['checks']),
                  'failed': [key for key, value in result['checks'].items() if not value],
                  'cross_review': result['cross_review']['status'],
                  'final_sha256': {PATH.name: sha(PATH), MD.name: sha(MD)}}))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
