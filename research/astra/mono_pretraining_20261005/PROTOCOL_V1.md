# Protocol v1 (frozen before any GDSC2 label or Jaaks combination outcome is read by this study)

Study: `research/astra/mono_pretraining_20261005/`. Date of freeze: see `FREEZE.json`. Status of all results: **EXPLORATORY** —
Jaaks et al. 2022 was opened by earlier studies; nested folds reduce in-study tuning bias only.

## 1. Question

Does external single-drug supervision (GDSC2 fitted dose-response, 63 menu drugs) supply *action-comparison*
information — which anchor x library pair to screen in a new line — beyond (a) the development-selected strong simple
history ranking, (b) the same architecture trained from scratch on the same combination history, and (c) the same
pretraining with a broken drug or cell mapping? A secondary question is whether a coupled agent can use it better
than a deterministic rule; `decisions/AGENT_ROLE.md` quantifies why this is expected to have no headroom.

Task evaluated: **A, intervention selection** (rank the registered S x V menu of a new line for confirmed discovery under the
frozen two-round contract). Task B (evidence acquisition) is represented only by the *own-mono ceiling* (an information
ablation, not a priced action). Task C (mechanism discrimination) has no qualified data and is not evaluated.

## 2. Data and units

* Combination data: Jaaks 2022 anchored screen as built by the frozen builder (`feedback_validation_20261003/jaaks.py`),
  menu = S x V pairs of breast/colon/pancreas, both orientations, author QC (RMSE <= 0.2). Label for learning: 100 x max over
  anchor concentrations of mean SYNERGY_DELTA_EMAX of each orientation; calls: the authors' `Synergy` call (frozen builder).
* Mono data: GDSC2 release 8.5 fitted dose response, file SHA256 `f950a702...7560`; records of the 63 Jaaks drugs with an
  equal Sanger DRUG_ID (sibling IDs not pooled); target `y_rel = (LN_IC50 - ln MAX_CONC)/ln 2` (log2 steps relative to the top
  dose; extrapolated IC50 kept, no censoring flag exists); fitted-parameter transfer from one joint NLME fit (records are not
  independent observations; provenance with Jaaks plates is not authenticated). Composite `1032|1372` and `2265` have no mono
  labels and stay in the menu (embedding rows 63, 64; pairs with them are excluded from every learned arm's training rows and
  receive g = 0, i.e. fall back to the base ranking).
* Cell covariates: 14 PROGENy scores from baseline RNA, standardised on all 1,431 public-context cells (covariates only,
  identical for every arm). They are RNA-derived priors, not measured pathway activity or culture state.
* Unit of inference: the target cell line. Roles (SV/VS), history draws and permutation/seed members are averaged inside a line.
* Partition: the frozen 125-line partition (HD 64 / E 61). HD is split into 5 tissue-stratified line-grouped folds
  (`common.fold_of`, seed 20261005). E is one further fold.

## 3. Mono exclusion rule (deviation D1 from the design-only protocol)

S0 found that GDSC2 contains the Jaaks lines themselves and almost no other breast/colon/pancreas line. The design-only
protocol excluded all 125 Jaaks lines, which would test only cross-tissue transfer. **Tier Y (primary)**: mono pretraining
for an outer fold excludes that fold's Jaaks lines (so the target's own mono labels never enter its pretraining) but
includes the 837 non-Jaaks cells and Jaaks lines of the other folds, i.e. public mono of other lines of the same tissue, as a
lab would have. **Tier X (secondary)**: no Jaaks line at all (cross-tissue only). Jaaks combination outcomes never enter mono
training. A 126th line (HPAF-II) is excluded everywhere. Residual risk: GDSC2's joint fit uses the target line's records to
estimate shared parameters; disclosed, not removable.

## 4. Model and arms (low capacity, one code path)

Head: `z -> W (14x4) -> r`; mono `y = beta_a + r.e_a`; combination residual `g = theta . phi`, with rotation-invariant
`u_a = r.e_a`, headroom `rho_a = sigmoid((beta_a + u_a)/2)` and features
`h6 = [u_a+u_b, u_a u_b, u_a-u_b, rho_a+rho_b, rho_a rho_b, rho_a-rho_b]` (deviation D2: the design-only coordinate-wise
`r*(e_a+e_b)` form is not identified up to rotation of the rank basis; see `test_bilinear.py`). `beta` is fixed in fine-tuning;
W, E are pulled to their initial values (L2-SP). Training rows = exactly the n4 history rows of the baseline (leave-line-out pair
prior, line-centred, SD-scaled residuals). Score = contract S_both prior + centred g (mean of both orientations).

| arm | initialisation / information | purpose |
|---|---|---|
| S1 | base simple ranking chosen on HD among S_both, L_v, C_s, C_v, C_mean, C_prod, D_add | strong simple comparator |
| D_add | additive S-drug + V-drug effects from the same history | drug-additive comparator |
| `pre_h6` (**primary**) | mono-pretrained W, E, beta; h6 head | transfer value |
| `pre_h3` | same, context-only features (no potency) | context vs potency |
| `pot_p3` | beta only, no context (u = 0) | drug-level potency prior ("M_pot") |
| `scr{0..9}_h6` | random W, E, beta = 0, same code, rows, steps | same-architecture scratch; seed spread = noise floor |
| `dperm{0..9}_h6` | pretraining with the 63 drug labels randomly relabelled (K=10) | validity of drug mapping |
| `cperm{0..9}_h6` | pretraining with context permuted within tissue (K=10) | validity of cell mapping |
| `preX_h6` | tier X pretraining (no Jaaks line) | cross-tissue-only transfer |
| `own_h6` | observed GDSC2 mono shifts of the line's own mono replace predicted u (ceiling) | information ceiling, **not deployable** |

Fine-tune configuration: 4 frozen configurations (l2_theta in {1, 30} x l2_init in {10, 300}), 200 Adam steps, lr 0.02,
chosen **per arm family on HD** by mean within-line Spearman gain over the base ranking (never by yield, never on E).
Mono configuration (steps in {300, 600, 1200} x l2 in {1e-3, 1e-2}) chosen on the proposed non-Jaaks validation cells only.
Mono labels are winsorised per drug at the training 1/99 percentiles and weighted by inverse drug variance (training only).
Compute is not matched across arms (pretrained arms add mono training); it is disclosed in the run manifest.

## 5. Campaign contract

P2 (frozen): round 1 screens the first ((100-30) x M)//100 of the screen order, round 2 verifies round-1 hits in the
**base ranking's** verification order (identical in every arm), M = ceil(menu/5), no screens in the last round, ties by the
shared rank. Only the round-1 screen score differs between arms. Histories: 4 same-tissue lines (n4), 10 independent draws per
(tissue, outer fold) (not the 3 seeds of earlier studies); HD histories are drawn from HD lines outside the target's fold; E
histories from HD lines.

## 6. Endpoints, inference, classes

* Information estimand: mean within-line Spearman of the screen score vs the two-orientation mean label (`concordance`);
  also AUC for the joint call where defined.
* Decision estimand: measured confirmed discoveries under P2; relative gain with the registered tissue-stratified line
  bootstrap (10,000 resamples, contract seed); the frozen decision function with tau = 5% gives
  HARM / WORTHWHILE_EXCLUDED / UNRESOLVED / SMALL_BENEFIT / BENEFIT_DETECTED / WORTHWHILE (all prefixed EXPLORATORY_).
  "Two of three seeds" is dropped (no discriminating power); replaced by the permutation and scratch-vs-scratch reference
  distributions.
* Swap analysis (purchased screens that differ from the base, confirmed gained/lost) is reported before yield differences.
* Dependence: the line bootstrap is conditional on this drug library; recurring pairs make it too narrow (earlier factor
  about 2.2). A line x pair bootstrap is run for the primary decision contrasts as a sensitivity.
* Power (from `decisions/EVALUATION_DESIGN.md`): at 64 or 61 lines the minimum detectable relative yield effect is about 8-10%;
  a formal exclusion of tau needs more lines than Jaaks has unless the contrast SD is small. UNRESOLVED is a likely class and is
  not evidence of no effect.

## 7. Gates (pre-registered; E opens only if all pass)

* **G1 (mono preflight, held-out Jaaks lines' own GDSC2 labels, tier Y):** pretrained within-cell drug-ranking Spearman exceeds
  the global drug-mean baseline with bootstrap CI > 0, and the within-tissue per-drug Spearman exceeds all 20 permutation
  controls and 0.
* **G2 (own-mono ceiling, HD):** `own_h6` concordance gain over the base ranking with CI > 0. If even the line's own measured
  mono cannot move the ranking, mono-derived information is exhausted for this task and pretraining is stopped.
* **G3 (HD development):** `pre_h6` concordance gain over base and over scratch each with CI > 0, and above all 10 drug and all
  10 cell permutation members.
If a gate fails, E is not read and the stage result is the (qualified, exploratory) negative; HD results are still reported in full.

## 8. Failure handling and invariants

Non-finite mono labels are dropped and counted; pairs with unmapped drugs abstain; no prediction replaces an observed
response; all outcome reads are logged in `access_log.jsonl`; frozen file hashes must match on every read; per-record
poisoning, history-leak and identity tests are in `test_*.py`. No Vis outcome, no API/LLM call, no physical experiment.

## 9. Agent arms

`decisions/AGENT_ROLE.md`: realisable decision headroom is about 1-2% (< tau and < the registered 5%/10% rule); the
deterministic abstention/coverage rule is built into every learned arm (unmapped pairs fall back to the base score). An LLM arm
is gated on a positive development result for the deterministic coupled arm and on written approval, and is **not planned**.
The coupled agent therefore equals the model arm by construction here; this is reported as "no demonstrated headroom".

## 10. Not done / out of scope

Mechanism discrimination; Vis 2024 or any untouched release; new-drug and new-pair generalisation; physical savings;
foundation-model or knowledge-graph embeddings (literature review: no expected benefit, dilutes attribution).
