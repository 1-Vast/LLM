"""Independent safe-metadata manifest audit, with no raw biological data access."""
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from rdkit import Chem, rdBase
from rdkit.Chem import rdFingerprintGenerator

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/tggates_feedback_headroom'
REVIEW = LOG/'review'
MANIFEST = LOG/'MANIFEST.json'
PROXY = ROOT/'log/20261022/api_evidence_innovation/chemical_proxy/RESULT.json'
MENU = ROOT/'log/20261022/renewal_application/data/TGGATES_THREE_DOSE_IDENTITY.json'
SAFE = ROOT/'log/20261022/tggates_functional_qualification/JOINED_IDENTITY_FLAGS.json'
OLD_FREEZE = ROOT/'log/20261022/tggates_functional_qualification/PRE_OPEN_FREEZE.json'
FIELDS = ('EXP_ID', 'GROUP_ID', 'INDIVIDUAL_ID', 'COMPOUND_NAME', 'SPECIES',
          'SEX_TYPE', 'SACRIFICE_PERIOD', 'DOSE', 'DOSE_UNIT', 'DOSE_LEVEL')
PREFIX = 'tggates-feedback-headroom-v1|'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(row):
    return row['EXP_ID'], row['GROUP_ID'], row['INDIVIDUAL_ID']


def identity(row):
    return {field: row[field] for field in FIELDS}


def graph(rows):
    adjacency = {row['compound_label']: set() for row in rows}
    for pos, left in enumerate(rows):
        for right in rows[pos+1:]:
            if (left['neutral_parent'] == right['neutral_parent']
                    or bool(left['scaffold']) and left['scaffold'] == right['scaffold']):
                adjacency[left['compound_label']].add(right['compound_label'])
                adjacency[right['compound_label']].add(left['compound_label'])
    remaining, groups = set(adjacency), []
    while remaining:
        queue, component = deque([min(remaining)]), set()
        while queue:
            node = queue.popleft()
            if node not in component:
                component.add(node)
                queue.extend(adjacency[node]-component)
        groups.append(sorted(component))
        remaining -= component
    return groups


def main():
    destination = REVIEW/'DATA_MANIFEST_AUDIT.json'
    assert not destination.exists()
    paths = [MANIFEST, LOG/'PROTOCOL_DRAFT.md', REVIEW/'DATA_MANIFEST_AUDIT_PROTOCOL.md',
             PROXY, MENU, SAFE, OLD_FREEZE, Path(__file__)]
    inputs = {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    with (REVIEW/'DATA_MANIFEST_AUDIT_PRE_EXECUTION.json').open('x', encoding='utf-8') as stream:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'sha256': inputs}, stream, indent=2)
        stream.write('\n')
    manifest, proxy, menu, safe = [json.loads(path.read_bytes()) for path in [MANIFEST, PROXY, MENU, SAFE]]
    failures, checks = [], 0

    def check(condition, name):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(name)

    check(len(safe) == len({key(row) for row in safe}), 'safe_unique_keys')
    by_key = {key(row): row for row in safe}
    resolved = [row for row in proxy['rows'] if row['resolution'] == 'NAME_RESOLVED_PROXY_ONLY']
    declared = {row['compound_label']: row for row in menu['results']['both']['accepted_identity_only']}
    independent_groups = graph(resolved)
    blocks = []
    for labels in independent_groups:
        digest = hashlib.sha256((PREFIX+'\n'.join(labels)).encode('utf-8')).hexdigest()
        blocks.append({'block_id': digest, 'labels': labels})
    blocks.sort(key=lambda row: row['block_id'])
    for rank, block in enumerate(blocks):
        block.update(rank=rank, role='source' if rank < 24 else 'development' if rank < 31 else 'later')
    check(len(blocks) == 39, '39_components')
    check(blocks == manifest['blocks'], 'exact_reconstructed_split')
    by_label = {label: block for block in blocks for label in block['labels']}
    check(set(by_label) == {row['compound_label'] for row in resolved}, '45_resolved_labels')
    check(len(by_label) == 45 and len(declared) == 47, '45of47')
    excluded = {row['compound_label'] for row in proxy['rows'] if row['resolution'] != 'NAME_RESOLVED_PROXY_ONLY'}
    check(excluded == {row['compound_label'] for row in manifest['excluded_unresolved']}, 'excluded_unresolved')
    by_compound = {row['compound_label']: row for row in manifest['compounds']}
    check(set(by_compound) == set(by_label), 'manifest_compound_coverage')
    check(len(by_compound) == len(manifest['compounds']), 'manifest_label_unique')
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    treatment_roles, control_roles = {}, {}
    counts = {role: Counter() for role in ('source', 'development', 'later')}
    units = set()
    for source_row in resolved:
        label = source_row['compound_label']
        actual, block, declaration = by_compound[label], by_label[label], declared[label]
        role = block['role']
        check(actual['experiment'] == declaration['experiment'] == source_row['experiment'], label+':experiment')
        check(actual['role'] == role and actual['block_id'] == block['block_id'], label+':roleblock')
        check(actual['neutral_parent_proxy'] == source_row['neutral_parent'], label+':parent')
        expected_bits = list(generator.GetFingerprint(Chem.MolFromSmiles(source_row['neutral_parent'])).GetOnBits())
        check(expected_bits == actual['fingerprint_on_bits'], label+':fingerprint')
        check(set(actual['doses']) == {'Low', 'Middle', 'High'}, label+':threelevels')
        amounts = {}
        counts[role]['compound_labels'] += 1
        for exp, name, amount, unit, level in declaration['dose_keys']:
            expected = [identity(row) for row in safe
                        if row['EXP_ID'] == exp and row['COMPOUND_NAME'] == name
                        and row['SACRIFICE_PERIOD'] == '24 hr' and row['DOSE_UNIT'] == unit
                        and row['DOSE_LEVEL'] == level and Decimal(row['DOSE']) == Decimal(amount)]
            expected.sort(key=key)
            actual_dose = actual['doses'][level]
            check(expected == actual_dose['samples'], label+':'+level+':exact_samples')
            check(Decimal(actual_dose['value']) == Decimal(amount) and actual_dose['unit'] == unit, label+':'+level+':dose')
            check(len(expected) >= 2 and len({key(row) for row in expected}) == len(expected), label+':'+level+':replicates')
            amounts[level] = Decimal(amount)
            units.add(unit)
            counts[role]['treatment_condition_bundles'] += 1
            counts[role]['treatment_sample_records'] += len(expected)
            for row in expected:
                sample_key = key(row)
                check(sample_key not in treatment_roles, label+':'+level+':key_once')
                treatment_roles[sample_key] = role
                safe_row = by_key[sample_key]
                check(safe_row['functional_identity_match'] and safe_row['DNA_nonmissing_unconflicted']
                      and safe_row['LDH_nonmissing_unconflicted'], label+':'+level+':flags')
                check(row['SPECIES'] == 'Human', label+':'+level+':human')
        check(0 < amounts['Low'] < amounts['Middle'] < amounts['High'], label+':positive_order')
        expected_controls = sorted((identity(row) for row in safe
                                    if row['EXP_ID'] == declaration['experiment']
                                    and row['COMPOUND_NAME'] == label and row['SACRIFICE_PERIOD'] == '24 hr'
                                    and row['DOSE_LEVEL'] == 'Control'), key=key)
        check(expected_controls == actual['controls_metadata_only'], label+':exact_controls')
        check(len(expected_controls) >= 2, label+':control_replicates')
        for row in expected_controls:
            sample_key = key(row)
            check(sample_key not in control_roles or control_roles[sample_key] == role, label+':control_role')
            control_roles[sample_key] = role
            check(row['SPECIES'] == 'Human', label+':control_human')
    check(not set(treatment_roles) & set(control_roles), 'treatment_control_disjoint')
    check(sorted(units) == manifest['unit_categories'], 'unit_categories')
    for left_pos, left in enumerate(resolved):
        for right in resolved[left_pos+1:]:
            if (left['neutral_parent'] == right['neutral_parent']
                    or bool(left['scaffold']) and left['scaffold'] == right['scaffold']):
                check(by_label[left['compound_label']]['role'] == by_label[right['compound_label']]['role'], 'no_structure_edge_crossrole')
    role_summaries = {}
    for role, counter in counts.items():
        counter['proxy_blocks'] = sum(block['role'] == role for block in blocks)
        counter['treatment_assay_values'] = 2*counter['treatment_sample_records']
        counter['unique_control_records_metadata_only'] = sum(value == role for value in control_roles.values())
        counter['new_wet_experiments'] = 0
        counter['new_cel_downloads'] = 0
        expected_cost = dict(counter)
        check(expected_cost == manifest['costs'][role], role+':all_cost_fields')
        role_summaries[role] = expected_cost
    check([counts[r]['compound_labels'] for r in ('source','development','later')] == [24,7,14], 'label_counts_24_7_14')
    check([counts[r]['treatment_sample_records'] for r in ('source','development','later')] == [144,42,84], 'sample_counts_144_42_84')
    check(counts['source']['treatment_assay_values']+counts['development']['treatment_assay_values'] == 372, 'source_dev372')
    check(counts['later']['treatment_assay_values'] == 168, 'later168')
    check(manifest['controls_numeric_permission'] is False and manifest['later_numeric_permission'] is False, 'numeric_permissions')
    check(manifest['fingerprint']['rdkit'] == rdBase.rdkitVersion, 'rdkit_version')
    for path in (PROXY, MENU, SAFE):
        check(manifest['inputs_sha256'][path.relative_to(ROOT).as_posix()] == sha(path), 'input_sha:'+path.name)
    old = json.loads(OLD_FREEZE.read_bytes())['sha256']
    raw_relative = 'log/20261022/tggates_functional_qualification/sealed_source/open_tggates_cell_viability.zip'
    check(manifest['raw_zip_relative'] == raw_relative, 'raw_relative')
    check(manifest['inputs_sha256'][raw_relative] == old[raw_relative], 'raw_hash_prior_record_only')
    result = {'status': 'PASS_METADATA_MANIFEST_ONLY' if not failures else 'FAIL',
              'checks': checks, 'failures': failures, 'role_costs': role_summaries,
              'source_development_prelisted_assay_values': 372, 'later_prelisted_assay_values': 168,
              'later_values_accessed_or_cast': 0, 'raw_ZIP_CSV_CEL_opened': False,
              'new_HTTP': 0, 'new_fits': 0, 'input_sha256': inputs,
              'scope': 'Internal identity/split/cost integrity only; no numeric validity, source-material or donor identity established.'}
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'input_sha256'}, ensure_ascii=False))
    return 0 if not failures else 2


if __name__ == '__main__':
    raise SystemExit(main())
