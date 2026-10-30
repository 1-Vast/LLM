# Failure and boundary log

* The paper's full PDF/HTML/JATS routes returned 429 after bounded retries;
  Highwire returned 403 and Europe PMC full text returned 500. The abstract is
  retained as the load-bearing paper evidence, with no invented training or
  replication details.
* Public engagement scouting did not find a single matched cell × drug × dose
  × time × engagement × genetic-reference × orthogonal-function table.
* The earlier 684-row transcriptome–PRISM bridge used different time/dose and
  pooled AUC semantics, and was rejected as a matched function experiment.
* The FLT3 r3 pilot improved held-out viability RMSE slightly after adding
  relative Kd, but the expression-conditioned contrast correlation was 0.0601;
  no target engagement, perturbation/rescue or independent biological repeat
  was available.
* A bounded DepMap 26Q1 GeneEffect stream passed byte/MD5 checks and joined the
  PRISM 19Q4 FLT3 table exactly for 395 cells. The first implementation froze
  dependency tertiles on repeated pair×cell×dose rows and reported `rho=0.0717`;
  an independent challenge rejected that unit. The corrected unique-cell
  result is `rho=0.0642`; pair-level mean-over-dose `rho=0.1116` is dose
  unstable (range `-0.2854` to `0.6170`), and cell-level mean direct rho is
  `-0.0706`. The repeated-row direct rho is `-0.0056`. This cross-release
  genetic reference did not close the cellular engagement or intervention gap.
* A fresh 2025–2026 engagement search found CellEKT and a live-cell kinase
  probe assay with useful dose/time/repeat fields, but no verified PRISM,
  DepMap or GDSC row-level crosswalk. Large PRIDE files and supplements were
  intentionally not downloaded under the 50 MB search budget.
* Prior shared-gain and kinobeads-to-function substitutions remain negative or
  unqualified. They are boundaries against silently treating a proxy as a
  functional mechanism, not evidence that every conditional rule fails.
