"""Post-result, full-development descriptive diagnostics; frozen gate unchanged."""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/decrypte_feedback_pilot'


def main():
    data = json.loads((OUT / 'DEVELOPMENT_VALUES.json').read_text(encoding='utf-8'))
    pred = json.loads((OUT / 'PREDICTIONS.json').read_text(encoding='utf-8'))
    y = np.array(data['y'])
    base_loss = np.mean((np.array(pred['selected_predictions']['0']) - y[:, [1, 2, 3]]) ** 2, axis=1)
    gain = base_loss - np.mean((np.array(pred['selected_predictions']['1']) - y[:, [1, 2, 3]]) ** 2, axis=1)
    order = np.argsort(-np.mean((y-1) ** 2, axis=1), kind='stable')
    cumulative = [{'rank': k, 'drug': data['drugs'][i],
                   'cumulative_B0_error_fraction': float(base_loss[order[:k]].sum()/base_loss.sum()),
                   'cumulative_B1_gain_fraction': float(gain[order[:k]].sum()/gain.sum())} for k, i in enumerate(order, 1)]
    rounding = {}
    for assay in ('Metabolic activity', 'Confluency', 'Cytotoxicity'):
        details = []
        precision = Counter()
        for row in data['records']:
            if row['assay'] != assay:
                continue
            relative = [Decimal(row['cells'][c]['payload']) for c in 'KLMNO']
            raw = [Decimal(row['cells'][c]['payload']) for c in 'PQRST']
            precision.update(max(0, -v.as_tuple().exponent) for v in relative)
            if min(relative) <= Decimal('0.0005') or min(raw) <= 0:
                details.append({'drug': row['drug'], 'eligible': False})
                continue
            lower = max(a/(b+Decimal('0.0005')) for a, b in zip(raw, relative))
            upper = min(a/(b-Decimal('0.0005')) for a, b in zip(raw, relative))
            details.append({'drug': row['drug'], 'eligible': True, 'compatible': lower <= upper,
                            'denominator_lower': str(lower), 'denominator_upper': str(upper)})
        rounding[assay] = {'relative_stored_decimal_length_counts': dict(precision),
                           'eligible': sum(d['eligible'] for d in details),
                           'compatible': sum(d.get('compatible', False) for d in details), 'details': details}
    result = {'post_result_diagnostic': True, 'gate_changed': False, 'cumulative_response_rank_diagnostics': cumulative,
              'hypothetical_rounding_compatibility': rounding}
    (OUT / 'DESCRIPTIVE_DIAGNOSTICS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'top_response_rank_prefixes': [cumulative[i] for i in (0, 2, 4, 9)],
                      'rounding': {k: {a: b for a, b in v.items() if a != 'details'} for k, v in rounding.items()}}, indent=2))


if __name__ == '__main__':
    main()
