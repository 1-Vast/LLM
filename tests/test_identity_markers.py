"""Feature labels are trusted only when cell-identity markers confirm them.

File summary
- Path: tests/test_identity_markers.py
- Purpose: pin the marker-based label check that found the one-row offset in the SciPlex3
  Figshare release, using synthetic matrices so the test needs no local asset.
- Core points: a shifted label table is detected and its offset recovered; an unsupported or
  ambiguous alignment is refused by name; an out-of-range column is unlabelled, never borrowed.
- Interfaces: `test_*` functions only.
- Depends on: virtual_cell.identity_markers
"""
from pathlib import Path

import numpy as np
import pytest

from virtual_cell.identity_markers import (
    IDENTITY_MARKERS,
    check_markers,
    resolve_label_offset,
    shift_labels,
)


def _matrix(stray_header: bool):
    """Three contexts whose marker columns are high only in their own context."""

    genes = ["FILLER%d" % i for i in range(40)]
    contexts = list(IDENTITY_MARKERS)
    columns = []
    for context, markers in IDENTITY_MARKERS.items():
        columns.extend((gene, context) for gene in markers)
    columns.extend((gene, None) for gene in genes)
    rng = np.random.default_rng(0)
    means = {c: rng.uniform(0.01, 0.2, len(columns)) for c in contexts}
    for index, (_, context) in enumerate(columns):
        if context is not None:
            means[context][index] = 3.0
    labels = [gene for gene, _ in columns]
    if stray_header:
        labels = ["id gene_short_name"] + labels[:-1]
    return means, labels


def test_correct_labels_pass_at_offset_zero():
    means, labels = _matrix(stray_header=False)
    offset, checks, refusal = resolve_label_offset(means, labels)
    assert (offset, refusal) == (0, None)
    chosen = next(c for c in checks if c.offset == 0)
    assert chosen.tested == chosen.peaked_in_expected_context == 12


def test_stray_header_row_is_detected_and_its_offset_recovered():
    means, labels = _matrix(stray_header=True)
    assert not check_markers(means, labels, offset=0).passed()
    offset, _, refusal = resolve_label_offset(means, labels)
    assert (offset, refusal) == (1, None)
    corrected = shift_labels(labels, offset, len(means["K562"]))
    assert corrected[:4] == list(IDENTITY_MARKERS["K562"])
    assert corrected[-1] is None, "the column past the end of the table stays unlabelled"


def test_labels_that_fit_no_offset_are_refused_by_name():
    means, labels = _matrix(stray_header=False)
    scrambled = list(reversed(labels))
    offset, _, refusal = resolve_label_offset(means, scrambled)
    assert offset is None and refusal == "feature_labels_fail_identity_markers"


def test_too_few_testable_markers_cannot_pass():
    means, labels = _matrix(stray_header=False)
    means = {"K562": means["K562"]}  # the other contexts were never measured
    check = check_markers(means, labels)
    assert check.tested == 4 and not check.passed()
    assert set(IDENTITY_MARKERS["MCF7"]) <= set(check.untestable)


def test_an_alignment_the_markers_cannot_decide_is_refused():
    means, labels = _matrix(stray_header=False)
    # Two passing alignments: permissive thresholds admit every offset.
    offset, _, refusal = resolve_label_offset(means, labels, minimum_fraction=0.0, minimum_tested=0)
    assert offset is None and refusal == "feature_label_offset_ambiguous"


def test_context_means_of_different_lengths_are_rejected():
    with pytest.raises(ValueError, match="differ_in_length"):
        check_markers({"K562": np.ones(3), "MCF7": np.ones(4)}, ["HBG1", "TFF1", "X"])


ROOT = Path(__file__).resolve().parents[1]
SCIPLEX = ROOT / "data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad"


@pytest.mark.skipif(not (SCIPLEX.is_file() and (ROOT / "data/external/hgnc/hgnc_complete_set.txt").is_file()),
                    reason="needs the local SciPlex3 release and the HGNC table")
def test_the_sciplex3_release_labels_are_offset_by_its_stray_header_row():
    """The published table names column j's gene at row j + 1; the realignment must say so."""

    h5py = pytest.importorskip("h5py")
    from evaluation.model_validation import verified_feature_labels

    with h5py.File(SCIPLEX, "r") as f:
        table = f["var"]["ensembl_id"]
        published = (table["categories"].asstr()[:][table["codes"][:]] if isinstance(table, h5py.Group)
                     else table.asstr()[:])
        obs = f["obs"]["cell_line"]
        lines = obs["categories"].asstr()[:][np.clip(obs["codes"][:100_000], 0, None)]
        valid = obs["codes"][:100_000] >= 0
        matrix = f["X"]
        pointer = matrix["indptr"][:100_001]
        columns = int(matrix.attrs["shape"][1])
        data = matrix["data"][: pointer[-1]]
        index = matrix["indices"][: pointer[-1]]
    row = np.repeat(np.arange(100_000), np.diff(pointer))
    sums = {}
    for line in ("A549", "K562", "MCF7"):
        member = (lines == line) & valid
        keep = member[row]
        sums[line] = np.bincount(index[keep], weights=data[keep], minlength=columns) / max(member.sum(), 1)
    check = verified_feature_labels(ROOT, published, sums, columns)
    assert check["first_published_label"] == "id gene_short_name"
    assert check["offset"] == 1
    hbg2 = "ENSG00000196565"  # HGNC:4832 HBG2
    column = check["labels"].index(hbg2)
    assert max(sums, key=lambda line: sums[line][column]) == "K562"
