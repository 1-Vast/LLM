"""Extract the prespecified contrasts after the sealed separate scorer."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cipa_control_information'

if __name__ == '__main__':
    scores = json.loads((OUT / 'TERMINAL_SCORES.json').read_text())
    fits = json.loads((OUT / 'FIT_COUNTS.json').read_text())
    result = {
        'gate': scores['information_gate'],
        'best_ordinary': scores['best_prespecified_ordinary_comparator'],
        'mean_site': scores['equal_physical_site'],
        'pooled': scores['pooled_equal_bundles'],
        'primary_comparisons': {k: scores['comparisons']['fixed:conditional'][k]
                                for k in scores['information_gate_by_reference']},
        'gates': scores['information_gate_by_reference'],
        'budget': {k: v for k, v in fits.items() if k not in (
            'ordinary_fits', 'conditional_fits', 'summary_constructions', 'conditional_preprocessing')},
        'summary_count': len(fits['summary_constructions']),
        'preprocessing_count': len(fits['conditional_preprocessing']),
    }
    with (OUT / 'RESULT_SUMMARY.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))
