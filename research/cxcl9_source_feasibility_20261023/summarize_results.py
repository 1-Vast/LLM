"""Describe saved metrics; does not fit or select another model."""
import json
from source import OUT

if __name__ == '__main__':
    result = json.loads((OUT/'PREDICTION_RESULTS.json').read_text(encoding='utf-8'))
    summary = []
    for variant, cells in result['variants'].items():
        for cell, row in cells.items():
            models = row['models']
            summary.append({'variant': variant, 'cell': cell, 'selected': row['selected_adaptive'],
                'source_copy_mse': models['source_copy']['mse'],
                'four_control_affine_mse': models['control_affine']['mse'],
                'control_affine_relative_gain': 1-models['control_affine']['mse']/models['source_copy']['mse'],
                'nine_feedback_selected_mse': models[row['selected_adaptive']]['mse'],
                'nine_feedback_selected_regret': models[row['selected_adaptive']]['mean_menu_regret'],
                'control_affine_regret': models['control_affine']['mean_menu_regret'],
                'duplicate_dispersion': row['target_duplicate_dispersion']})
    target = OUT/'SAVED_METRIC_SUMMARY.json'
    assert not target.exists()
    target.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
