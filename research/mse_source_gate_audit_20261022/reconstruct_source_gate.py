"""Independent DOM/Fraction reconstruction; only the frozen source scalars are authorized."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys
from xml.dom import minidom
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/mse_source_gate'
OUT = ROOT / 'log/20261022/mse_source_gate_audit/postrun'
SRC = ROOT / 'log/20261022/biological_decision_scout/sources'
EXPECTED_FREEZE = '3d2fa71920482128905986d5dce9a5adb39675840274ef87a3e40348d1ca1058'
MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
OFFREL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
RAW10 = ['Lymphocyte_act', 'Lymphocyte_conv', 'Macrophage_round', 'Macrophage_stretched',
         'Malignant_adherent', 'Malignant_colony', 'Malignant_single', 'Malignant_spheroid',
         'Other', 'Unassigned']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(name, payload):
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)


def children(node, name):
    return [c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE and c.localName == name]


def node_text(node):
    return ''.join(c.data if c.nodeType in (c.TEXT_NODE, c.CDATA_SECTION_NODE) else node_text(c)
                   for c in node.childNodes)


def keyed_string(cell, shared):
    kind = cell.getAttribute('t')
    if kind == 's':
        return shared[int(node_text(children(cell, 'v')[0]))]
    assert kind == 'inlineStr', 'Non-string metadata key/header'
    return node_text(children(cell, 'is')[0])


def parse_authorized(book, sheet_name, source_ids, fields):
    """Resolve metadata then access v text only for authorized sample AND named field.

    Full requested-sheet DOM buffers contain denied XML; scalar text of denied cells
    is never retrieved. This does not import or call root's streaming ET reader.
    """
    result, ledger, skipped = {}, [], []
    with zipfile.ZipFile(book) as archive:
        shared_dom = minidom.parseString(archive.read('xl/sharedStrings.xml'))
        shared = [node_text(si) for si in shared_dom.getElementsByTagNameNS(MAIN, 'si')]
        workbook = minidom.parseString(archive.read('xl/workbook.xml'))
        sheet = [s for s in workbook.getElementsByTagNameNS(MAIN, 'sheet')
                 if s.getAttribute('name') == sheet_name]
        assert len(sheet) == 1
        relation_id = sheet[0].getAttributeNS(OFFREL, 'id')
        relationships = minidom.parseString(archive.read('xl/_rels/workbook.xml.rels'))
        relation = [r for r in relationships.getElementsByTagName('Relationship')
                    if r.getAttribute('Id') == relation_id]
        assert len(relation) == 1
        member = relation[0].getAttribute('Target').lstrip('/')
        if not member.startswith('xl/'):
            member = 'xl/' + member
        document = minidom.parseString(archive.read(member))
        rows = document.getElementsByTagNameNS(MAIN, 'row')
        header = {re.match(r'[A-Z]+', c.getAttribute('r'))[0]: keyed_string(c, shared)
                  for c in children(rows[0], 'c')}
        assert header['A'] == 'SampleID' and len(set(header.values())) == len(header)
        columns = {name: [col for col in header if header[col] == name][0] for name in fields}
        for row in rows[1:]:
            cells = {re.match(r'[A-Z]+', c.getAttribute('r'))[0]: c for c in children(row, 'c')}
            sample = keyed_string(cells['A'], shared)
            if sample not in source_ids:
                skipped.append(sample)
                continue
            assert sample not in result, 'Duplicate authorized sample'
            result[sample] = {}
            for field in fields:
                col = columns[field]
                cell = cells.get(col)
                record = dict(sample=sample, sheet=sheet_name, field=field,
                              coordinate=col + row.getAttribute('r'), status='missing', value=None)
                if cell is not None:
                    if children(cell, 'f'):
                        record['status'] = 'formula_disallowed'
                    elif cell.getAttribute('t') not in ('', 'n'):
                        record['status'] = 'nonnumeric'
                    elif children(cell, 'v'):
                        token = node_text(children(cell, 'v')[0])
                        record['numeric_token'] = token
                        try:
                            number = Decimal(token)
                            record['status'] = 'finite' if number.is_finite() else 'nonfinite'
                            if number.is_finite():
                                record['value'] = str(number)
                                result[sample][field] = Fraction(token)
                        except (InvalidOperation, ValueError):
                            record['status'] = 'invalid_numeric_token'
                ledger.append(record)
        assert set(result) == source_ids
    return result, ledger, skipped, member


def hash_order(namespace, items):
    return sorted(items, key=lambda item: (hashlib.sha256((namespace + '\n' + item).encode()).hexdigest(), item))


def reconstruct():
    assert digest(PHASE / 'FREEZE.json') == EXPECTED_FREEZE
    freeze = load(PHASE / 'FREEZE.json')
    hash_checks = {name: {'expected': expected, 'actual': digest(ROOT / name)}
                   for name, expected in freeze['files'].items()}
    assert all(v['expected'] == v['actual'] for v in hash_checks.values())
    inventory_path = ROOT / 'log/20261022/contrast_gate_check/FINAL_FILE_INVENTORY.json'
    prior = load(inventory_path)['files']
    assert all(digest(ROOT / r['path']) == r['sha256'] for r in prior)
    manifest = load(PHASE / 'PATIENT_MENU_MANIFEST.json')
    assert all(digest(ROOT / name) == expected for name, expected in manifest['input_hashes'].items())
    # Rebuild the eligibility/whole-patient mask from metadata, not the result.
    keys = load(SRC / 'MSE_KEY_AUDIT.json')
    identities = {r['sample']: r['patient'] for r in keys['clinical_identity']}
    designs = {r['sample']: r['plate'] for r in keys['experiment_identity']}
    eligible = sorted(r['sample'] for r in keys['response_masks']['RCN raw']['rows']
                      if re.match(r'^[2-7]STP', designs[r['sample']]))
    ordered_patients = hash_order(manifest['split_namespace'], {identities[s] for s in eligible})
    partitions = {p: 'source' if i < 55 else 'development' if i < 75 else 'later'
                  for i, p in enumerate(ordered_patients)}
    rows = [dict(sample=s, patient=identities[s], partition=partitions[identities[s]], design=designs[s])
            for s in eligible]
    assert rows == manifest['rows']
    source = {r['sample']: r['patient'] for r in rows if r['partition'] == 'source'}
    assert len(source) == 75 and len(set(source.values())) == 55
    drugs = load(ROOT / 'log/20261022/contrast_independent_review/MSE_COMMON65_UNIT_QUALIFICATION.json')['whitelist']
    assert drugs == manifest['drugs'] and len(drugs) == 65
    probes = hash_order(manifest['fixed_probe_namespace'], drugs)[:8]
    terminals = sorted(set(drugs).difference(probes))
    assert probes == manifest['probes'] and terminals == manifest['terminal_drugs'] and len(terminals) == 57
    scalar_data, ledger, skipped, xml_members = {}, [], {}, {}
    for sheet_name, workbook_id, fields in [('RCN raw', 8, drugs), ('RCF raw', 8, drugs),
                                            ('Cell_type_abundance_raw', 6, RAW10)]:
        book = SRC / f'complete_members/41467_2024_52694_MOESM{workbook_id}_ESM.xlsx'
        data, records, omitted, member = parse_authorized(book, sheet_name, set(source), fields)
        scalar_data[sheet_name] = data
        ledger.extend(records)
        skipped[sheet_name] = omitted
        xml_members[sheet_name] = member
    assert len(ledger) == 10500 and Counter(r['sheet'] for r in ledger) == Counter(
        {'RCN raw': 4875, 'RCF raw': 4875, 'Cell_type_abundance_raw': 750})
    upper, lower = Fraction(10000000001, 10000000000), Fraction(-1, 10000000000)
    violations = []
    for record in ledger:
        if record['status'] != 'finite':
            violations.append(record)
            continue
        number = Fraction(record['numeric_token'])
        if number > upper or (record['sheet'] == 'Cell_type_abundance_raw' and number < lower):
            violations.append(record)
    # Only source values have been retrieved. Compare the independently extracted ledger.
    published_access = load(PHASE / 'SOURCE_VALUE_ACCESS.json')
    assert ledger == published_access['records'], 'Independent coordinate/token/status ledger differs'
    assert skipped == published_access['skipped_sample_ids'], 'Skipped metadata IDs differ'
    groups = defaultdict(list)
    for sample, patient in source.items():
        groups[patient].append(sample)
    hit = {sample: {drug: int(scalar_data['RCN raw'][sample][drug] >= Fraction(1, 2)
                             and scalar_data['RCF raw'][sample][drug] >= Fraction(1, 5))
                    for drug in terminals} for sample in source}
    hit_counts = {s: sum(hit[s].values()) for s in source}
    patient_rows, training_rows = [], []
    for heldout in sorted(groups):
        training = [p for p in sorted(groups) if p != heldout]
        assert len(training) == 54 and not set(groups[heldout]).intersection(
            s for p in training for s in groups[p])
        rates = {}
        for drug in terminals:
            within = [Fraction(sum(hit[s][drug] for s in groups[p]), len(groups[p])) for p in training]
            rates[drug] = sum(within, Fraction(0)) / 54
        chosen = sorted(terminals, key=lambda d: (-rates[d], d))[:5]
        base_samples = [Fraction(sum(hit[s][d] for d in chosen), 5) for s in groups[heldout]]
        oracle_samples = [Fraction(min(hit_counts[s], 5), 5) for s in groups[heldout]]
        baseline = sum(base_samples, Fraction(0)) / len(base_samples)
        oracle = sum(oracle_samples, Fraction(0)) / len(oracle_samples)
        mixed = any(0 < hit_counts[s] < 57 for s in groups[heldout])
        patient_rows.append(dict(patient=heldout, baseline=float(baseline), oracle=float(oracle),
                                 gap=float(oracle-baseline), baseline_exact=str(baseline),
                                 oracle_exact=str(oracle), gap_exact=str(oracle-baseline),
                                 mixed_hit_sample=mixed, selected=chosen))
        training_rows.append(dict(held_out_patient=heldout, held_out_samples=groups[heldout],
                                  training_patients=training,
                                  training_samples=[s for p in training for s in groups[p]],
                                  terminal_rates_exact={d: str(rates[d]) for d in terminals}))
    means = {key: sum((Fraction(r[key + '_exact']) for r in patient_rows), Fraction(0)) / 55
             for key in ['baseline', 'oracle', 'gap']}
    mixed_count = sum(r['mixed_hit_sample'] for r in patient_rows)
    checks = dict(all_required_values_finite_and_in_contract=not violations,
                  descriptive_oracle_gap_at_least_0_10=means['gap'] >= Fraction(1, 10),
                  at_least_10_mixed_hit_patient_groups=mixed_count >= 10)
    summaries = {}
    for sheet, data in scalar_data.items():
        values = [Decimal(r['value']) for r in ledger if r['sheet'] == sheet and r['status'] == 'finite']
        summaries[sheet] = dict(min_exact_decimal=str(min(values)), max_exact_decimal=str(max(values)),
                               negative=sum(v < 0 for v in values))
    # Root result is used only for comparison after independent parsing and arithmetic.
    root_result = load(PHASE / 'RESULT.json')
    assert root_result['freeze_sha256'] == EXPECTED_FREEZE
    assert patient_rows == root_result['opportunity']['patients'], 'LOPO patient choices/utilities differ'
    for key, exact in means.items():
        assert str(exact) == root_result['opportunity'][key + '_exact']
        assert float(exact) == root_result['opportunity'][key]
    assert mixed_count == root_result['opportunity']['mixed_hit_patients']
    assert hit_counts == root_result['source_hit_counts_per_sample']
    assert summaries == root_result['response_summaries']
    assert not violations and root_result['violations'] == []
    assert root_result['checks'] == {
        'all_required_values_finite_and_in_contract': checks['all_required_values_finite_and_in_contract'],
        'descriptive_oracle_gap_at_least_0.10': checks['descriptive_oracle_gap_at_least_0_10'],
        'at_least_10_mixed_hit_patient_groups': checks['at_least_10_mixed_hit_patient_groups']}
    assert root_result['passed'] == all(checks.values())
    assert root_result['decision'] == 'STOP_EXACT_CONFIGURATION' and not all(checks.values())
    assert root_result['source_samples'] == 75 and root_result['source_patients'] == 55
    assert root_result['source_required_field_attempts'] == 10500
    assert root_result['numeric_access_attempts'] == dict(Counter(r['sheet'] for r in ledger))
    assert root_result['opportunity']['leave_one_patient_out_label_aggregations'] == 55
    assert root_result['predictive_model_fits'] == root_result['provider_calls'] == 0
    assert root_result['nonsource_scalar_accesses'] == root_result['scaled_sheet_accesses'] == 0
    save('INDEPENDENT_SOURCE_LEDGER.json', dict(records=ledger, skipped_sample_ids=skipped,
                                             authorized_xml_members=xml_members))
    save('INDEPENDENT_LOPO_DETAILS.json', dict(patients=patient_rows, training=training_rows,
                                             source_patient_sample_mask=dict(groups),
                                             source_terminal_hits=hit))
    audit = dict(status='PASS_INDEPENDENT_RECONSTRUCTION_OF_STOP', passed=True,
                 audit_agreement_passed=True, biological_task_gate_passed=False,
                 utc=datetime.now(timezone.utc).isoformat(),
                 code_sha256=digest(Path(__file__)), freeze_sha256=EXPECTED_FREEZE,
                 freeze_file_checks=hash_checks, freeze_bound_files_verified=len(hash_checks),
                 prior_inventory_files_verified=len(prior), prior_inventory_unchanged=True,
                 source_samples=75, source_patients=55, common_actions=65, fixed_probes=probes,
                 terminal_actions=57, raw_composition_fields=RAW10,
                 field_attempts=len(ledger), field_attempts_by_sheet=dict(Counter(r['sheet'] for r in ledger)),
                 decoded_finite_source_tokens=sum(r['status'] == 'finite' for r in ledger),
                 violations=violations, source_patient_sample_mask=dict(groups),
                 skipped_sample_ids=skipped, skipped_counts={k: len(v) for k, v in skipped.items()},
                 source_hit_counts_per_sample=hit_counts, patient_results=patient_rows,
                 exact_means={key: str(value) for key, value in means.items()},
                 display_means={key: float(value) for key, value in means.items()},
                 mixed_hit_patients=mixed_count, label_aggregations=55, checks=checks,
                 gate_passed=all(checks.values()), decision='STOP_EXACT_CONFIGURATION',
                 response_summaries=summaries, full_token_coordinate_status_ledger_matches=True,
                 full_patient_lopo_choices_and_utilities_match=True, root_result_matches=True,
                 nonsource_scalar_accesses=0, scaled_sheet_scalar_accesses=0, nonmenu_scalar_accesses=0,
                 early_stp_scalar_accesses=0, predictive_solver_fits=0, provider_calls=0,
                 parser='Independent xml.dom.minidom OOXML parser; no import of root gate.py',
                 physical_buffer_disclosure='Requested-sheet DOM contains denied bytes; denied scalar text is not retrieved.',
                 limitations='Released derived cohort-sensor outcomes; no raw denominators or retained-well precision; descriptive gate only.',
                 output_hashes={name: digest(OUT / name) for name in ['INDEPENDENT_SOURCE_LEDGER.json', 'INDEPENDENT_LOPO_DETAILS.json']},
                 compared_root_hashes={name: digest(PHASE / name) for name in ['RESULT.json', 'SOURCE_VALUE_ACCESS.json', 'RUN_TRANSCRIPT.txt']})
    save('FINAL_NUMERICAL_AUDIT.json', audit)
    print(json.dumps({k: audit[k] for k in ['status', 'field_attempts', 'source_samples', 'source_patients',
                                           'exact_means', 'mixed_hit_patients', 'checks', 'decision',
                                           'freeze_bound_files_verified', 'prior_inventory_files_verified']}))


if __name__ == '__main__':
    assert sys.argv[1:] == ['authorized-source-audit']
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        reconstruct()
    except Exception as error:
        failures = list(OUT.glob('FAILED_ATTEMPT_*.json'))
        save(f'FAILED_ATTEMPT_{len(failures)+1:02d}.json',
             dict(utc=datetime.now(timezone.utc).isoformat(), error_type=type(error).__name__,
                  message=str(error), code_sha256=digest(Path(__file__))))
        raise
