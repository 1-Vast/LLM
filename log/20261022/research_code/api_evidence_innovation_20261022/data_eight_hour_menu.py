"""Expand only the outcome-blind TG-GATEs early-time menu census."""
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'log/20261022/tggates_functional_qualification/JOINED_IDENTITY_FLAGS.json'
LOG = ROOT/'log/20261022/api_evidence_innovation/data'
FIELDS = {'EXP_ID', 'GROUP_ID', 'INDIVIDUAL_ID', 'COMPOUND_NAME', 'SPECIES',
          'SEX_TYPE', 'SACRIFICE_PERIOD', 'DOSE', 'DOSE_UNIT', 'DOSE_LEVEL',
          'BARCODE', 'functional_source_rows', 'functional_identity_match',
          'CEL_identity_and_barcode_match', 'DNA_nonmissing_unconflicted',
          'LDH_nonmissing_unconflicted'}
FLAGS = ('functional_identity_match', 'CEL_identity_and_barcode_match',
         'DNA_nonmissing_unconflicted', 'LDH_nonmissing_unconflicted')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = LOG/'TGGATES_EIGHT_HOUR_MENU.json'
    assert not out.exists()
    frozen = {'protocol_sha256': sha(LOG/'TGGATES_EIGHT_HOUR_MENU_PROTOCOL.md'),
              'script_sha256': sha(Path(__file__)), 'source_sha256': sha(SOURCE)}
    with (LOG/'TGGATES_EIGHT_HOUR_MENU_PRE_EXECUTION.json').open('x', encoding='utf-8') as stream:
        json.dump(frozen, stream, indent=2)
        stream.write('\n')
    rows = json.loads(SOURCE.read_bytes())
    assert all(set(row) == FIELDS for row in rows)
    assert all(type(row[key]) is bool for row in rows for key in FLAGS)
    controls, conditions = defaultdict(list), defaultdict(list)
    for row in rows:
        if row['DOSE_LEVEL'] == 'Control':
            controls[row['EXP_ID'], row['SACRIFICE_PERIOD']].append(row)
        else:
            key = (row['EXP_ID'], row['COMPOUND_NAME'],
                   str(Decimal(row['DOSE']).normalize()), row['DOSE_UNIT'], row['DOSE_LEVEL'])
            conditions[key].append(row)
    results = {}
    for early_time in ('2 hr', '8 hr'):
        for endpoint, assays in (('LDH', ('LDH',)), ('both', ('DNA', 'LDH'))):
            def functional(row):
                return all(row[name+'_nonmissing_unconflicted'] for name in assays)
            eligible = []
            for key, members in conditions.items():
                early = [r for r in members if r['SACRIFICE_PERIOD'] == early_time]
                late = [r for r in members if r['SACRIFICE_PERIOD'] == '24 hr']
                if (len(early) >= 2 and len(late) >= 2
                        and all(r['CEL_identity_and_barcode_match'] for r in early)
                        and all(functional(r) for r in late)
                        and sum(r['CEL_identity_and_barcode_match'] for r in controls[key[0], early_time]) >= 2
                        and sum(functional(r) for r in controls[key[0], '24 hr']) >= 2):
                    eligible.append(key)
            by_drug = defaultdict(list)
            for key in eligible:
                by_drug[key[:2]].append(key)
            accepted, excluded = [], []
            for drug, keys in sorted(by_drug.items()):
                reasons = []
                if len(keys) != 3 or {k[4] for k in keys} != {'Low', 'Middle', 'High'}:
                    reasons.append('not_three_low_middle_high')
                units = {k[3] for k in keys}
                if len(units) != 1 or not units <= {'μM', 'μg/mL', 'ng/mL'}:
                    reasons.append('unit_unresolved_or_inconsistent')
                doses = [Decimal(k[2]) for k in keys]
                if len(set(doses)) != 3 or any(d <= 0 for d in doses):
                    reasons.append('not_three_distinct_positive_doses')
                ordered = sorted(keys, key=lambda k: Decimal(k[2]))
                if [k[4] for k in ordered] != ['Low', 'Middle', 'High']:
                    reasons.append('numeric_level_order_mismatch')
                record = {'experiment': drug[0], 'compound_label': drug[1], 'dose_keys': ordered}
                (excluded if reasons else accepted).append(dict(record, reasons=reasons) if reasons else record)
            results[early_time+'_'+endpoint] = {
                'eligible_condition_count': len(eligible), 'eligible_label_count': len(by_drug),
                'complete_three_positive_dose_labels': len(accepted),
                'accepted_identity_only': accepted, 'excluded_identity_only': excluded,
            }
    assert results['2 hr_LDH']['complete_three_positive_dose_labels'] == 51
    assert results['2 hr_both']['complete_three_positive_dose_labels'] == 47
    gate = results['8 hr_both']['complete_three_positive_dose_labels'] >= 60
    result = {'basis': 'Previously whitelisted identities/availability flags only',
              'frozen_inputs': frozen, 'source_rows': len(rows), 'results': results,
              'sixty_label_asset_triage_gate': 'PASS' if gate else 'FAIL',
              'limits': ['No response values/CEL/RNA/reserve opened',
                         'Labels are not independent biological tasks or resolved chemical groups',
                         'No numerical validity/performance/power/RSI claim',
                         'Prescreen dose, assay normalization and unknown lot mapping retained']}
    with out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: {k: v for k, v in value.items() if 'identity_only' not in k}
                      for key, value in results.items()}, ensure_ascii=False))
    print(json.dumps({'asset_triage_gate': result['sixty_label_asset_triage_gate'],
                      'result_sha256': sha(out)}))


if __name__ == '__main__':
    main()
