# P0.5R: finite informative axis recovery

**Status: prospective design. No new RNA requests were made by this design task.** The historical 39-coordinate gate is retained separately for every source file. Certifying c44/c45 does not certify c40/c44's unopened 250-cell plan, all 2,000 columns, or a STATE decoder axis.

## What must remain fixed

The existing data endpoint is the mean of 39 declared `X_hvg` coordinates, with weights `+1/39`; it is not an independently signed apoptosis program. Existing control-only matching compares each coordinate to `log1p` of the same cell's stored named X values. Stored X in this filtered release is normalized expression, not raw UMI. Do not apply `normalize_total`, change the tolerance, reorder a model output, drop all-zero genes or infer shared file order to manufacture a pass.

The original c44 audit identifies 34/39 coordinates. CD38, PLCB2, IFNB1, F2 and TNF have no nonzero identifying trajectories in its selected DMSO cells. c45 has not been certified. Consistent identified subsets do not establish identical full column order. A new audit must independently test all 39 coordinates in c44 and all 39 in c45, against every named source column in the relevant file, including genes outside the endpoint.

## Path A: authoritative lineage first

Accept a released ordered mapping only when the receipt binds the precise source repository revision, per-file generation provenance, 2,000 ordered positions and transformation to the filtered dataset. Preserve its raw bytes and hash. Recovered local files must match their original registered hash; the old 1,969-name and separate 1,972-name historical receipts are not interchangeable assets. Treat data input order and checkpoint decoder order as separate certificates. STATE issue #279 is evidence of a missing asset, not a maintainer-authenticated axis.

Absent a full authoritative map, numerical certification may establish the 39 endpoint coordinates only. It cannot extrapolate the remaining 1,961 identities.

## Path B: expression-guided calibration, with finite limits

Public gene-named summaries may select calibration conditions. This is **expression-guided selection**, not metadata blindness. They identify likely informative conditions; their means cannot authenticate an individual stored coordinate. Record the exact summary revision, file, condition, plate, gene identity, transformation, cell count and missingness. Raw UMI averages, normalized X averages and log averages are different quantities; use positivity only as a selection hint unless the summary's precise transformation is authenticated. Never infer a nonzero-cell probability from a positive mean alone.

Use the following bounded first stage for each file:

1. Construct eligible source conditions that have full-QC cells, exact component/dose/unit labels, sample and plate joins, and global protocol-time provenance. Exclude all future P0.6 sentinel conditions and their pooled treatment sample IDs across **every cell-line partition**. Also exclude the old 250 noise rows and any protected evaluation sample/condition. Store exclusions explicitly, not as a line-name filter.
2. Query named statistics for the five c44 unresolved genes and **all 39** in c45. Choose up to **four calibration conditions per file** by a deterministic greedy covering rule: maximize the number of not-yet-covered genes with authenticated positive target expression, then maximize a preregistered within-gene quantile score, then exact sample identity. Statistics missing for a gene count as unknown, not zero. Cell count supplies eligibility, not gene identity.
3. Proposed first-stage cell budget: **16 discovery and 16 holdout cells per condition**, selected before paired vectors are read using a stable barcode/row hash. Prefer holdout cells from a different calibration sample on a matched repeat plate. Both source samples remain calibration-only. If a second sample does not exist, a disjoint cell holdout is a weaker same-source validation and must be labeled that way. No source is automatically independent because cells do not overlap.
4. For each selected cell, read exact raw-CSR row pointers, index/value spans, and the paired complete stored X_hvg vector. CSR offsets and indices are metadata; values and X_hvg are expression. Coalesce only touching selected spans, never full chunks that contain evaluation or sentinel expression. Preserve every HTTP range, body hash and per-stage cumulative charge, including repeated bytes.
5. Do not keep adding samples until the gate passes. The stage has at most eight conditions and 256 total cells across the two files. An **expression-byte and total-response cap** must be frozen after source layout inspection and before RNA reads; propose 20 MB incremental successful response bodies including metadata, CSR, X_hvg and repeats. A conservative projected CSR size estimate must fit that cap. If it does not, reduce the preregistered stage before freeze, not while observing coordinate success.

If the stage is uninformative, return `BLOCKED/INSUFFICIENT_COORDINATE_INFORMATION`. Only an explicitly separate stage, with another freeze, exclusions and spending cap, may proceed. A deterministic next-stage rule may be preregistered, but a first-stage failure is preserved and future selection is disclosed as adaptive calibration. This is calibration allocation, not independent biological decision validation.

The exact smallest successful sample size is unknowable before observing sparse trajectories. The finite design is a minimal *attempt*, not a promise of authentication. Positive summary expression does not guarantee informative selected cells, and some genes may remain unidentifiable in both lines.

## Numerical acceptance and holdout checks

For each declared coordinate and source file:

- Compare the discovery trajectory to `log1p(stored X)` for **all 62,710 source columns**. Check the source's actual dimension rather than hard coding a matching list from another file. Reject duplicated gene symbols, duplicate CSR indices, nonfinite/negative stored expression and inconsistent row identities.
- Require exactly one source-column match within the unchanged absolute tolerance `1e-5`, the exact expected symbol, and at least two nonzero discovery cells (`abs(value)>1e-5`). A nonunique sparse trajectory remains blocked even when one matching symbol has the expected name.
- Freeze that discovered position, then test the separate holdout vectors. Require all holdout differences at most `1e-5`, at least one nonzero holdout value for the coordinate and no holdout contradiction. All-zero holdout concordance alone is not independent informative confirmation.
- Independently reconstruct received raw CSR and stored X_hvg bytes and recompute matching against all source genes without importing producer matching logic. Bind the per-file mapping to row manifest, source revision, transforms, chosen conditions, match counts, nonzero counts, excluded sample IDs and verifier hashes.

The release gate is **39/39 discovery-and-holdout passes in c44 AND 39/39 in c45**. Failed or ambiguous coordinates retain unknown identity. The mapping is not completed by borrowing a match from the other file. Previously identified c44 coordinates may supply a diagnostic consistency check but cannot exempt them from the new full gate.

If an authoritative axis establishes all positions, numerical holdout checks can be treated as version/transform sanity checks instead of empirical identity discovery. That is a different provenance-backed route and must be reported separately.

## Independent new named-X observation channel

An alternative can operate without unknown HVG order **only as a separately named channel**. Authenticate the relevant file's `var/gene_name` dictionary and its one-to-one mapping to stored X CSR columns. Require each of the 39 requested symbols to occur exactly once; missing or duplicated symbols block that channel. Extract named source columns directly, apply `log1p(stored normalized X)` once, and keep the same declared +1/39 weights if that is the desired new RNA scalar.

The currently retained c44 calibration source already contains raw CSR for 224 DMSO cells (28 cell-line/sample/plate strata of eight cells). Those bytes can support an exploratory named-X control audit after a **new freeze before new scalar/variance summaries are computed**, while clearly disclosing that their full expression has already been exposed for axis authentication. This costs no new RNA download. Direct source-name identity makes an all-zero gene a valid observed zero in this channel; it still cannot identify a hidden X_hvg column.

Certify the named channel's metadata axis, transformation, weights, rows, units and source joins independently. Give it a distinct channel ID, such as `tahoe_filtered_named_X_log1p_mean39_v1`; retain `equivalence_to_old_hvg_endpoint=false/unproven` and `old_hvg_gate_released=false`. Do not feed its variance into old cached STATE residual updates without a dedicated equivalence/calibration study. Zero observed variance in eight cells is not proof of a noise-free future measurement.

For an exploratory control-only diagnostic, compute `var(X @ w, ddof=1)/actual_n` and the diagonal comparator from the same normalized/logged 39-vector, with a complete-vector conditional bootstrap. Actual n is eight here, not 32. Plate/sample group means describe source contrasts; they cannot identify causal biological/batch variance or certify culture-level intervals. The named-X diagnostic does not finish the old 250-cell noise experiment or produce treated-response fidelity, RNA-to-function or decision benefit.

## P0.6 reuse of the official pseudobulk baseline

The official code receipt is pinned at `goodarzilab/tahoe100m_analysis` commit `4f4123d9e1ac6a02e2447935ba47b04fc2f061f8`; six source responses total 33,289 bytes, below the 5 MB method-source cap. See `METHODS_REVIEW.md`.

The useful baseline compares **drug-minus-same-plate-DMSO signatures** between plate6 and plate14 across genes. It subsamples treated cells while holding each plate's DMSO reference fixed. This helps distinguish high baseline-expression correlation from reproducible perturbation signal and studies dependence on treated-cell count. A fixed noisy reference is conditioned on, not rendered noise-free.

For the small future sentinel panel, use a preregistered cell-depth grid that the actual observations support (for example 8, 16 and 32 cells), complete-vector samples without replacement and deterministic seeds. The ten Monte Carlo subsamples in the official code are repeated draws from existing cells, not independent biological repeats. Report source-pair signature correlation alongside scalar source disagreement and conditional variance. Keep all references and pair dependencies explicit.

The official script recomputes 2,000 Seurat HVGs from plate6 after `normalize_total` and `log1p`. That is **not the old filtered X_hvg basis or 39-coordinate endpoint**. A faithful full-script reproduction needs its preprocessing and named HVG list; a cheap 39-gene adaptation is a different, declared panel baseline. Do not use the script to reconstruct a missing STATE HVG order. Do not treat its compositional abundance or cell-cycle metrics as separately measured viability or apoptosis.

## Dual-core boundary

The agent may propose finite calibration conditions and explain receipt conflicts; a deterministic validator owns exclusions, condition legality, byte caps and source identity. The frozen STATE model remains unchanged. Until a qualified observation channel shows incremental held-out information under a separate decision protocol, acquisition gain and P2 stay closed. Source-coordinate progress establishes usable measurement semantics, not the effectiveness of the world model or an LLM acquisition policy.
