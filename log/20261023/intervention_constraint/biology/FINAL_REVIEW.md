# Final biological review: identity stop, no biological reciprocity result

2026-10-23. Read current RECIPROCITY_IDENTITY.json, RECIPROCITY_TEST.json, reciprocity.py, test_reciprocity.py, API_CRITIQUE.md and api/PROPOSAL.md. Inspected the existing RNA feature-construction code and two raw gene-metadata lines only. Did not open RNA feature values, functional values, new result matrices or protected labels. Independent reports remain unchanged.

## Decision and evidence

**ACCEPT_STOP_IDENTITY / REAL_RECIPROCITY_GATE_NOT_RUN.** The prospective all103-unique-coordinate requirement fails before numerical response loading. Saved identity metadata reports RHOXF2B maps to indices14109 and14112 after applying the frozen RHOXF2→RHOXF2B alias to feature symbols. I independently read the raw metadata at those zero-based indices:

    14109 ENSG00000203989 RHOXF2B
    14112 ENSG00000131721 RHOXF2

These are two separate stable feature identifiers and original symbols, not two copies of one identical feature row. Their convergence under a canonical label cannot establish that either is the conjugate response coordinate of the intervention represented by the canonical target label. No expression-dependent choice, row merge, convenient canonical-name preference, or post-hoc removal is justified by the frozen protocol. This is an identity/coordinate qualification failure; it is not a measured reciprocal-sign/cycle violation or evidence against cellular potentials.

The code's identity() reads the stored genes metadata member, original gene metadata, and file bytes for hashes. It does not load the features array. main() asserts identity status PASS before loading features. Saved report states response_values_loaded=0. No biological numerical reciprocity result exists. Therefore do not report a real-data compatibility rate, failed biological symmetry, response-model performance, or inability of all possible future identity-resolved interfaces. Future reconsideration would need an independently justified stable-ID/guide-target contract and a new pre-access coordinate protocol, not rewriting this stopped protocol.

## Existing baselines are not invalidated by this gate

Existing rna_pseudobulk.py accumulates all33,694 matrix-feature indices separately and writes features of shape103×33,694; its target-level RENAMES canonicalizes intervention identities. The two readout-feature rows were not collapsed or dropped in that full-feature construction. Earlier direct/RNA nuclear/fusion baselines use a full RNA vector and do not need a one-to-one target-index equals readout-index correspondence. This newly attempted reciprocity gate requires that stronger coordinate identity because its algebra directly exchanges intervention and readout indices. Failure of the stronger condition does not establish that old predictive computations were wrong or that all RNA information benefits disappear. It also does not retroactively prove the old biological labels globally correct; historical exposure and provenance caveats remain as previously recorded.

## Synthetic checks and scope

Saved five-case PASS_SYNTHETIC is supported by the inspected test assertions: positive-amplitude SPD example, near-zero amplitudes, dense nonconjugate forcing, sparse chordless cycle, and nonlinear finite forces. These validate intended algebraic bookkeeping and counterexamples, not biological observations. They explain why near-zero entries need separate exact/support accounting and why finite nonlinear potentials can fail endpoint reciprocity. The real endpoint remained unopened, so no numerical condition can be promoted from these tests.

One implementation limitation does not affect the stop: main() uses exact sign/support/diagonal violations for its headline status, while normalized triangles and graph cycle defects are descriptive fields. It does not make an exact-equality decision from a nonzero floating-point cycle residual. This matches a bounded necessary-sign diagnostic but cannot support a claim that its headline status completely decides symmetrizability. No need to expand or fit the solver after the identity stop.

## Additional API critique

The separate API response returns NONE. Its fixed-projection feature update, once dimensionally specified, is ordinary scalar regression on those features; this does not support new cellular constraints. Its expression orth(RNAij−RNAi−RNAj) is underspecified and cannot be used as executable biological semantics. More importantly, learning a nonadditive combination projection from an acquired double transcriptome adds measured information; same-information controls must receive it, and functional endpoint fit alone cannot validate its molecular direction.

The API's statement that gain disappearing after removing the projection/gate disproves its contribution is logically reversed as a generic ablation interpretation; it can show the component matters to that predictor. A matched direct model reproducing the benefit is the relevant competing explanation. I agree with root's API_CRITIQUE on this correction and on improved-improver: changing biological tasks with decreasing required sample counts is not a controlled comparison of old versus updated improvers. No new training or repeated API call is justified by this NONE result.

## Final scope

This phase produced a precise hypothesis, independent biological and mathematical criticism, actual reciprocal cross discussion, a source-only identity gate that stopped as prescribed, and synthetic scope checks. It did not verify an update algorithm or a drug decision benefit. NO_NEW_CORE_GO; world-model necessity, agent necessity, inheritance, joint synergy and recursive improvement remain NOT_ESTABLISHED. This local stop is not a global lack-of-data blocker and does not authorize weakening the full research objective.
