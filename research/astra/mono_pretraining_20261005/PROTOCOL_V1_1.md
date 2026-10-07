# Protocol v1.1 — one development-only repair (declared AFTER v1 development outcomes were seen)

**Status.** EXPLORATORY and post-outcome. The v1 development result (`results/s2_dev_*.json|pkl`, `s2_gates.json`: G2 and G3
failed, E sealed) is retained unchanged as evidence. `FREEZE.json` (v1) is superseded by `FREEZE_V1_1.json`; the v1 versions of
`run_s2.py`, `common.py`, `analyze.py`, `make_freeze.py` are preserved byte-for-byte in `archive_v1/` (hashes in both freezes).

**Why.** The independent verification (`decisions/VERIFY_REPORT.md`) reproduced every v1 number exactly, found no leakage, and found
the v1 fine-tune grid unfair to the learned arms: l2_theta in {1, 30} is too weak for a 3-6 parameter head fitted on four history
lines (about 1,300 rows of mostly noise), so every learned arm over-fit and lost to the base ranking (scratch arms too), and the
grid had no near-zero-weight fallback although `decisions/AGENT_ROLE.md` required lambda = 0 to be reachable. The pretrained gain
over the base ranking moved from -0.0091 (theta 30) to -0.0002 (theta 3000); the own-mono ceiling from +0.0005 to +0.0023
[+0.0009, +0.0040] at theta 30000. The v1 "HARM" class and the failed G2 are therefore partly an artefact of the grid.
(The protocol's own "at most one development-only repair in a new frozen version" clause applies.)

**Change (only this).** `CFG_GRID` = l2_theta in {30, 1000, 30000, 1e6} x l2_init in {10, 300} (8 configurations; 1e6 is an
exact fall-back to the base ranking for practical purposes). The same grid, the same HD concordance selection rule and the same
matched tuning opportunity apply to *every* learned arm (pretrained, scratch, permuted, potency-only, own-mono, tier X).

**Unchanged.** Data, folds, histories (10 draws), mono pretraining (S1 outputs reused), arms, base-ranking choice, the P2 contract,
estimands, bootstrap, verdict function, gates G1-G3 and their thresholds, E sealed unless all gates pass. No arm, gate, threshold,
endpoint or data is added. Outputs are written with suffix `_v1_1`.

**Interpretation limits.** The v1 selection of the grid-best configuration per family by HD concordance is the same procedure as in v1
but over a larger grid (more selection optimism for every learned arm equally); the base ranking was itself selected on HD yield among
seven candidates (favours the base in HD comparisons against it). Attribution contrasts (pretrained vs scratch / permuted) are not
affected by that asymmetry. A positive v1.1 gate result would still be development-grade: E is the only transport read and is
exposed data.
