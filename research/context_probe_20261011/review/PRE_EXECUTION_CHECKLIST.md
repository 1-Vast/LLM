# Independent review checklist

Prepared 2026-10-11 (Asia/Shanghai) before reading any target response values for this study. This is an implementation audit checklist, not registration or biological confirmation.

## Required model-side isolation

- The split of entire response contexts is based on metadata only. Drug identities, doses, aliases and the terminal menu are qualified without evaluation outcomes.
- All target responses are absent before fitting means, scalers, basal feature selection, drug loadings, residuals, covariance and hyperparameters. Basal expression is permitted unlabeled deployment input, but fitted transformations use reference contexts only.
- Reference-only fitting and leave-context-out residual construction are distinct: a held-out reference residual may not enter its own fitted prior. If fitting a residual adapter, its training residual bank excludes the relevant held context too.
- The common eight probes are fixed from reference information; aliases of probes cannot remain in the terminal menu.
- Evaluation missingness cannot choose the drug library, target context population, probe panel, substitute measurements, or fallback ranking. A selected missing endpoint is recorded as unavailable/partial under a fixed estimand.
- A complete target-column poisoning test must preserve prior, panel, and prefeedback ranking. Keeping only purchased probe values fixed must preserve the committed postfeedback ranking.

## Decision and cost controls

- All feedback arms share the same strong development-selected prior, eight values, one turnaround and terminal pool. Zero-purchase prior is a separate deployment comparator.
- An offset/positive-affine mean arm must select the same top-k as its no-update counterpart, except explicitly documented numerical tie handling.
- Correctly identified and shuffled-identity probe updates use the same values and costs. The shuffle is fixed independently of evaluation outcomes.
- The compatibility comparator is refitted to this PRISM functional endpoint. The old RNA A/B model is not imported as if it supplied a validated functional covariance.
- Only committed choices are scored. No value from a terminal candidate is purchasable in this diagnostic; exact best top-k is evaluator-only.
- Costs of all eight attempted measurements are charged even if some values are missing; failed/missing measurements cannot be silently refunded. Scenario prices are not real monetary cost validation.
- The primary result is context-level paired top-k utility. MSE alone cannot pass. Seeds, genes and drugs are not extra independent contexts/cultures.

## Conditions and scope

- Treatment admission is exactly HTS, 2.5 uM, qualified single-compound metadata. Identity grouping and dose aggregation are documented.
- Cell identity/STR restrictions derive from metadata. Unknown identity is not silently resolved using outcomes.
- The downloaded replicate-collapsed files do not carry measurement-level culture/plate/time provenance. Five-day exposure is a source-protocol statement unless additional evidence is acquired.
- Source `primary-screen-readme.txt` documents treatment-wise ComBat across cell-line pool/replicate combinations before median collapse. Model-side masking cannot undo published upstream normalization or establish raw-assay preprocessing isolation.
- All public data are already exposed retrospective material. A newly frozen split supports algorithm diagnosis; even a positive result is not fresh scientific confirmation, prospective net benefit or independent biological replication.
- No selection-conditional, simultaneous/path-coverage or FCR guarantee follows merely from freezing a policy. Do not claim one in this first information diagnostic.

## Expected independent verification

1. Check input and frozen-artifact hashes, split disjointness, menu/probe membership, metadata qualification and exposure declarations.
2. Independently reconstruct cost arithmetic, top-k from saved committed scores, utility from evaluator labels, paired contrasts and missingness denominators.
3. Run rank-invariance and leakage poison checks against the public prediction API, without reimplementing the producer model.
4. Audit source boundary and control interpretation; record unresolved limitations without repairing outcomes or expanding scope after scoring.

Sources read before preparing this checklist: `research/next_round_review_20261011/README.md`, the earlier `pairwise_v3/joint_residual.py` and README, `budgeted_feedback_20261011/data/DATA_STRATEGY.md`, PRISM primary source readme and metadata headers. No target response matrix was read by this reviewer.
