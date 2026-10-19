# Replicate-identified Virtual Cell decisions (RSD)

Development assessment on exposed PRISM 19Q4 (HTS002, 2.5 uM); frozen before the selection and evaluation blocks; no independent confirmation.

- Virtual Cell posterior whose signal and noise covariance are identified from replicate plates of purged reference compounds (cross-replicate covariance,
  reference-only selection by replicate-split decision utility); graded on a third replicate no policy can read and on the primary-screen run.
- Context selection (10 lines per compound): `rsd - raw` +0.118 [+0.084, +0.157], above the frozen threshold 0.067; equal to two raw reads at half the wells;
  cross-run +0.090; false progression 0.251 -> 0.170. Held in all three blocks (+0.081 / +0.085 / +0.118).
- Candidate progression (16 compounds per line): -0.008 [-0.037, +0.025], not supported in any block.
- Selected-candidate optimism +0.07 (raw +1.08), but 80% coverage on selected pairs 0.675. Chemistry prior hurt new classes; PCA below raw; KG escalation tied
  exploit-first; the posterior added nothing to the raw re-read rule.
- Exploratory: heavy-tailed pair-level replicate noise (kurtosis 3.2) dominates the extreme pairs progression picks.

Decision: REVISE (heavy-tailed pair noise before any progression claim); all three blocks are opened, so the next test needs an unopened tier. Full record,
freeze and verification in [`research/replicate_decisions_20261019`](../../research/replicate_decisions_20261019/REPORT.md).
