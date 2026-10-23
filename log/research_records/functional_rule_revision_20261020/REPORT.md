# Report: evidence-driven revision of functional transfer rules (O'Neil 2016)

Executed 2026-10-20 under [PROTOCOL.md](PROTOCOL.md) (frozen before the challenge batch was disclosed; hashes in `FREEZE.json`).
Exposed internal-development data: a hidden partition is not independent confirmation. The object tested is a conditional functional
prediction rule, not a molecular mechanism. Software tests passing is not scientific validation.

## Decision

**UNSUPPORTED** (internal development, estimation pilot). The bounded revision did not improve selection of unseen drug pairs over
same-data fixed-structure refitting, and a useful gain at the registered margin is excluded for the raw candidate:
revision candidate minus refit = **-0.0005** shortlist utility (pair-bootstrap 95% [-0.0008, +0.0005]; one-sided upper bound at alpha/3 = +0.0006, margin 0.005).
Gate G rejected the revision and every comparator candidate, so each deployed procedure equals the refit and the three registered deployed contrasts are exactly 0 by construction; the raw-candidate contrasts carry the information.
Standard structure learning did not help either (no full-dictionary or conventional procedure beat the refit). The project should not invest further in this form of rule revision on this task; the binding limit is task headroom, not the editor.

## What was run

Raw route on the authenticated originals: 22,737 pair-cell groups (583 pairs x 39 cells, batches 1/2, complete 4x4 grids, none excluded), 350/87/58/88 pairs in S/C/G/F.
Endpoint A = 1 - mean(X/X0) over 16 points; 5 pairs per cell shortlisted from the 88 F pairs; utility = macro-cell mean true A. Fixed model: ridge on the residual from a same-batch interpolated multiplicative reference.
Frozen dictionary of 16 edits (6 gated splits of shared components, 10 module-pair additions). One 60-pair challenge panel (2,340 groups) from C. Margin 0.005 (rule below), design label ESTIMATION_PILOT (worst S-side minimum detectable effect 0.018 > margin).
Margin: the brief's default 0.02 exceeds the source-side headroom (S pools: Bliss-reference regret 0.023, fixed model 0.0186), so the pre-C rule gave 0.005. The protocol text says "about 0.017" for the fixed model; the measured value was 0.0186.
Reproduce: `run.py qualify`, `run.py all`, `verify.py` (commands in PROTOCOL.md). Verifier output: VERIFY OK, no model refit and no sealed outcome opened.

## Answers

**A. Did new observations improve decisions?** Not demonstrably. Refit on S+C minus the frozen S-only model: +0.0009 [-0.0005, +0.0020] (below the 0.005 margin; reference-residual metric -0.0006). Regret fell from 0.0085 to 0.0076. The combination data themselves matter more than the challenge: S-fitted model minus the pure single-agent reference ranking +0.0040 [+0.0003, +0.0086]; refit minus reference +0.0049 [+0.0011, +0.0097]. Ordinary information-update benefit, not a revision result.

**B. Did bounded revision beat same-data fixed refitting?** No. Raw candidate (E13, add a shared component for module class m1-m3, coefficient +0.012) minus refit -0.0005 [-0.0008, +0.0005]; drug-jackknife SE 0.0011. At G: utility gain +0.00026 (threshold 0.0025), MSE ratio 1.009 overall and 1.006 out of scope (<= 1.02): rejected on the utility criterion. Deployed = refit. Activity MSE on F: revision 0.00266 vs refit 0.00267; 49% of F groups got larger error than under the refit (mean excess 0.0001): a diffuse reshuffle, not a repair.

**C. Did it beat the full-dictionary and conventional comparators?** Raw revision minus raw full dictionary -0.0000 [-0.0009, +0.0011]; minus raw conventional champion (boosted trees; the factorisation machine lost on S+C validation) +0.0011 [-0.0010, +0.0034]. Deployed comparators are all the refit (G rejected the full dictionary, +0.0010 at G; the champion, -0.0025 and MSE ratio 1.088). Nothing is distinguished; non-significance is not equivalence.

**D. Transferable benefit on F?** None detected. Only 3 of the 88 F pairs (117 groups) lay inside the revision's scope; the edit changed in-scope predictions by 0.0076 on average (out of scope 0.0014), yet utility did not move (0.7551 vs 0.7557 refit; oracle 0.7633; Bliss reference 0.7508). The reference-residual secondary measure is also flat (-0.0037 revision raw vs -0.0032 refit). Remaining headroom after the refit is 0.0076, so the 0.005 margin would require recovering two thirds of it: this task is nearly saturated by the reference plus drug- and drug-by-cell effects.

**E. Was a policy comparison supported and executed?** No: NOT_RUN. Acquisition bundles, controls and physical costs cannot be recovered from the originals; Agent strategy gain (counterexample-directed vs coverage vs direct confirmation) is untested. The challenge panel is a fixed design counted in groups, not a purchased physical budget.

**F. Did the executable rule change cross-pair sharing, and where?** Yes, mechanically. Before: refit structure, 1,569 parameters (lambda_base 30, lambda_theta 3). After: one added column and coefficient (1,570 parameters), `R_hat = R_hat_refit_structure + beta * 1[module class = m1-m3]`, beta = +0.0120; supporting evidence 31 source/challenge pairs in scope, 7 in the challenge panel (273 challenge groups, 3 flagged counterexamples out of 54 flagged in 2,340). It altered 195 unmeasured groups (5 pairs, 117 in F). Full numeric records: `RULES.json`, `RULE_EFFECTS_revision.csv`, `RULE_EFFECTS_api.csv`. Its evidence base was thin (challenge gain +0.0023 relative CV, all-groups +0.0010), and none of the 16 edits improved S cross-validation by more than 0.4% before the challenge, so the editor was selecting among noise-level differences.

**G. Did the API proposer add anything?** No. One deepseek-flash request, one HTTP attempt, 3,569 prompt + 101 completion tokens, 1.45 s, valid answer (receipt `API_RECEIPT.json`; prices unverified so no money figure). It chose E14 (add shared component for module class m2-m2, beta +0.022) rather than the deterministic E13 while its rationale claimed to follow the highest-challenge-gain rule; E14 has the higher all-groups but lower challenge gain. Raw API arm minus refit -0.0011 [-0.0012 lower bound, +0.0006]; minus raw revision -0.0006 [-0.0010, +0.0007]; G rejected it (+0.0002). Integration and contract compliance are established; held-out utility gain is not. This single bounded run cannot show robust LLM behaviour.

**H. What remains untested?** Policy value (counterexample-directed acquisition under real costs); a task with more decision headroom (the reference already captures most of the ranking); edits built from richer functional components than single-agent modules (modules came from monotherapy profiles only, one module held 4 drugs and a 0-pair class made one edit inert); larger challenge budgets; independent confirmation (all quantities here are retrospective, on exposed data, with technical repeats rather than independent cultures); the DBP/Potter task (separate, not started); faithful comboFM/BATCHIE reproductions (our conventional learners are home-built approximations).

## Integrity notes

* Pre-C S-only development (grids, margin rule, per-edit S gains) is disclosed in the protocol; the dictionary was not changed after seeing it. C, G and F were each read once through the vault (ledger in `RESULTS.json`).
* Predictions and nominations of all methods were sealed and hashed before G; F predictions for every candidate were fixed before G, so G could only choose between precomputed predictions.
* G was a consumed development resource; F was opened once. The intervals respect repeated pairs (whole-pair bootstrap, drug jackknife, cell bootstrap) but not independent replication.
* Deployed-procedure contrasts are degenerate here because every candidate was rejected at G; this is the registered fallback, not an error.
