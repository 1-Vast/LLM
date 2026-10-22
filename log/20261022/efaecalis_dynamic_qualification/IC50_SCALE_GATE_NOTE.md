# Fig 4B IC50 target scale: minimum pre-response check

2026-10-22. Scientific-skeptic clarification requested by Root. No outcome cells read.

The primary Fig 4 caption in `SWITCH_DESIGN_LITERATURE.json` identifies the bottom-right plotted collateral effect as log2-transformed IC50 fold change. The identity-only workbook audit reported `B39=Relative`, `B40=IC50s`, twenty strain IDs in `D34:W34`, fourteen day labels in `C35:C48`, and still-unopened numeric response cells `D35:W48`.

**These facts authenticate a candidate relative-IC50 block, but do not yet establish its stored scale.** A plot may transform raw ratios before drawing, or may directly plot an already transformed table. The phrase “Relative IC50s” alone is compatible with both. Therefore neither “use raw values as log2 fold change” nor “apply log2 to raw values” is currently justified.

Minimum sufficient check, without reading response values:

1. An explicit author definition for this exact block, or author figure/export source code, connects its sheet/range or exact exported array to Fig 4 bottom-right.
2. That connection specifies whether the stored quantity is IC50, IC50 divided by an ancestral reference, or log2 of that ratio; it specifies any transformation performed between table and plot.
3. The ancestor reference / normalization has a documented identity and units, sufficient to interpret the response. If deriving relative values from absolute IC50, the corresponding ancestor denominator must be identified before calculation.

An explicit Excel formula or export expression can satisfy this check without evaluating its numeric result. A plotting script that loads a different raw file is insufficient unless the workbook block is linked to the same exported variable. An ordinary number format, presence/absence of negative values, value range, histogram, or predictive performance is not an acceptable scale check.

Once documented, freeze exactly one transformation: identity for a stored log2 ratio, log2 for a stored positive ratio, or documented ancestral normalization followed by log2 for absolute IC50. Do not compare transformations against held-out outcomes.

If this minimum chain cannot be established, record `SCALE_UNRESOLVED` and do not execute a scientifically interpreted IC50 primary pilot on this block. This is separate from algorithm novelty: resolving scale would permit a narrow prediction qualification; it would not rescue the two stopped DeepSeek constructions.

The original proposed individual day8–13 AUC gate is `NOT_EXECUTED`; a summary AUC row and seven sampled-day OD panels must not be silently substituted for the required individual daily AUC trajectories. A replacement IC50 protocol must be registered before numerical access and only after its identity/scale qualifies.
