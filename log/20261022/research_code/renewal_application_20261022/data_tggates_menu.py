"""Outcome-blind audit of the skeptic's fixed three-dose 2h->24h menu."""
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'log/20261022/tggates_functional_qualification/JOINED_IDENTITY_FLAGS.json'
OUT = ROOT / 'log/20261022/renewal_application/data/TGGATES_THREE_DOSE_IDENTITY.json'
FIELDS = {'EXP_ID', 'GROUP_ID', 'INDIVIDUAL_ID', 'COMPOUND_NAME', 'SPECIES',
          'SEX_TYPE', 'SACRIFICE_PERIOD', 'DOSE', 'DOSE_UNIT', 'DOSE_LEVEL',
          'BARCODE', 'functional_source_rows', 'functional_identity_match',
          'CEL_identity_and_barcode_match', 'DNA_nonmissing_unconflicted',
          'LDH_nonmissing_unconflicted'}


def main():
    assert not OUT.exists(), 'Refuse to overwrite'
    payload = SOURCE.read_bytes()
    rows = json.loads(payload)
    assert all(set(row) == FIELDS for row in rows)
    assert all(type(row[key]) is bool for row in rows for key in
               ('functional_identity_match', 'CEL_identity_and_barcode_match',
                'DNA_nonmissing_unconflicted', 'LDH_nonmissing_unconflicted'))
    menus, controls = defaultdict(list), defaultdict(list)
    for row in rows:
        if row['DOSE_LEVEL'] == 'Control':
            controls[(row['EXP_ID'], row['SACRIFICE_PERIOD'])].append(row)
        else:
            key = (row['EXP_ID'], row['COMPOUND_NAME'],
                   str(Decimal(row['DOSE']).normalize()), row['DOSE_UNIT'], row['DOSE_LEVEL'])
            menus[key].append(row)
    results = {}
    for endpoint in ('LDH', 'both'):
        names = ('DNA', 'LDH') if endpoint == 'both' else ('LDH',)
        def functional(row):
            return all(row[name + '_nonmissing_unconflicted'] for name in names)
        eligible = []
        for key, members in menus.items():
            early = [r for r in members if r['SACRIFICE_PERIOD'] == '2 hr']
            late = [r for r in members if r['SACRIFICE_PERIOD'] == '24 hr']
            early_controls = controls[(key[0], '2 hr')]
            late_controls = controls[(key[0], '24 hr')]
            if (len(early) >= 2 and len(late) >= 2
                    and all(r['CEL_identity_and_barcode_match'] for r in early)
                    and all(functional(r) for r in late)
                    and sum(r['CEL_identity_and_barcode_match'] for r in early_controls) >= 2
                    and sum(functional(r) for r in late_controls) >= 2):
                eligible.append(key)
        by_drug = defaultdict(list)
        for key in eligible:
            by_drug[key[:2]].append(key)
        accepted, excluded = [], []
        for drug, dose_keys in sorted(by_drug.items()):
            reasons = []
            if len(dose_keys) != 3 or {k[4] for k in dose_keys} != {'Low', 'Middle', 'High'}:
                reasons.append('not_exactly_three_low_middle_high_conditions')
            units = {key[3] for key in dose_keys}
            if len(units) != 1 or not units <= {'μM', 'μg/mL', 'ng/mL'}:
                reasons.append('unit_unresolved_or_inconsistent')
            values = [Decimal(key[2]) for key in dose_keys]
            if any(value <= 0 for value in values) or len(set(values)) != 3:
                reasons.append('not_three_distinct_strictly_positive_released_doses')
            ordered = sorted(dose_keys, key=lambda key: Decimal(key[2]))
            if [key[4] for key in ordered] != ['Low', 'Middle', 'High']:
                reasons.append('dose_level_order_differs_from_numeric_order')
            record = {'experiment': drug[0], 'compound_label': drug[1],
                      'dose_keys': [list(key) for key in ordered]}
            if reasons:
                excluded.append(dict(record, reasons=reasons))
            else:
                accepted.append(record)
        expected = 156 if endpoint == 'LDH' else 144
        assert len(eligible) == expected, (endpoint, len(eligible), expected)
        results[endpoint] = {'available_conditions': len(eligible),
                             'available_compound_labels': len(by_drug),
                             'three_declared_positive_dose_compounds': len(accepted),
                             'accepted_identity_only': accepted,
                             'excluded_identity_only': excluded}
    record = {'basis': 'Previously whitelisted identities and booleans only; no raw reopening or outcomes',
              'source': str(SOURCE.relative_to(ROOT)),
              'source_sha256': hashlib.sha256(payload).hexdigest(),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'early_time': '2 hr', 'late_time': '24 hr', 'results': results,
              'limits': ['Declared positive concentration is not measurement accuracy certification',
                         'Chemical structure, alias grouping and non-small-molecule eligibility remain unresolved',
                         'No physical culture/donor identity or numerical response validity inferred',
                         'These compound labels are not independent task counts',
                         'No response values, CEL files, models or protected reserve accessed']}
    OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: {name: value for name, value in result.items()
                           if name not in ('accepted_identity_only', 'excluded_identity_only')}
                      for key, result in results.items()}, indent=2))
    print(json.dumps({key: result['excluded_identity_only'] for key, result in results.items()},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
