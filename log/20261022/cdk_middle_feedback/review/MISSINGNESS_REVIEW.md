# CDK S3 missingness: exact author-source review

Reviewer `/root/recursive_distinct`, 2026-10-22. **GO for an explicitly declared author-consistent zero-convention exploration; do not claim that all Excel blanks have been authenticated as true measured zeros.** This distinction permits a useful numerical pilot without hiding its observation assumption.

No new S3/S4 outcome values, author TSV count values, sequencing archive or fitted result was read. The only new request was the exact public author QMD specified by the parent, under the preceding `MISSINGNESS_SOURCE_PROTOCOL.md`. Existing failed-reader evidence must remain intact.

## Request and provenance

Paper-authenticated repository: `https://github.com/douglas-russo/GuarducciAbravanel2026_barcoding-scRNAseq` (already present in the primary paper's saved links). Exact attachment-specified source path: `cell-line-barcoding.qmd`, branch `main`. One GET to its raw equivalent succeeded with HTTP 200, no redirects, at `2026-10-22T09:28:08Z`. Received 95,948 bytes, SHA256 `946c2903bc7ce66f80de8a4e19b842ae2116a96ae6dbb3a955fd02d1a8c9f533`. Body: `author_cell_line_barcoding.qmd`; receipt: `author_cell_line_barcoding.receipt.json`. No retry, tree listing, second request, archive, R execution or plot rendering occurred. The branch URL is mutable; the stored content hash pins what was actually reviewed.

## What the source establishes

1. **Same family of input tables, but a compiled long representation.** QMD lines 9–18 list `Barcodes_Palbo_study`, `Barcodes_Abema_study` and related worksheet names, state that raw barcode counts are in the supplementary table, then say: “we read in barcode counts and metadata from tables that compile this same data together into a long-format.” The QMD calls that supplement S2 rather than the final article's S3; matching worksheet names and repository provenance establish relevance, but that numbering mismatch should be retained in the record.
2. **Counts are widened with implicit missing combinations filled with zero.** Lines 249–284 select sample/barcode/count, join metadata and call:

   ```r
   pivot_wider(id_cols = barcode, names_from = graph_name,
               values_from = count, values_fill = 0)
   ```

   Lines 1024–1031 repeat this operation for source-filtered barcode/sample counts. Lines 319–324 and 1041–1048 do the corresponding fraction widening with `values_fill = 0`.
3. **The authors explicitly describe a not-seen→zero operation.** Lines 676–684 say:

   ```r
   #' impute a zero barcode fraction where that barcode is not seen
   #' (artifact of preprocessing).
   ...
   tidyr::complete(timepoint, Cluster, plot_bioreplicate_id,
                   fill = list(fraction = 0))
   ```

   This particular `complete` is at the aggregated cluster/fishplot stage. It corroborates the processing interpretation but must not be misquoted as a raw S3-cell importer.
4. **The unfiltered composition-distance path also fills absent barcode coordinates with zero.** Lines 1760–1765 recalculate fractions as `count / sum(count)` within sample; lines 1810–1821 widen fraction by barcode with `values_fill = 0` before Jensen–Shannon calculation. Lines 2135–2140 and 2185–2196 repeat the same pattern for sample-level comparisons. The count normalization also appears at lines 985–991. Thus zero-completion is not limited to one heatmap visualization.

Taken together, these are direct author-code evidence that absent **long-table barcode/sample combinations** receive zero in the assembled sample-by-barcode composition representation. This is stronger than assuming zero merely because sparse biological tables often use blanks.

## What remains unproven

The QMD does not contain the exact Excel S3 export builder or a wide-Excel-to-long-TSV transformation authenticating every omitted `<c>` cell. I found no explicit blanket `replace_na(0)` applied to arbitrary input assay fields. `pivot_wider(values_fill = 0)` fills implicit missing combinations; it is not evidence that an explicit NA or failed measurement inside an existing long-table row is safe to zero. Moreover, the author uses `sum(count)` without `na.rm=TRUE`: unresolved explicit numeric NA would not be made harmless by this normalization.

Consequently, the code does not prove that any particular omitted Excel Count/Fraction pair arose only from non-detection, establish an assay detection threshold, distinguish sampling loss from low abundance, or identify clone death. A sequencing/processed-table zero is not proof of zero living cells. Neither does a completed barcode matrix prove that an entirely absent sample was measured successfully.

The accurate conclusion is: **the proposed sparse-completion convention agrees with the authors' composition-analysis representation; its application to S3 structural omissions remains an explicit processing assumption where the precise exporter is unavailable.** It is not a reconstructed biological measurement fact.

## Minimal admissible numerical amendment

Proceed without another source request if the pilot is renamed/described as using that source-supported convention and the following contract is frozen before rerunning the parser:

- Restrict to the already authenticated treated sample columns and valid literal barcode-ID rows. Treat only a structurally absent/empty Count **and matching Fraction** pair as an implicit absent barcode/sample combination under the convention. Distinguish omitted XML cells from explicit error cells, explicit NA/text annotations, formulas without a usable cached value and malformed numeric values.
- Preserve genuine numeric zeros. Reject explicit nonnumeric/NA/error values and negative/nonfinite counts. If one of Count/Fraction is present and the other absent, report it as a separate discrepancy requiring a rule, not automatic evidence for zero. Do not assume a whole empty/missing sample is an all-zero measured assay; require a positive finite observed count total per sample.
- Count the structural missing pairs, genuine zero cells, explicit-NA/error cases and asymmetric pairs per sample and in total. Preserve the original cell-location diagnostic and the original failed-reader logs. The amended parser must state which class it completes and attach this QMD hash.
- Normalize counts over the completed full barcode representation, keep OTHER mass, and apply the same convention to every method and information arm. Check available numeric Count/Fraction pairs for consistency under the frozen normalization. Do not let a count/fraction discrepancy choose the representation giving the best model score.
- Predictions and scientific conclusions remain conditional on this processed-composition convention and sequencing sampling noise. The numerical pilot is allowed to estimate conditional information value; it is not a validated clone-survival experiment or a full author-analysis reproduction.

If a reader supports only treating *all* missing tokens as zero, amend it before running. This is a small, testable parser change: synthetic tests should distinguish structural paired omissions from explicit NA/errors, asymmetric missingness and an absent assay. No additional neural model or biological experiment is needed to make that distinction.

A supplementary convention-sensitivity calculation is permissible only if its rule is recorded before model results are inspected. Avoid a purported “complete-case” barcode analysis selected using held-out End completeness: that would allow target missingness to define the prospective feature universe. Where no alternative assumption yields an identifiable common target, the honest sensitivity statement is the unresolved observation assumption, not an invented confidence interval.

## Decision and boundaries

**GO:** numerical exploratory composition forecasting with explicitly logged author-consistent completion of structural missing barcode/sample pairs and the above validation. **NOT ESTABLISHED:** that every S3 omitted cell is an independently verified measurement zero, that non-detection means extinction, or that the missingness mechanism is known. Keep both statements visible in the final pilot report.

This resolves the immediate execution question at an appropriate development level; it does not require indefinite source hunting. If explicit errors/asymmetric pairs/absent samples are actually encountered, stop only that unsupported parsing path and record their exact class before choosing another numerical contract. The original broader virtual-cell/agent/RSI objective remains unachieved and is not narrowed to a zero-convention composition predictor.
