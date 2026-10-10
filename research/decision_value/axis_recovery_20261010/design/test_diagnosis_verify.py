"""Support occurrence is insufficient for identity discrimination."""
import numpy as np
from scipy.sparse import csr_matrix

from research.decision_value.axis_recovery_20261010.design.diagnosis_verify import group_patterns


def test_zero_contrast_separates_equal_occurrence_counts():
    matrix = csr_matrix(np.array([[1,1,0],[1,1,0],[1,0,1]], dtype=bool))
    assert group_patterns(matrix, [0,1], [0]) == [{0,1}]
    assert group_patterns(matrix, [0,1,2], [0]) == [{0}]


def test_all_source_genes_are_competitors_even_when_outside_endpoint():
    matrix = csr_matrix(np.array([[1,1,0],[0,0,1]], dtype=bool))
    assert group_patterns(matrix, [0,1], [0]) == [{0,1}]
