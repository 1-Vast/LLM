"""Exact arithmetic witness for the retained proposal, not a biological test."""
from fractions import Fraction as F
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/feedback_shift_mechanism/root/API_CHECK.json'

if __name__ == '__main__':
    assert not OUT.exists()
    baseline, beta, previous = F(11, 2), F(1, 2), F(1)
    output_a = baseline + beta * (F(10) - previous)
    output_b = baseline + beta * (F(20) - previous)
    beta_one = baseline + F(1) * (F(10) - previous)
    assert output_b - output_a == beta * 10
    assert output_a == 10 and output_b == 15
    assert beta_one == F(29, 2) and beta_one != 10
    OUT.write_text(json.dumps(dict(
        exact_fraction_checks=3, all_pass=True,
        same_lawful_inputs_unseen_current_mean10_output=str(output_a),
        same_lawful_inputs_unseen_current_mean20_output=str(output_b),
        beta1_example_output=str(beta_one), beta_half_example_output=str(output_a),
        interpretation='Literal current-batch correction leaks target information; past-batch interpretation is a distinct lawful ordinary comparator.',
        biological_experiment=False, main_predictor_rerun=False), indent=2), encoding='utf-8')
    print(OUT.read_text(encoding='utf-8'))
