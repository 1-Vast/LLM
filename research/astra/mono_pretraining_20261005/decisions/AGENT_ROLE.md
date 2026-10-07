> **File summary**
> - **Path**: `research/astra/mono_pretraining_20261005/decisions/AGENT_ROLE.md`
> - **Purpose**: design the four policy arms (strong simple; world-model-informed deterministic; agent without world model; coupled agent
>   plus world model) so that extra information, prediction and decision policy are separately identified; state the agent headroom
>   honestly against the registered 5% rule; fix the matched biological budget and a compute/API disclosure template.
> - **Core points**: realisable agent-decision headroom on this task is about 1-2% (perfect-foresight bounds 0.7-3.8% for
>   verification and split, 5.1% only as an unrealisable per-line best-of-two); it is below tau = 5% and below the registered
>   indication rule. The smallest honest agent arm is a pre-registered deterministic abstention/coverage rule; an LLM arm is gated
>   and not planned. A null on the coupled arm means "no decision-policy headroom beyond fallback", not "agents cannot help".
> - **Evidence status**: EXPLORATORY; numbers from `confirmation_campaign_20261004` receipts (see `DECISION_SPACE.md`).

# Policy arms, agent role and budgets

## 1. Common contract for all arms

All arms run the frozen two-round campaign (P2, fp 30, cap M = ceil(menu/5), deadline 2 rounds, QC-conditioned menu, shared tie-break
`numpy default_rng([20261004, tissue, line_index, role])`). Per target line and history draw they receive **identical histories** (the n4
sets of seeds 11, 23, 47 or more, plus n8 and all as transport), identical purchase legality (`Lab`: no re-screen, verify only a
revealed hit from an earlier round, no screens in the last round), identical verification order (the comparator's p_v), and the same
cap. Every candidate in the menu has both orientations measured, so any legal action returns a measured value; nothing is imputed,
an unexecutable action (pair outside the QC menu) is refused, never scored as 0.

Only the **round-1 screen order** differs between arms (and, in the gated P3 sensitivity, the round-2 screen order). This is the
decision where the oracle headroom lives (+28.5% E / +21.9% HD, `DECISION_SPACE.md`).

## 2. The four arms and what each difference identifies

| Arm | Round-1 screen score | Information | Decision rule |
|---|---|---|---|
| **S1 strong simple** | C*: best of {S_both, L_v, C_s, C_v, C_mean, C_prod} chosen on inner folds, plus two matched-information simple comparators declared before any run: **D_add** (anchor and library drug marginal rates and mean labels from the same history, additive, k0 = 2) and **M_pot** (mono-potency prior: tissue-level GDSC2 drug potency, no combo learning). Selection inside outer-training folds only. | history only (M_pot adds public mono) | rank by score, ties by shared rank |
| **W world-model-informed deterministic** | z(C*) + lambda x z(g_line), g = the model's within-line centred prediction (centring removes the line level), lambda in {0, 0.25, 0.5} fixed on inner folds (lambda = 0 is an exact fallback); pair with an unmapped drug has g = 0 (abstention) | history + public mono (via pretraining) + 14 static covariates | the same rule for every line, fixed before any outer read |
| **A0 agent, same information, no model** | chosen by the agent from the simple library (which ranker, fp in {25, 30, 35}), never sees g | history + round-1 reveals (P3 only) | deterministic rule agent first; LLM variant gated (section 5) |
| **A1 coupled agent + model** | agent chooses among {C*, W(lambda in {0.25, 0.5})} and may abstain per line, with g, coverage flags and the reliability record available | A0's information + g | same action space as A0 plus the model option |

Contrasts (all paired by line, all with the same cap):

| Contrast | Isolates | Reading |
|---|---|---|
| W_pre - W_scratch | mono information given architecture, inputs, combo data, steps | transfer value of the mono labels |
| W_scratch - S1 | architecture and combo supervision without mono | prediction effect of the learner |
| W_pre - S1 (**primary**) | what a lab gains by adding mono-pretrained prediction to the best simple ranking | decision-relevant gain |
| W_pre - W_perm (drug / cell, >= 20 permutation draws) | validity of the mono mapping | attribution of gain to biology |
| A0 - S1 | decision policy without a model | agent value from the simple library alone |
| A1 - W_pre | decision policy given the same model output | coupling value |
| (A1 - A0) - (W_pre - S1) | interaction | whether agent and model are worth more than the sum |

The decision-policy contrasts are only meaningful if W_pre - S1 is positive; otherwise A1 can at best equal S1 by falling back.

## 3. Which concrete decision can the agent change, and how much can it move

Numbers are E (HD) from the receipts; all are perfect-foresight bounds unless stated.

| Candidate decision | Mechanism with a model output | Bound | Why it is not worth an agent |
|---|---|---:|---|
| Verification order, verify-all-hits | none: forced when cap is not binding | +1.7% (+0.7%); binding in 4.9% (3.1%) of C_mean campaigns | forced |
| fp (screen share) per line | adaptive split | +3.8% (+3.7%) hindsight-best fp per campaign | a fixed fp chosen on development captures most; needs outcomes to pick |
| Early stop / skip a predicted-barren line | model predicts few hits | zero yield gain; cost saving up to 25% of measurements in perfect foresight (32 of 125 lines have no joint hit) | to save 20% of measurements with <= 5% yield loss it must skip 25 of 125 lines with at most 4.6 non-barren, i.e. >= 81% precision at >= 64% recall of barren lines (non-barren lines average 2.71 confirmed under C_mean, 12.6 confirmed = 5% of the 252 pooled); line-level evidence for such prediction does not exist |
| Per-line reliability-gated blending (pick WM or simple per line from round-1 reveals) | switch ranking after observing round 1 | hindsight best-of-two R vs C_mean +5.1% (E), +2.2% (HD) | cannot be realised: a campaign yields about 2 round-1 screen hits (C_mean: 272 hits over 122 campaigns), and the within-line AUC of a ranking among the eligible round-2 candidates is defined in only 23 of 61 E lines (76 of 122 campaigns undefined); any reliability estimate from purchased candidates only is also selection-biased; P2 has no screens after round 1 anyway |
| Abstain to the simple ranking (unmapped drug, low coverage, out-of-domain) | deterministic coverage rule | 0 by construction (never worse than S1 on abstained pairs) | a rule, not an agent |
| Round-2 screen choice with feedback (P3) | feedback-conditioned ranking | oracle round-2 +10.9-18.8% | realised feedback gain +1.7% [-1.4, +5.3] (post hoc), AUC +0.01, registered NO_RELATIVE_FEEDBACK_VALUE |
| Cross-line budget allocation | line-level propensity from the model | +7.2% (E), +6.2% (HD), perfect foresight of barren lines | needs line-level discrimination far beyond anything measured; exploratory only |
| Cheap target-line mono request | fixed info ablation | not definable (no priced action) | not a decision in these data |

**Verdict against the registered rule.** The rule (choice frequency >= 10% **and** oracle bound >= 5%, `scheduler_rule_definition` in
`resources/results/summary_20261004_130800/summary.json`) is not
met by R, C_mean or S_both at fp 30. The realisable agent gain is <= about 1-2%, which is below the 5% minimum meaningful
improvement. The cross-line allocation and per-line best-of-two bounds exceed 5% only under perfect foresight and are not
supported by any measured predictor. **The honest statement is: there is no demonstrated headroom for an agent beyond a deterministic
fallback on this task.** Prior agent-related findings point the same way: the LLM planner's exact-k failure on Jaaks was an id-format artefact and its picks
followed presentation order and displayed scores (`feedback_validation_20261003/REPORT.md`, summary and section 1).

## 4. Smallest honest agent arm

A0 and A1 are implemented first as one **deterministic rule agent**, written and hashed before any outer-fold read:

1. R1 abstention: any pair with an unmapped drug, a composite intervention (`1032|1372`) or a missing model score uses the S1 score.
2. R2 coverage gate: a line whose mapped-pair fraction is below 0.5 uses S1 entirely (reported as an abstained line).
3. R3 option choice: A1 uses W(lambda) with lambda fixed by the inner-fold rule; A0 uses the inner-fold best simple ranker. No
   learning across lines, so no leakage between evaluation units.
4. R4 (only if W_pre - S1 has L > 0 on development): **interleaved round 1** (alternate top picks of W and S1, de-duplicated) so that
   each ranking's own purchases yield measured hit rates, and a pooled reliability gate across previously completed lines in a
   random order. Interleaving is a different physical policy from the pure arms and is therefore reported as its own row, never
   substituted for W or S1. It avoids scoring the unchosen ranking on outcomes a real lab would not have.

What a null means:

- **A1 - W_pre indistinguishable from 0:** no decision-policy headroom beyond deterministic fallback, in line with the registered
  indication rule. It does **not** show that agents cannot help in other tasks (mechanism discrimination, multi-hypothesis
  planning) that this data cannot test.
- **W_pre - S1 indistinguishable from 0 or negative:** there is nothing to couple; A1 reduces to S1 by fallback and the agent
  question is moot.
- **A0 - S1 indistinguishable from 0:** rule-selected rankers or fp add nothing, as the 3.8% fp bound predicts.

## 5. LLM arm (gated, not planned)

Run only if (a) the deterministic A1 shows L > 0 against S1 on development, **and** (b) the registered indication rule passes on
the new predictor, **and** (c) the parent gives written approval (contract cap USD 3). If run: the LLM chooses only among
enumerated option labels (never free-text pair ids), temperature 0, schema-validated output, abstention allowed, exact model
id and prompt hash logged, one call per campaign decision point, refusal and malformed output counted as fallback to S1. Report
the number of calls, tokens, USD, retries and malformed outputs next to the confirmed-yield contrast; a gain that disappears when
the LLM's options are replaced by a random choice among the same options is not an agent gain.

## 6. Matched biological budget

Identical across arms and reported per arm: cap M (orientation measurements) and spent measurements; round-1 screens, verifications,
unused cap; number of rounds used and minimum days (4 per round); history lines and rows (same sets); mono rows used for pretraining
(declared **information**, not budget); native plates touched, custom plate starts (200 controls per plate documented), combination
wells, controls and shared single-agent wells, with unknown prices, labour and capacity stored as null. Spent measurements may
differ slightly between arms (a ranking that finds more hits buys more verifications); the cap is a cap, not a spending requirement,
exactly as in the confirmation campaign. No arm may buy outside the registered menu or after the deadline.

## 7. Compute and API disclosure template

| Item | Per arm and per history draw |
|---|---|
| Hardware / OS / Python / library versions, thread count | |
| Mono pretraining: rows, entities (drugs, cells), steps, wall-clock, CPU-hours; shared one-time cost, amortisation stated | |
| Combo training: rows, steps, seeds, wall-clock, CPU-hours | |
| Parameter counts and trained-parameter counts (pretrained vs scratch matched) | |
| Hyperparameters selected (inner folds) and number of configurations tried | |
| Inference: scoring time per line | |
| Agent: decision points, rule evaluations | |
| LLM/API (if any): provider, model id and version, calls, input/output tokens, USD, retries, malformed or refused outputs, prompt and response hashes | none planned |
| Failures and exclusions (lines, pairs), with reasons | |
| Code, config, data and checkpoint SHA-256; run start/end timestamps | |

Compute is not matched across arms (the pretrained arm is more expensive by construction); it is disclosed, and any claim of
"better per unit cost" must use the biological cap and the disclosed compute separately, never mixed.
