"""Statistical traps: optimistic action selection and correct task units."""
from fractions import Fraction as F
from upper_bound import envelope, score


def test_mean_of_maxima_is_not_maximum_of_means():
    values = {'x': {'a': F(1), 'b': F(0)}, 'y': {'a': F(0), 'b': F(1)}}
    groups = {'x': 'x', 'y': 'y'}
    _, _, upper, _ = envelope(values, groups, ('a', 'b'))
    fixed = max(score({cell: row[a] for cell, row in values.items()}, groups) for a in ('a', 'b'))
    assert upper == 1 and fixed == F(1, 2)


def test_lawful_fallback_can_change_the_opportunity_decision():
    values = {'x': {'repair': F(1), 'B1': F(1, 2)},
              'y': {'repair': F(0), 'B1': F(1, 2)}}
    groups = {'x': 'x', 'y': 'y'}
    assert envelope(values, groups, ('repair',))[2] == F(1, 2)
    assert envelope(values, groups, ('repair', 'B1'))[2] == F(3, 4)


def test_duplicate_stocks_are_one_lineage_with_optimistic_stock_selection():
    values = {'x1': {'a': F(1), 'b': F(0)}, 'x2': {'a': F(0), 'b': F(1)},
              'y': {'a': F(0), 'b': F(0)}}
    groups = {'x1': 'x', 'x2': 'x', 'y': 'y'}
    _, _, upper, common_action = envelope(values, groups, ('a', 'b'))
    assert upper == F(1, 2) and common_action == F(1, 4)
    assert score({'x1': F(1), 'x2': F(1), 'y': F(0)}, groups) == F(1, 2)
