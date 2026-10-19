# P0 Biological Residual Information Gate

Development gate on the exposed Jaaks 2022 screen, frozen before the run. It also audits
`action_substitution_20261019`.

- **Target annotation beyond functional similarity:** +2.8% (CI up to 7.7%). Real targets beat shuffled ones, but
  balanced accuracy is lower. Gate 1 UNDERPOWERED.
- **B5's consequential errors are not predicted by biological mismatch** on held-out families (AUROC 0.48).
  Quantitative kinobeads binding was worse than B5. Gate 2 UNDERPOWERED.
- **The reproducible decision opportunity is 0.012 ECB-like units, below the 0.02 minimum.** Only 5 families form
  choice sets. Gate 3 FAIL.
- **Feedback on the strongest prior (B5)** still helps: -16% MSE, balanced accuracy +0.028.
- **Audit corrections:**
  - B5 is function x target Jaccard.
  - The agent-value bound was specific to w of about 0.2 at epsilon 0.03.
  - Accuracy hid 75% prevalence.
  - Replicate dates share one cell stock.

Decision: UNDERPOWERED by rule; STOP for same-family substitution on Jaaks. The only qualified future endpoint is the
unopened AstraZeneca 2024 matrix screen (figshare project 163378), which needs approval and a new protocol. Record:
[`research/biological_residual_gate_20261019`](../../research/biological_residual_gate_20261019/REPORT.md).
