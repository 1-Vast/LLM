# Independent generated-input audit

2026-10-22. Functional auditor. Status: **PASS**.

Read only the generated input artifacts and frozen design/code receipts. No source ZIP or test targets were opened, no preparation/model stage was started, and no frozen file was modified. Large full/without_mono feature arrays were checked through NPZ headers rather than loaded during the live fit.

All input artifact hashes match INPUTS_RECEIPT; frozen nonarchive hashes and preparation code/protocol/design/schema STARTED bindings match. The pinned source ZIP hash was not independently recomputed because this audit was explicitly forbidden to reopen that source.

| Role | MASTERs | Episodes | Target rows | Valid episodes | Unique paid matrices | Unique paid rows | Logical bundles | Logical paid rows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 160 | 1030 | 48230 | 1030 | 1350 | 61670 | 2060 | 94220 |
| validation | 64 | 430 | 20174 | 430 | 558 | 25550 | 860 | 39452 |
| test | 96 | 644 | 30212 | 644 | 836 | 38276 | 1288 | 59080 |

Input validity is 100% in every role. Train/validation labels are finite; every test input y is NaN. ROWS, episode, role, target pair and metadata identities align. Paid endpoint means and paid own-grid residual summaries were independently recomputed from PAID_OBSERVATIONS and match. Logical two-bundle cost is retained per episode despite physical source deduplication.

Conversion receipts contain only paid train/validation/test mono+combination and train/validation target inhibition scopes. Actual conversion counts equal unique paid rows times three plus permitted target counts; no test target, target attached mono/fitted, or reserve scope exists. The 413 reserve MASTERs and 2749 reserve episodes are absent from active keys/population and remain numerically unopened under this interface.

These checks establish consistency of generated inputs and declared field use; they do not prove the released source's original normalization provenance or independent prospective assay separation. No performance/novelty conclusion is drawn.

Machine-readable checks and exact hashes: INPUTS_INDEPENDENT_AUDIT.json. Failed checks: none.
