# Independent frontier assessment: local-feedback entropy adaptation

2026-10-23. Read the complete goal objective and the three assigned predecessor decisions before proposing. This report did not read peer-role reports. No new biological response array, protected endpoint, fit, synthetic execution, generated-code execution or API-model call was made. Two logical public GETs were used; no other network operation was needed.

## One bounded candidate and exact source

**FETA: Asking Less, Adapting Better: Feedback-Efficient Test-Time Adaptation for Vision-and-Language Navigation**, Zixu Wang et al., arXiv2610.30643v1, first timestamp2026-10-22T03:05:25Z in retained arXiv API metadata. Official full HTML is retained as feta.body with receipt; readable projection feta.txt. Read abstract, introduction/related-work framing, full SectionsIII–IV, SectionsV-C/V-D discussion and VI–VII implementation/human-agreement details. No author result was independently reproduced, and neither all figures nor complete appendix derivations were audited.

Source discovery used one newest-first arXiv query for learned optimizer OR test-time adaptation, first-submission date2025-01-01 through2026-10-23, max8. All eight metadata entries were inspected; only FETA was promoted to full-text examination. This is vocabulary/recency-biased, not an exhaustive novelty search. Scoped history search found no literal title/ID/FETA match in20261022/23 Markdown, which establishes only that search result, not independent novelty clearance. Old Titans/Hope/MIRAS/deltaTTT/MGTTA, SPICL, auxiliary neural-process and MAE-collision studies were not rediscovered as new candidates.

## Actual executable operation

After a completed episode, compute normalized action-policy entropies Hhat_t=H_t/log|A_t|. Filter trajectories by their within-trajectory standard deviation exceeding a recent-window percentile. Window150, initially pass all; percentiles vary by benchmark/split in SectionVII. In a selected trajectory choose t*=argmax_t ||grad_z Hhat_t||. Purchase exactly one binary judgment r_t* about whether the executed action was locally useful. Optimize only that step with

L = indicator(filter) * stopgrad(|r-p_theta(a|s)|^gamma) * (2r-1) * H_theta(s), gamma=.6.

The author's implementation description uses a full-parameter update at episode end, not a learned feedback update generator. Their simulator labels a non-stop action positive when geodesic distance to goal decreases; stop is positive when within success threshold. Human-study annotators see full observation history and before/after state/action. Ninety queries each receive one human annotation, with author-reported78.9% agreement; this is not multi-rater consensus or our measured result.

This is a concrete policy adaptation operator with a feedback-selection/resource restriction, not exactly ordinary scalar least squares. Its benefit hypothesis is that one action-local label can avoid mis-crediting every trajectory step, and that entropy-gradient saliency spends labels where this chosen entropy objective has a usable derivative. The source already owns those operations. Merely renaming navigation steps as interventions, entropy weighting as functional-error repair, and later checkpoints as inheritance supplies no new algorithm.

## Transfer contract and decisive limitation

Concrete desired cell application would be deciding which drug/dose stage to alter after a failed multi-stage treatment, using cheap local feedback while predicting final growth/apoptosis. A legal transfer would require an independently measured label for whether the selected stage improved the relevant later function, conditioned on legal history. Existing endpoint feedback in BeatAML or GDSC could supply paid terminal labels, but cannot supply per-step correctness or a geodesic-to-cure oracle. Source-supplied local navigation labels and cell endpoint labels are different information contracts. The already stopped organoid schedule study cannot be reopened to synthesize local labels from exposed endpoints.

An actual time-resolved assay might measure local changes, but transient decrease in cell number is not automatically a correct stage for the final treatment objective. A paired perturbation/counterfactual or justified surrogate would need validation. No new qualified public corpus demonstrating this contract was identified or downloaded here. Public drug-response endpoint data are a plausible static binary-feedback testbed, but static entropy adaptation would neither be a novel mechanism nor establish a cellular transition world model.

There is also a precise optimization restriction, useful for choosing a comparator rather than claiming a novel failure theorem. For two actions with executed-action probability p=sigmoid(z),

dH/dz = p(1-p) log((1-p)/p).

At exactly p=.5, this is0 for either r. Stop-gradient discrepancy weighting cannot change that zero. Ordinary binary cross-entropy on the same purchased label has derivative p-r, nonzero for either binary label. Therefore FETA-style signed entropy correction is not a replacement for all direct supervised feedback updates. For a verified executed action that is not the current mode, positive entropy minimization is also not generally guaranteed to increase its probability. Whether the paper actually executes such actions was not authenticated from code, so this is a conditional transfer warning, not an asserted flaw in their experiments. The paper itself motivates saliency by entropy-gradient vanishing near uniformity.

This analytic identity was not run as a new toy experiment. It is not evidence that a biological model encounters uniform predictions, that FETA fails its reported task, or that BCE beats FETA empirically. It exposes a necessary same-label direct-update control. A valid drug test must share exact paid labels and selection costs with supervised BCE/MSE/refit, full-history direct conditioning, ordinary continual replay, active selection, simple mixture and equal-budget program-search controls. Comparing only to entropy TTA would be insufficient.

## Decision

**NO_SUPPORTED_CELL_UPDATE_CORE / NO_FIT_GO.** Retain FETA as a new source-supported feedback-granularity precedent and explicit direct-label comparator requirement. Do not promote a biological signed-entropy updater, add modules/editor, or fetch an endpoint dataset merely because the source is recent. The missing ingredient is a distinct cell-specific update/measurement restriction with justified attainable local feedback, not an untried name for this source operation.

Reopen only with a genuinely specified local-label contract and new finite-cost operation whose expected gain exceeds same-label supervised updates; stop if gain depends on a fabricated local reward, unpriced paired experiments, or only an entropy-only comparator. This is not a universal rejection of active feedback, cell trajectories, familiar mathematics or functional adaptation. No cell-world, agent, inherited-updater, joint or improved-improver contribution is established. FETA's continued policy adaptation over repeated rounds is not by itself an improved algorithm for producing the next updater.

## Accounting and failure record

Two logical GETs, both200: search.body and feta.body, each with exact URL/status/UTC/bytes/SHA256 in matching receipt JSON. Search contains eight metadata entries, not eight fully reviewed methods. Native-agent model identity/tokens/currency unavailable; not invented. Zero DeepSeek/model-API calls, zero biological fits. All new source evidence lives in this directory and scripts under research/functional_error_renewal_20261023/frontier/.

Initial text projection attempted bs4, which is absent in maestro and failed with ModuleNotFoundError before producing output. Replaced it with standard-library HTMLParser; no installation or repeat GET. The readable projection includes site chrome/script text and is an inspection aid, not a canonical source replacement. No source original changed. Two unused requests from the4-GET ceiling were not spent without a specific unresolved question.
