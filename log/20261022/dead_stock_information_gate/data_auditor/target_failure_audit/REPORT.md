# 72 h target diagnosis: four finite negative export values

**Decision: ABORT_INVALID_TARGET remains in force.** The registered nonnegative exported-count/log transform is incompatible with the observed 72 h target on this exact asset configuration. This is a data/observation-domain qualification failure, not a negative result about the dead channel, biology, world models, agents or RSI. The stopped experiment is not rerun.

The independent diagnostic inspected all 288 relative-72 h intersect_live_cells records across 96 wells: 284 are finite and nonnegative; four are finite negative integers. There are zero empty/missing, malformed or nonfinite live literals in this target scope. The four negative records belong to two wells at concentration label 25. Only these four individual records received additional tot_cells/intersect_dead_cells access.

| CSV source line, including header | Context | Well | Image | live literal | total literal | dead literal | total − dead |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: |
| 6230 | mcer-1e3 | H7 | 1 | -2 | 142 | 144 | -2 |
| 6575 | mcer-3e3 | H12 | 1 | -24 | 357 | 381 | -24 |
| 6598 | mcer-3e3 | H12 | 2 | -1 | 468 | 469 | -1 |
| 6621 | mcer-3e3 | H12 | 3 | -15 | 472 | 487 | -15 |

All have Elapsed literal 72, relative time 72 from the well's first acquisition at 0, and Date Time literal 5/18/2019 4:30:00 PM. Context remains an opaque source label. In each bad row, live+dead equals total exactly under Decimal arithmetic; total and dead are finite/nonnegative and dead exceeds total. This supports a **difference-compatible exported arithmetic value**. It does not establish the author's construction intent, background subtraction, overlap correction, measurement noise distribution, literal biological death exceeding total population, or negative true viable cells. Exact arithmetic in four rows is not an authenticated global exporter definition.

The complete authorized live-only target panel for H7 is [-2,11,17], mean 26/3 ≈8.6667. Its positive mean does not rescue the frozen requirement that every image readout be nonnegative before aggregation. H12's panel is [-24,-1,-15], mean -40/3 ≈-13.3333; even a post hoc mean-only rule would not make log2(mean+1) valid. No image or well was removed and no value was clipped or imputed.

The main run reached its saved 96-well prefix-only kinetic cache and then failed at the first fold's training-target read. No direct predictor fit, out-of-fold prediction or information-value score exists. The diagnostic's inspection of all 72 h live values is an explicitly expanded exposure after that terminal failure; it is not restored blindness or permission to reuse these targets as a confirmation set. Additional 72 h dead/total access is confined to the four listed rows; other future responses and the Replicates file remain numerically unopened by this audit.

Four synthetic scope tests passed before actual access. They checked closed-value perturbation invariance, no non-72 h response conversions, no dead/total conversion for valid live rows (including siblings of an affected well), invalid literal classification and the negative-image/positive-mean distinction. FREEZE.json and DIAGNOSTIC.json confirm the original source, pre-response freeze, original code/protocol, prefix cache, RUN.txt and FAILURE.txt remained byte-identical. Source SHA256 is 7ec7b019690f09f833a81bd4a98ec47e39df32ac249c767714a7e2d817a39c92. This audit made zero fits, filters, clips, downloads or retests.

Required missing source definition: how total/dead/live segmentation objects, intersections, corrections and any subtraction/normalization were constructed; why the dead-labeled export can exceed the total-labeled export; and what biological endpoint each field represents. Nonnegative total alone would not authenticate viability. The present arithmetic does not select or validate a signed observation likelihood. A later observation model/source question requires independent scientific rationale, review and a prospective protocol; no total-target substitution, likelihood repair or 24→72 h rerun is authorized here.

Exact records, the affected live panels, field-access ledger and unchanged-file checks are in DIAGNOSTIC.json. The opposing post-failure exchange is preserved in POST_FAILURE_CROSS.md. The conclusion stops this exact registered configuration, not all use of this source and not all virtual-cell research.
