"""Verify immutable draft, source hash binding, field joins and metadata geometry."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_value_qualification/data'
started = time.perf_counter()
checks = []


def check(name, condition):
    checks.append({'name': name, 'pass': bool(condition)})
    if not condition:
        raise AssertionError(name)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


independent_sha = 'd92f8306f37918ad65b58fe0a7e17ff2dd285d043ece1a43fecdf7d6b4cb0e56'
check('Independent first draft unchanged', sha(OUT / 'INDEPENDENT.md') == independent_sha)
prism = load('PRISM_METADATA_QUALIFICATION.json')
follow = load('METADATA_FOLLOWUP.json')
contract = load('FIELD_CONTRACT.json')
geometry = load('MANIFEST_GEOMETRY.json')
depmap = load('DEPMAP_METADATA_JOIN.json')
old = json.loads((ROOT / 'research/anchor_purchase_20261016/FREEZE.json').read_text())['inputs']
for name, digest in prism['metadata_hashes'].items():
    path = ROOT / 'data/external/prism_19q4/raw' / name
    check('Current metadata hash ' + name, sha(path) == digest)
    key = path.relative_to(ROOT).as_posix()
    if key in old:
        check('Historical metadata hash/exposure binding ' + name, digest == old[key])
for name, record in follow['matrices'].items():
    path = ROOT / 'data/external/prism_19q4/raw' / name
    check('Current byte hash ' + name, sha(path) == record['sha256'])
    check('Unique row IDs ' + name, record['duplicate_row_ids'] == 0)
    check('Unique column IDs ' + name, record['duplicate_column_ids'] == 0)
    check('No response conversion flag ' + name, record['numerical_response_conversion'] is False)
    key = path.relative_to(ROOT).as_posix()
    if key in old:
        check('Historical secondary hash/exposure binding', old[key] == record['sha256'])
for name in ('primary-screen-readme.txt', 'secondary-screen-readme.txt'):
    path = ROOT / 'data/external/prism_19q4/raw' / name
    check('Historical source README binding ' + name, sha(path) == old[path.relative_to(ROOT).as_posix()])
check('Exact-dose metadata triple count', prism['hts002_exact_2p5uM']['complete_core_triples'] == 1280)
check('Preserved parser failure evidence', load('PRISM_METADATA_QUALIFICATION_parser_v1.json')['hts002_exact_2p5uM']['complete_core_triples'] == 795)
check('Corrected plate parser complete', follow['unparsed_plate_names'] == [] and follow['incomplete_exact_dose_count'] == 0)
check('Header complete ceiling', contract['header_complete_triples'] == 1279)
check('Chemistry complete ceiling', len(contract['catalog']) == contract['header_complete_chemistry_resolved'] == 1274)
check('No fit registration', contract['status'] == 'FIELD_CONTRACT_ONLY_NOT_FIT_REGISTRATION')
check('No finite coverage invented', contract['finite_coverage'] == 'UNREAD')
check('Twenty actual eligible pool groups', len(contract['pool_rows']) == contract['full_profile_pool_units'] == 20)
check('481 row membership slots', sum(map(len, contract['pool_rows'].values())) == contract['full_profile_nominal_field_slots'] == 481)
check('Pool rows form disjoint partition', len({r for rows in contract['pool_rows'].values() for r in rows}) == 481)
check('481 row IDs actually in matrix', follow['matrices']['secondary-screen-logfold-change.csv']['eligible_contexts_missing_matrix'] == [])
check('Exact absent profile retained', follow['matrices']['secondary-screen-logfold-change.csv']['selected_columns_missing_header'] == ['PREP025_CS5_X3:A13::HTS002'])
check('Excluded core mapping', geometry['missing_header_cores'] == ['BRD-K37618799'])
check('No overlap among missing-header and unresolved exclusions', geometry['excluded_intersection'] == [])
check('Geometry total matches catalog', geometry['eligible_after_union_exclusion'] == len(contract['catalog']))
for label, graph in geometry['graphs'].items():
    check('Geometry partition ' + label, sorted(r for group in graph['components'] for r in group) == sorted(r['core'] for r in contract['catalog']))
    check('Geometry count ' + label, sum(graph['component_sizes']) == 1274)
check('Main graph explicitly single component', geometry['graphs']['parent_OR_exact_murcko_including_empty_OR_compound_plate']['component_sizes'] == [1274])
check('Empty-scaffold sensitivity still single', geometry['graphs']['descriptive_sensitivity_parent_OR_nonempty_murcko_OR_plate']['component_sizes'] == [1274])
check('Per-plate feasibility all35', len(geometry['per_plate_holdout_purge']) == 35)
for name, record in depmap['files'].items():
    check('DepMap file hash ' + name, sha(ROOT / depmap['directory'] / name) == record['sha256'])
check('DepMap sample/variant ID joins481', depmap['join']['sample_info_join'] == depmap['join']['mutation_any_record_join'] == 481)
check('DepMap expression join478 not silently481', depmap['join']['expression_id_join'] == 478 and len(depmap['join']['missing_expression_ids']) == 3)
for name, record in follow['gdsc_design'].items():
    if name == 'design_key_overlap':
        continue
    check('GDSC source hash ' + name, sha(ROOT / record['path']) == record['sha256'])
    check('GDSC no outcome conversion ' + name, record['outcome_fields_converted'] is False)
captures = list(OUT.glob('*.http.json'))
check('One external request within maximum4', len(captures) == 1)
for receipt in captures:
    record = json.loads(receipt.read_text())
    body = OUT / (receipt.name.removesuffix('.http.json') + '.body')
    check('HTTP failure body retained', record['status'] == 500 and body.stat().st_size == record['bytes'])
    check('HTTP body hash', sha(body) == record['sha256'])
for path in sorted((ROOT / 'research/update_value_qualification_20261022').glob('data*.py')):
    ast.parse(path.read_text(encoding='utf-8'))
    check('Python syntax ' + path.name, True)
result = {'status': 'PASS', 'checks': len(checks), 'detail': checks, 'utc': datetime.now(timezone.utc).isoformat(),
          'python': sys.executable, 'elapsed_seconds': time.perf_counter() - started,
          'scope': 'Metadata/string-ID/byte-hash verification only; no response numerical conversion or model fitting'}
(OUT / 'VERIFICATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
receipt = {'independent_draft_sha256': independent_sha,
    'independent_saved_before_other_new_drafts_read': True,
    'actual_cross_participants': ['/root/functional_auditor', '/root/mechanism_advocate', '/root/scientific_skeptic', '/root'],
    'actual_questions_and_replies_recorded': True,
    'hashes': {str(p.relative_to(ROOT)): sha(p) for p in
        [OUT / 'CROSS.md', OUT / 'VERIFICATION.json', OUT / 'WORK_AND_FAILURES.md',
         ROOT / 'log/20261022/update_value_qualification/advocate/INDEPENDENT.md',
         ROOT / 'log/20261022/update_value_qualification/skeptic/INDEPENDENT.md',
         OUT / 'FIELD_CONTRACT.json', OUT / 'MANIFEST_GEOMETRY.json', OUT / 'DEPMAP_METADATA_JOIN.json']},
    'phase_code_hashes': {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / 'research/update_value_qualification_20261022').glob('data*.py'))},
    'numerical_response_conversions': 0, 'new_model_fits': 0, 'provider_calls': 0, 'external_GETs': len(captures),
    'decision': 'CONDITIONAL_FIELD_FEASIBILITY_ONLY; NO_NEW_CORE; NO_NUMERICAL_REGISTRATION',
    'remaining': 'Root may independently freeze one scoped ordinary-update source qualification pilot; broad research goal unachieved'}
(OUT / 'CROSS_RECEIPT.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'PASS', 'checks': len(checks), 'elapsed_seconds': result['elapsed_seconds']}))
