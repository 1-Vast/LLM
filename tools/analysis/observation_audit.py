"""Offline coordinate and cell-sampling arithmetic, without source certification.

Extracted from the separately verified P0.5R extension matching routines and
the observation-reliability projection diagnostic. Frozen research is unchanged.
Inputs must already share rows, transformations and declared gene coordinates.
This module never infers biological replication or a model's output axis.
"""
import argparse
import json
from pathlib import Path

import numpy as np


def _matrix(values, columns, minimum_rows=1):
    values = np.asarray(values, dtype=float)
    if (values.ndim != 2 or values.shape[1] != columns
            or len(values) < minimum_rows or not np.isfinite(values).all()):
        raise ValueError("finite row-aligned matrix with the declared columns required")
    return values


def _identities(values):
    values = list(values)
    if (not values or any(not isinstance(v, str) or not v.strip() for v in values)
            or len(set(values)) != len(values)):
        raise ValueError("nonempty unique string identities required")
    return values


def numerical_axis_matches(names, raw, targets, symbols, *, consistency=None,
                           tolerance=1e-5):
    """Compare each declared coordinate with every candidate source column.

    Passing requires a unique expected identity and at least two informative
    discovery rows. Optional consistency requires one informative row and the
    same tolerance; it is never labelled an independent validation set.
    Caller supplies transformed expressions: no normalization is inferred.
    """
    names, symbols = _identities(names), _identities(symbols)
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("finite positive tolerance required")
    lookup = {name: index for index, name in enumerate(names)}
    if any(symbol not in lookup for symbol in symbols):
        raise ValueError("every declared symbol must have a source identity")
    raw, targets = _matrix(raw, len(names)), _matrix(targets, len(symbols))
    if len(raw) != len(targets):
        raise ValueError("source and coordinate rows must align")
    if consistency is not None:
        held_raw = _matrix(consistency[0], len(names))
        held_target = _matrix(consistency[1], len(symbols))
        if len(held_raw) != len(held_target):
            raise ValueError("consistency source and coordinate rows must align")
    records = []
    for column, symbol in enumerate(symbols):
        candidates = np.arange(len(names))
        for row in np.argsort(-np.abs(targets[:, column])):
            candidates = candidates[np.abs(raw[row, candidates] - targets[row, column]) <= tolerance]
        matches = candidates.tolist()
        index = lookup[symbol]
        support = int((np.abs(targets[:, column]) > tolerance).sum())
        record = dict(symbol=symbol, matching_source_indices=matches,
                      nonzero_rows=support,
                      expected_max_error=float(np.abs(raw[:, index] - targets[:, column]).max()),
                      passed=matches == [index] and support >= 2)
        if consistency is not None:
            error = float(np.abs(held_raw[:, index] - held_target[:, column]).max())
            nonzero = int((np.abs(held_target[:, column]) > tolerance).sum())
            record.update(consistency_max_error=error, consistency_nonzero_rows=nonzero)
            record['passed'] &= error <= tolerance and nonzero >= 1
        records.append(record)
    return dict(records=records, all_coordinates_matched=all(r['passed'] for r in records),
                candidate_genes=len(names), tolerance=tolerance,
                source_identity_authenticated=False, model_output_axis_authenticated=False,
                independent_validation=False)


def projection_variance(values, weights):
    """Weighted endpoint variance, retaining covariance and actual cell count.

    No weight normalization or extra observation noise is added. The s2/n
    quantities assume conditionally independent cells (for example IID cells).
    Correlated-cell or culture-level variance is not estimated.
    """
    weights = np.asarray(weights, dtype=float)
    if (weights.ndim != 1 or not len(weights) or not np.isfinite(weights).all()
            or not np.any(weights)):
        raise ValueError("finite nonzero endpoint weight vector required")
    values = _matrix(values, len(weights), minimum_rows=2)
    shifted = values - values[0]
    scalar = shifted @ weights
    full = float(np.var(scalar, ddof=1))
    diagonal = float(np.sum(np.var(shifted, axis=0, ddof=1) * weights ** 2))
    mean = float((scalar + values[0] @ weights).mean())
    if not np.isfinite([full, diagonal, mean]).all():
        raise ValueError("endpoint arithmetic overflow")
    n = len(values)
    return dict(cells=n, genes=len(weights), scalar_mean=mean,
                scalar_sample_variance=full, scalar_sample_mean_variance=full / n,
                diagonal_only_scalar_sample_variance=diagonal,
                diagonal_only_sample_mean_variance=diagonal / n,
                covariance_sample_mean_variance=(full - diagonal) / n,
                full_to_diagonal_ratio=full / diagonal if diagonal > 0 else None,
                independent_biological_units=None,
                assumption="Conditionally independent cells (for example IID); correlated-cell, culture and batch variance not identified.",
                limitation="Observed residual covariance already includes measurement variation; do not add this variance twice.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('axis', 'variance'))
    parser.add_argument('input', type=Path, help="Local NPZ; axis: names/raw/targets/symbols; variance: values/weights.")
    args = parser.parse_args(argv)
    with np.load(args.input, allow_pickle=False) as data:
        if args.mode == 'axis':
            if ('consistency_raw' in data) != ('consistency_targets' in data):
                raise ValueError("both consistency arrays required")
            held = (data['consistency_raw'], data['consistency_targets']) if 'consistency_raw' in data else None
            result = numerical_axis_matches(data['names'].tolist(), data['raw'],
                                            data['targets'], data['symbols'].tolist(), consistency=held)
        else:
            result = projection_variance(data['values'], data['weights'])
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
