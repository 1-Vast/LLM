# MAESTRO research progress — 23 October 2026

The current evidence supports useful ordinary feedback screening and calibration in bounded drug-discovery tasks. A new transferable updating mechanism, a necessary virtual-cell world model and recursive self-improvement remain unestablished. This report consolidates the historical summary, the latest experiment and opposing reviews; bootstrap draws and reviewer agreement are not independent biological evidence.

## Latest result: paid two-stage repeatability

The Jaaks developmental replay contains 5,390 metadata-selected single-anchor units across 78 SIDM clusters. Scout and final observations come from globally disjoint validation-plate roles. Every policy pays 3,234 reads, represented by 22,638 combination-well proxies. A success requires both purchased observations to exceed a fixed synergy threshold of 0.10.

| Policy | Repeat-positive units | Status |
|---|---:|---|
| Fixed original ranking after the same scouts | 675 | Frozen comparator |
| Scout-magnitude feedback ranking | **919** | Frozen tested policy |
| Equal original/scout rank mixture | 830 | Frozen descriptive comparator |
| Strong fixed paired acquisition at equal cost | **876** | Frozen strong comparator |
| Binary scout gate, then original ranking | **898** | Post-result simple control |
| Binary scout gate, then fixed hash ranking | 869 | Post-result simple control |

Feedback gains **43 repeats, or 4.91%**, over strong fixed paired acquisition. The fixed-choice SIDM-bootstrap count interval is [9, 78]. A post-result sensitivity normalizing each resampled arm by its own cost gives an improvement of 1.90 repeats per 1,000 proxy wells, interval [0.40, 3.28]. These are conditional developmental intervals, not prospective policy guarantees.

The simpler gated-original policy captures most of the gain. Feedback adds only 21 repeats over it; the count interval [-11, 52] and cost-aware interval [-0.01, 1.88] per 1,000 wells include zero. Superiority over that simpler control is unestablished; equivalence is not proved.

The frozen rule passes only for this repeatability endpoint. At threshold > 0, feedback yields 1,061 repeats versus 1,409 for fixed paired acquisition. Its fixed allocation can confirm at most 1,078 units. At the primary threshold, final-only positive counts are also lower for feedback: 919 versus 1,037. Do not retune thresholds, budgets or splits on these results.

All data were previously exposed and the validation candidate pool was selected by the original study. Shared normalization, drugs and plate structure limit independence. The cost is a seven-combination-well-per-read proxy, excluding shared controls, plate packing and turnaround. No new wet experiment or protected AZ outcome was used.

## What survived critical review

Selecting an already-positive scout can improve the two-read endpoint even if scout magnitude predicts nothing about the final observation. The result therefore supports ordinary paid screening, not a learned cellular updating law or latent-hit certification. The post-result binary-gate controls expose this distinction.

Three separate reviews covered statistical validity, assay evidence and primary literature before cross-discussion. Their strongest corrections were:

- The first final-only acquisition design was mathematically set-dominated by direct acquisition and was discarded before response conversion or freeze. A new explicit two-read task replaced it.
- Fitted Student-t likelihood ratios, finite null grids and capped-mean diagnostics do not establish real-assay conditional validity or FDR control. Missing required pools must prevent a diagnostic pass.
- A fixed half-capital wallet and half weight per multiplier have different guarantees. Same-stream expert scoring does not identify the outcomes of unqueried actions or whole alternative adaptive histories.
- Generic adaptive testing, mixing and credit are insufficient novelty. Direct methodological controls include [adaptive e-growth sampling](https://arxiv.org/abs/2609.26651v1), [active proxy e-values](https://arxiv.org/abs/2502.05715v2) and [globally stopped e-BH](https://arxiv.org/abs/2502.08539v3). Their assumptions do not establish our assay's validity. The full-method comparison with Scientific CI/CD remains incomplete because its current OpenReview PDF was inaccessible.

Source-level independent recomputation reproduced the metadata universe, nominations, paid-read ledger, all counts and all 2,000 bootstrap draws, including the post-result controls and cost sensitivity. Nine lightweight regression/integration checks and four statistical primitive groups passed. These checks establish selected arithmetic and software contracts, not biological replication or a new mechanism.

Failures remain recorded: multi-anchor concentration strings caused the first metadata-only freeze to fail; an incomplete synthetic fixture was corrected; and a supplementary-plan hash mismatch was caught and restored without replacing its receipt. Current hash agreement does not repair historical global provenance or prove secure blinding.

## Historical evidence retained

| Line | Retained conclusion | Boundary |
|---|---|---|
| BeatAML functional feedback | Ordinary covariance updating with eight drug measurements reduced MSE by 23.49% and top-3 regret by 15.07% | Exposed development; no RSI conclusion |
| Consistency-based updater | Lower order/batch sensitivity but worse MSE in all three tested seeds | Stop that configuration |
| CDK composition feedback | Small composition-prediction improvements | Functional drug-response benefit unestablished |
| CD14 stratified source rationale | Preset continuation gate failed | Do not rescue by changing marker, cut or split |
| CellHealth | Membership and source qualification completed; BRAF grouping issue corrected | Qualification is not a new predictive result |

Historical stops apply to their tested configurations; they are not blanket rejections of model families. This synthesis does not rerun those studies or promote their claims beyond their original scope.

## Decision and next admissible experiment

Keep ordinary binary-gated screening as a strong baseline. Do not expand a certification or RSI stack on the basis of this result. Before a new core claim, specify a later functional outcome whose success does not include the already-used selector, justify acquisition costs and independent future task units, and compute headroom and detectable effect before fitting. Compare on the same information against strong direct prediction, ordinary conditioning/retraining, active allocation and simple mixtures.

World-model, agent, inherited-updater, joint and improved-improver gains all remain unestablished. A later inheritance test needs independent ordered tasks; an RSI test must compare the changed improver with its frozen predecessor and equal-budget ordinary search.

## Retained evidence and storage

[EVIDENCE.json](EVIDENCE.json) retains the exact current numerical summaries and verification records. [SOURCE_INDEX.json](SOURCE_INDEX.json) lists original report paths and content hashes, including opposing reviews and failure records. [PACKAGE.json](PACKAGE.json) binds this compact package. Full originals remain locally retained; this publication packages reports and key results, rather than datasets or experimental implementations.

`log/` retains key reports, results and decisions. Detailed data and source bodies belong under `data/`; experimental implementations and tests belong under `research/`. Promotion to `src/` or `tools/` requires relevant validation and an explicit decision. No runtime implementation is promoted by this publication.
