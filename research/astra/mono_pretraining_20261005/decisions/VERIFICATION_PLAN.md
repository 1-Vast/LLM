> **File summary**
> - **Path**: `research/astra/mono_pretraining_20261005/decisions/VERIFICATION_PLAN.md`
> - **Purpose**: define what agent C will independently reproduce in phase 2 (from frozen prediction files and the contract text, not
>   from the lead's code), the comparator-strength, independence, leakage and attribution challenges, the concrete acceptance checks,
>   and the weak assumptions found in the lead's protocol.
> - **Core points**: 12 acceptance checks (A1-A12) with numeric thresholds; the attribution tests separate drug-level potency prior,
>   cell-background mapping, optimiser warm start and capacity; 14 protocol weaknesses (W1-W14), the most consequential being
>   an unspecified training-row set for the learned arms, a pair-level-only "strong simple" comparator, 3 reused seeds, a single
>   permutation draw, and a continue gate that a true 5% effect would almost never pass.
> - **Depends on**: `PLAN.md`, `knowledge_optimization_20261004/PRETRAINING_PROTOCOL.json`, `confirmation_campaign_20261004/**`.

# Independent verification plan (phase 2) and protocol audit

## 1. What must be independently reproduced

Independence rule: my harness is written from `campaign_contract.json` and the frozen prediction files only. It does not import
`design/`, `resources/`, `verify/`, or the lead's `src_*.py`. The existing independent engine in `verify/independent_check.py` is a
reference for expected outputs, not a dependency.

| Item | Reproduced from | Output compared |
|---|---|---|
| P2 campaign engine (legality, tie-break, cap, verification order) | contract text | purchases, confirmed, spent for every (arm, line, role, draw) of the lead's frozen score files |
| Baselines of record | contract text + builder panels via a logged ticket (phase 2 only, after freeze) | E: C_mean 117.5, S_both 118.5, R 110.5, oracle 151.0; HD (fp 30): C_mean 134.5, S_both 133.5, R 124.0, oracle 164.0; n4 (E): S_both 107.67, C_mean 97.67 |
| Primary and co-primary contrasts and intervals | frozen per-line values | relative gain, per-line gain, stratified bootstrap (contract seed), two-way bootstrap, sign-flip test |
| Mono-exclusion and fold-legality invariants | S0 manifests, fold file, history manifests | set identities, hashes |
| Selection of C*, lambda, steps inside outer-training sets | frozen inner-fold outputs | same selection from my own code on the same inputs |
| The learned models themselves | **not** re-trained by me unless the lead provides code and seeds; I verify their predictions' use, legality and determinism, and rerun one fold end to end as a determinism check (A11) | |

## 2. Acceptance checks

| # | Check | Pass criterion |
|---|---|---|
| A1 | Baseline reproduction with my engine (listed above) | exact equality for full-history numbers; n4 within +-0.01 per seed (sampler specification must be provided; if it is not, the n4 baseline is unverified and no n4 claim stands) |
| A2 | Frozen-score replay for all arms | 0 purchase mismatches against the lead's logs; cap never exceeded; no re-screen; no verify of an unrevealed or same-round hit; no last-round screen |
| A3 | Identical verification order across arms | assert equal verify scores (p_v of the comparator) per campaign, so only the round-1 order differs |
| A4 | Identical n1, M, rounds, screens bought and tie-break across arms | counts equal per campaign |
| A5 | Poisoning of outcomes | scramble the target line's unpurchased outcomes, its other role and every E line (and, in HD, every outer-test line's outcomes in the training pool): **0 purchases change** (precedent: 244 and 366 campaigns, 0 changes) |
| A6 | Mono-exclusion | zero Jaaks SIDM, COSMIC id, cell-line name or documented alias in the mono training and validation rows (exact and fuzzy name match); fit-group duplicates do not straddle splits; unmapped drugs counted |
| A7 | Fold and history legality | every history line is in the outer-training set of the same tissue; no E line anywhere in training or history; seeds logged separately for histories and initialisation |
| A8 | Training equivalence of pretrained vs scratch vs permuted | identical combo rows, order, steps, optimiser, regularisation, seeds; only initial weights (or mono labels) differ; parameter counts equal; training-log hashes recorded |
| A9 | Statistics | independent bootstrap with the contract seeds reproduces intervals to 4 decimals; two-way, sign-flip, leave-5-lines-out, per-tissue, history-draw random effect reported |
| A10 | Access control | every outcome read appears in the access log with owner and purpose; E not read before the freeze file; Vis never read |
| A11 | Determinism | rerun of one outer fold with 1 and with many threads gives identical purchases (scores rounded to 12 decimals are compared by rank, so floating-point jitter in a neural score can reorder ties; if it does, the arm is declared non-deterministic and the tolerance is reported) |
| A12 | Receipt hashes | frozen files, score files, fold files, S0 manifests hash-match the freeze |

## 3. Challenges to run

### 3.1 Comparator strength
- **Hindsight stress.** Report the contrast against the best of all simple rankings chosen in hindsight on the evaluated lines (at full
  history this hindsight best-of-six already beats C_mean by +4.3% E / +6.3% HD, so a model that beats only the nested-selected
  one but not the hindsight best has a weaker claim). Compute the same at n4.
- **Matched-information simple baselines**: D_add (drug-additive marginals from the same history), M_pot (public mono potency, no
  combo learning), and a cross-tissue pair-rate baseline (unordered pair rates from the other tissues), each selected inside folds.
- **Tie census**: fraction of menu pairs with exactly tied scores per arm and history size. At n4 most pairs have 0-4 history rows, so
  rate-based rankings are flat and the shared random tie-break decides; a continuous learned score always wins ties by construction.
  Report the contrast restricted to the pairs where the simple score is not tied, and with an informed tie-break (D_add) for S1.
- **Re-selection in the bootstrap**: re-select C* inside each resample (as the feedback study did) as a sensitivity; the contract's
  fixed C* understates comparator variance.

### 3.2 Independence and leakage
- A5-A8 above, plus: pretrain with the target tissue's mono rows removed (does transfer need same-tissue cells?); verify that the
  GDSC2 duplicate curves of a line (several DATASET / NLME curve ids) are all assigned to the same side; check for Jaaks drug
  concentration windows vs GDSC2 MIN/MAX_CONC mismatch used as an implicit drug identifier.
- Shared-institution check: report how many GDSC2 non-Jaaks cell lines share a tissue and a culture-collection source with the
  Jaaks target (descriptive).

### 3.3 Attribution of gains
Each arm differs from `W_pre` in exactly one respect; a gain counts as mono-pretraining only if it survives all of them.

| Control | Rules out |
|---|---|
| `W_scratch` (same inputs, rows, steps) | the learner, continuous heads and drug-additive structure |
| `W_scratch_long` (scratch trained for mono + combo step count on the combo rows) | extra optimisation, not mono information |
| `W_randlabel` (pretrain on mono rows with labels replaced by noise of the same scale) | optimiser warm start and standardisation |
| `W_drugperm`, `W_cellperm`, >= 20 draws each, report the distribution and the percentile of `W_pre` | label-to-drug and label-to-cell mapping; one draw (the protocol's "fixed permutation") is a weak null |
| `W_drugbias_only` (transfer b_a only, re-initialise e_a and W) | cell-independent drug potency prior |
| `W_tissue_out` (pretrain without the target tissue) | tissue-specific mono information |
| M_pot (mono potency, no combo learning) | all cell-independent mono information in a deterministic rule |
| Standardisation control: scratch with the same label scales and the same drug-bias initialisation computed from combo means | different standardisation/priors rather than mono labels |

Concentration diagnostics: leave-one-drug-out and leave-5-lines-out influence on the contrast; if the gain disappears after removing the
top one or two drugs it is a drug-level effect, not a "new cell background" effect.

### 3.4 First-round-only versus both rounds
The primary changes only the round-1 screen order. Verify (a) the same number of round-1 screens, (b) equal verification counts when
hits are fewer than capacity, (c) any difference in yield is attributable to which candidates were screened (report actions
changed, correct/wrong changes) and (d) the P3 sensitivity changes nothing about the primary verdict rule.

### 3.5 Poisoning and negative controls
A5 above; an **outcome-permutation null**: permute outcomes of lines within tissue (keeping rankings fixed) 200 times and run the
verdict function to get the false-positive rate of the continue rule; a **label-flip mono null**: pretrain on mono labels with the
drug-by-cell sign flipped; both must give no continue.

## 4. Weak assumptions in the lead's protocol

| # | Assumption (source) | Why it is weak | What to do |
|---|---|---|---|
| W1 | "Combo training: equal combo training budget across all learned arms; primary_history = 4 HD histories per tissue" (`PRETRAINING_PROTOCOL.json`) | It does not say whether the learned arms train on the 4 history lines or on all outer-training lines (about 51). The simple arms see only the history; unequal rows make any gain information, not mono | State explicitly that learned and simple arms see identical rows; freeze it |
| W2 | "strong_simple: select the original six" | All six are pair-level shrunk rates with k0 = 2 toward a pooled value and no drug-additive pooling; at n4 they are largely flat. The earlier n4 result already shows ranker choice moves yield by 10% (S_both vs C_mean) | Add D_add, M_pot, cross-tissue pair rates; report ties |
| W3 | Seeds 11, 23, 47 and "at least 2 of 3 seeds positive" | Three history draws reuse the same seeds as training; the baseline's history-draw SD is about 4.2%, equal to tau; sign agreement of 3 correlated seeds has no inferential value | >= 10 draws, history and initialisation seeds crossed, draw as random effect |
| W4 | "Fixed drug mapping permutation" and "fixed cell-background permutation" | One draw may fall near the identity or be unusually harmful or benign; it is not a null distribution | >= 20 draws each; compare to the distribution |
| W5 | Continue gate: point estimate >= 5% **and** lower bound > 0 versus scratch, strong simple and both permutations | At n = 61-64 and SD_rel 0.22, P(L > 0) is 0.43 when the true gain equals tau; the conjunction of four contrasts passes with far less. In effect the gate needs about 10% true gain, double the stated tau | State it; do not read a failure as exclusion of 5% (use the verdict function's L and U) |
| W6 | Mono target = fitted LN_IC50 as "transferable representation" | Fitted (nlme) parameters extrapolated beyond the screened window, per-drug dose ranges differ between GDSC2 and the Jaaks assay (7 library doses, two anchor concentrations), no demonstrated link from potency to the Emax-based synergy call | Report held-cell mono error against drug-mean and tissue-mean baselines; treat any transfer as potency-prior transfer until the controls in 3.3 show cell-specific content |
| W7 | Cell input = 14 PROGENy scores, rank 4 | Earlier cheap-context features were null or negative at n4 (TF similarity -1.86%, shuffled background slightly higher than real background, `REPORT_ZH.md` 4); a rank-4 bottleneck on a weak input makes "new cell background" gains unlikely and drug-level gains likely | Frame the claim as drug-level unless cell-permutation fails to match |
| W8 | "Exact SIDM exclusion" of Jaaks lines from mono training | The protocol itself says exact SIDM exclusion is not authenticated alias exclusion; Jaaks lines may exist in GDSC2 under other ids and curve groups | A6 fuzzy match; log residual risk |
| W9 | Tie-break "same rule for every predictor" | True, but continuous learned scores leave no ties while simple rate scores are flat at n4; the contrast then partly measures any informative tie-break | Tie census and informed-tie-break baseline |
| W10 | Pretrained arm gets mono steps plus combo steps, scratch gets combo steps only | Compute and optimisation mismatch | `W_scratch_long`, `W_randlabel` |
| W11 | n4 chosen as the primary regime | Chosen after the E n4 results were seen (S_both +10.2% over C_mean); exposure of E and of the whole library makes the regime and the comparator adaptive. The baseline in this regime is noisy (n8 below n4) | Declare as adaptive; report n8 and all; do not tune on E |
| W12 | "Line x pair intervals for broader pair scope" as the only dependence correction | The two-way interval is 2.2 times wider than the line interval; it is the honest interval for anything beyond "this library", and the design cannot reach tau-exclusion under it | Co-primary; state the UNRESOLVED consequence |
| W13 | Menu = pairs with both orientations passing QC | Conditions on target-line fit outcomes; identical across arms but limits external validity | Keep the declared limitation |
| W14 | Continue gate does not name the history-draw or tie issues, and "compute, wait" are reported but unlinked to the claim | A pretraining gain obtained with 100x compute is not a like-for-like policy gain | Disclosure template in `AGENT_ROLE.md` section 7 |
