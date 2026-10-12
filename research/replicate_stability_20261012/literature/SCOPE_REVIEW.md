# Scope and source review: secondary PRISM repeat ranking stability

Reviewed 2026-10-12, Asia/Shanghai. This is a prerequisite audit of **retrospective, exposed, processed-assay reliability**, using frozen local methods/README and metadata provenance. It is not Experiment Q execution, independent raw validation, an Agent superiority study, or mechanism adjudication. No new network request or response-value read was performed for this review.

## Attachment comparison

The earlier and reattached reports, titled `MAESTRO：对上传研究报告的进一步审查与研究建议`, are byte-identical: each contains 17,342 bytes, SHA256 `0fd78bbd06164a3c52859580c6686a9a4b19572b7d155dc7dbf8589741230594`. Their exact paths and the current read date are recorded in `SOURCE_READ_RECEIPTS.json`. Reattachment supplies no changed Experiment Q design. The report calls Experiment Q a candidate name, requires matched observation permissions, budgets and menus for B2/B3, and reserves independent confirmation for a suitable extra source or independent experiment after freezing the method.

## What the source methods support

[Corsello et al., Nature Cancer](https://doi.org/10.1038/s43018-019-0018-6) describes a five-day, barcoded pooled-cell-line assay, followed by cell lysis and Luminex barcode measurement. The secondary screen uses eight four-fold dilutions from 10 micromolar; 2.5 micromolar is one exact tested dose. Released log2-fold-change is relative to DMSO after QC and ComBat, not an absolute live-cell count. The original Extended Data Figure 1 caption states: “Up to 3 independently treated plates (range 1–3 based QC filtering) in one screen are median-collapsed.” This supports repeated independently treated assay plates. Separate thaw/culture-start independence remains unresolved; its absence from the schema does not negate the documented assay repeats.

The secondary README identifies `screen_id`, `compound_plate`, `detection_plate`, `well`, `broad_id`, and `dose`. Pool metadata supplies the cell row, pool and barcode mapping. A detection plate identifies detection for a replicate of a compound plate; it is not itself a verified independent biological culture. Pooling couples cell lines within an assay. Detection beads are measurement events, not new biological subjects.

MTS010 consists of technical redos added on 2019-11-22 and was not part of the original preprint analysis. Although the README recommends it for ordinary downstream use, **exclude it from this HTS002-only frozen reliability question**. Do not silently substitute a redo, another screen, another well assignment, or another dose when a selected observation is missing. A later redo study would need its own stated design.

The methods say: “ComBat was run over each treatment condition separately by considering the log2-transformed fold-change values as probes and pool-replicate combinations as batches.” The processed repeats have therefore participated in shared condition-specific correction. Repeat splitting after release does not undo that coupling. Agreement is evidence of stability of the released, corrected response representation; it is not a clean raw-repeat holdout, independent preprocessing validation, prospective evidence acquisition, or proof that ComBat removed the actual biological/platform confounder. Preprocessing can increase or decrease apparent agreement; this audit does not quantify that effect without raw outcomes and an independently designed preprocessing study.

## Admissible paired contrast and dependencies

Freeze the contrast menu from metadata before opening outcomes. Match HTS002, a single compound plate, exact dose, cell row/context and pool mapping. For each drug condition, verify its `broad_id`/well identity and distinct repeated detection-plate mappings. Require the two drugs in a contrast to share the same recorded repeat mapping; never pair two unrelated plates merely because each is labelled a replicate. Two drugs have different wells, but each drug's well must map consistently across HTS002 repeats. Ambiguous duplicate condition records are non-evaluable until the mapping is resolved.

For two eligible drugs a/b, define `D_r = y(a,r) - y(b,r)` at the fixed cell context, exact dose and compound plate. Compare the same D across matched repeats. With log2-fold-change, lower means a stronger measured viability effect; `D_r < 0` ranks a ahead of b if stronger killing is the stated objective. This can describe sign agreement, reversal, magnitude disagreement and missingness of within-plate drug ranking contrasts. It does not identify why a ranking changed.

The experiment owner confirmed the proposed pairing on 2026-10-12: exact archived representative full drug-batch ID, numeric 2.5 micromolar, HTS002 experimental treatment, same `compound_plate`, and identical actual `detection_plate` IDs for both drugs, retaining original `column_name` and wells. The menu comes from the archived prefeedback Top-20, compares prior ranks 1-10 with 11-20, and excludes the eight frozen probes. Context qualification uses STR/pool metadata. Exact-zero ties and sign/magnitude summaries carry no biological threshold; full and partial repeat coverage remain distinct. This confirmation concerns metadata and the frozen recipe; finite outcome availability is not established by it. `PAIRING_COORDINATION.json` records the coordination separately from original source receipts.

The analytic unit is the **context × compound plate × drug pair × matched repeat comparison**. It is a descriptive unit, not an independent biological sample. All pairs reuse drugs; three repeat-pair comparisons reuse plates; cell lines share pools and processing. Report these hierarchy counts separately and summarize by context/compound-plate block. Do not treat the combinatorial pair count as independent n, use it to manufacture confidence, or infer a background-versus-platform variance decomposition from this single-screen design.

Preserve all metadata-selected comparisons, with absent/nonfinite outcomes reported as non-evaluable. If a common finite subset is necessary for a metric, label the subset and its coverage explicitly; do not replace missing drug choices using hidden availability. Keep any margin/tie rule frozen before value access and report it as a descriptive sensitivity rule, not a biological equivalence or significance threshold.

## Falsifiable bounded claim

The admissible claim is: **for the frozen HTS002 exact-dose, same-compound-plate contrasts, the ordering of the released ComBat-corrected responses is reproducible to the extent reported across the documented assay repeats**. A predeclared sign agreement and reversal summary can falsify a stronger stability claim when repeat directions disagree; insufficient coverage makes it non-evaluable rather than successful. No numerical “stable” threshold or positive result is introduced by this source review. A higher-than-expected agreement must still be bounded by joint preprocessing, shared units and the exposed data history.

This prerequisite may reveal that a source does not reliably resolve close rankings. It cannot show that supplemental observations improve terminal decisions, that a virtual cell is corrected, or that an Agent adds value. Those are different claims requiring an independently frozen task and comparisons.

## Difference from the uploaded Experiment Q

| Uploaded proposal | This authorized prerequisite |
| --- | --- |
| B0/B1 separate empirical and virtual-cell contributions | No predictor or transfer model is fitted |
| B2/B3 compare deterministic planning with autonomous scientific investigation | No Agent, acquisition policy, literature-driven action or KG is evaluated |
| Additional evidence should improve a committed terminal decision | Only existing assay-repeat ranking reliability is described |
| Mechanism cases require genuinely discriminating observations | No stress/compensation/platform origin labels are assigned |
| Independent confirmation follows method freeze on a suitable extra source/experiment | Published processed repeats are retrospective and exposed |

The proposal requires B2/B3 to have equal observation permissions, budget and selectable experiments. That requirement allows policies to choose different actions; it does **not** mean they realized the same evidence. A later comparison intended to isolate the Agent's reasoning from evidence access additionally needs a **same-realized-information control**: identical prior/checkpoint, acquired observation values and missingness, committed action history, available source/tool evidence, terminal menu, cost accounting, and outcome sealing. If literature/tool evidence is available only to B3, the contrast measures that package's benefit and cannot isolate Agent reasoning. Report evidence-access gains and reasoning/action gains separately, with declared computational/API costs. These are requirements for a future design, not new arms added to this audit.

A complete-outcome oracle is the **realized utility ceiling for selections from the fixed, fully observed terminal menu**, under the same feasibility constraints and utility definition; it can give realized regret relative to a committed selection. It is not by itself an estimate of expected EVPI, achievable EVSI, or a paid evidence benchmark. Under a specified common probability distribution and decision-utility assumptions, standard EVPI bounds EVSI; neither quantity is estimated here. With incomplete outcomes, the observed-subset best selection cannot be renamed a complete oracle. The uploaded P0 “information limit” recommendation remains an unmet scientific requirement if only hindsight selections are computed.

## Provenance and stopping boundary

`SOURCE_READ_RECEIPTS.json` records exact reused-source SHA256 values, current read scopes, original retrieval receipts where available, and attachment equality. Historical files are unchanged. This audit makes no new endpoint, efficacy, novelty, biological mechanism, or production-promotion claim. It supplies a source/design boundary to the experiment owner; negative or non-evaluable reliability is a valid result. A new model/Agent/KG study needs its own justified evidence channel and frozen protocol.
