---
license: cc0-1.0
tags:
- biology
- single-cell
- perturbation
- differential-expression
- chemistry
size_categories:
- 1B<n<10B
configs:
- config_name: pdex
  data_files: pdex/*.parquet
  default: true
- config_name: cell_eval
  data_files: cell_eval/*.parquet
- config_name: control_expression
  data_files: zeroshot/control_expression.parquet
- config_name: cell_centroids
  data_files: zeroshot/cell_line_centroids_dmso.parquet
- config_name: cell_centroids_hvg
  data_files: zeroshot/cell_line_centroids_dmso_hvg.parquet
---

# Tahoe-100M Drug Screen Differential Expression Summary Statistics

Differential-expression summary statistics for the Tahoe-100M drug screen including
50 cancer cell lines × 384 drugs × 3 doses, one of the training datasets for
Rhaister. These are the statistics computed from the ~100M raw single cells of
[tahoebio/Tahoe-100M](https://huggingface.co/datasets/tahoebio/Tahoe-100M), including per-gene
fold changes, significance, and pseudobulk deltas per (cell line, treatment).

The repo includes two tables (`pdex` and `cell_eval`) plus the control-state references used
for zero-shot evaluation, and the dataset-definition files (filtering / split criteria)
under `definition/`.

## `pdex` per-gene differential expression (long format)

```python
from datasets import load_dataset
pdex = load_dataset("tahoebio/tahoe-de-rhaister", "pdex", streaming=True, split="train")
```

One row per (cell line, treatment, gene, plate). ~4.1 B rows total.

| Column | Description |
|---|---|
| `cell_line` | Cellosaurus ID of the cancer cell line. |
| `target` | Treatment: compound × concentration, e.g. `[('5-Azacytidine', 0.05, 'uM')]`. |
| `plate` | 96-well plate ID (1–14); the unit of plate-matched DMSO control. |
| `feature` | Gene symbol. |
| `fold_change` | log2 fold change, `log2(target_mean / ref_mean)`. `-inf` where `target_mean = 0`. |
| `percent_change` | `(target_mean − ref_mean) / ref_mean`. |
| `p_value` | Mann–Whitney U p-value, treated vs. plate-matched DMSO. |
| `statistic` | Mann–Whitney U statistic. |
| `fdr` | Benjamini–Hochberg adjusted p-value. |
| `target_mean` / `ref_mean` | Mean expression in the treated / control group. |
| `target_membership` / `ref_membership` | Cell counts in the treated / control group. |

## `cell_eval` pseudobulk expression deltas (wide format)

```python
cell_eval = load_dataset("tahoebio/tahoe-de-rhaister", "cell_eval", streaming=True, split="train")
```

One row per (cell line, treatment); 14 per-plate files. Columns `cell_line`, `treatment`,
then one column per gene (~2,000) holding the pseudobulk delta `mean(treated) − mean(control)`
on the linear (normalized) scale.

## Zero-shot reference tables

Control-state references used as the test-time predictor in the zero-shot setting:

- `control_expression`: per (cell line, plate, gene) DMSO-control mean expression.
- `cell_centroids`: one DMSO-condition centroid embedding per cell line.
- `cell_centroids_hvg`: per (cell line, plate) highly-variable-gene centroid of
  DMSO-condition mean expression.

## Definition & filtering criteria

`definition/` contains the dataset definition (`dataset.toml`) and the holdout split TOMLs
(`5_holdout`–`9_holdout` and titration variants). These encode the data paths, the
2,000-gene analysis set, plate aggregation (mean fold change / ref_mean, min p-value / FDR),
and the compositional `tahoe_5_holdout` split. A (cell, treatment) pair is held out
only when its cell line is in the holdout set and its treatment is in that cell's
held-out list, so each test cell and treatment is still seen individually in training.

## Source

```bibtex
@article{zhang2025tahoe,
  title={Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling},
  author={Zhang, Jesse and Ubas, Airol A and de Borja, Richard and Svensson, Valentine and Thomas, Nicole and Thakar, Neha and Lai, Ian and Winters, Aidan and Khan, Umair and Jones, Matthew G and others},
  journal={bioRxiv},
  pages={2025--02},
  year={2025},
  publisher={Cold Spring Harbor Laboratory}
}
```
