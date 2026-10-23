"""Descriptive diagnostics after the frozen pilot; cannot revise its gates."""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/almanac_feedback_pilot/root'


def main():
    assert not (OUT / 'DESCRIPTIVE_DIAGNOSTICS.json').exists()
    result = json.loads((OUT / 'RESULTS.json').read_text())
    metrics = result['development_metrics']
    compact = {name: {k: m[k] for k in ('mse', 'mae', 'mean_top10pct_regret')} for name, m in metrics.items()}
    values = np.load(OUT / 'VALUES.npz')
    pred = np.load(OUT / 'PREDICTIONS.npz')
    truth = values['y'][30:40, :, :8]
    pair_gain = np.mean((pred['B0-selected'] - truth) ** 2 - (pred['B1-selected'] - truth) ** 2, axis=(0, 2))
    gain = np.array(result['cell_gains'])
    info = {'scope': 'post-result descriptive only; no reselection or gate changes',
            'compact_metrics': compact,
            'relative_selected_mse_reduction': result['selected_gain'] / metrics['B0-selected']['mse'],
            'cells_improved': int(np.sum(gain > 0)),
            'minimum_delete_one_cell_gain': float(np.min((gain.sum() - gain) / 9)),
            'dose_gains': (np.array(metrics['B0-selected']['dose_mse']) - metrics['B1-selected']['dose_mse']).tolist(),
            'pairs_improved': int(np.sum(pair_gain > 0)), 'pair_count': len(pair_gain),
            'largest_pair_net_gain_fraction': float(pair_gain.max() / pair_gain.sum()),
            'smallest_delete_one_pair_gain': float(np.min((pair_gain.sum() - pair_gain) / (len(pair_gain) - 1))),
            'best_development_candidate_B0_oracle_only': min((n for n in metrics if n.startswith('B0:')), key=lambda n: metrics[n]['mse']),
            'best_development_candidate_B1_oracle_only': min((n for n in metrics if n.startswith('B1:')), key=lambda n: metrics[n]['mse']),
            'selection_regret_improved_cells': int(np.sum(np.array(metrics['B0-selected']['cell_top10pct_regret']) > metrics['B1-selected']['cell_top10pct_regret']))}
    (OUT / 'DESCRIPTIVE_DIAGNOSTICS.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    print(json.dumps(info, indent=2))


if __name__ == '__main__':
    main()
