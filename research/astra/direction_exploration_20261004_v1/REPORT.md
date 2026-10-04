# Research direction exploration — 2026-10-04

## Scope and conclusion

Three specialist agents reviewed model contribution, resource-constrained decisions, and data/inference requirements. The parent checked their consequential numerical claims against existing JSON receipts and inspected the acquisition code and probability-calibration implementation. This is an exploration of already exposed results, not a new prediction experiment, confirmation study, API run, or physical experiment. Production code and earlier research artifacts were not modified.

The next executable question should be narrow: **under the same historical information and a fixed feasible campaign, can confirmation-aware prediction beat strong simple rankings in measured confirmation yield?** Before comparing predictors, remove forced expenditure from the new campaign contract and establish the resource/time frontier. A small centered-feedback diagnostic is conditional on this foundation; a new scheduler or LLM arm is not currently justified.

## 1. Information use is not model contribution

The existing discovery totals are S = 252.5, S_both = 263.5, R = 269.0. S uses one orientation's history; S_both and R use both. The primary same-information contrast in the result file is R minus S_both: **+2.09%, historical bootstrap interval [-1.62%, +6.08%]**. The well-budget counterpart is +2.32% [-0.95%, +5.78%]. These are unresolved, not proof of zero or of practically meaningful benefit.

R is already a simple shrunk empirical joint-call rate, not a newly learned complex world model. The reported +6.5% for R minus S measures both extra information and a different ranking target. Relative percentages have different denominators and must not be subtracted as an exact attribution. The absolute increase is 11 discoveries for richer history and another 5.5 for R.

The existing NOT FROZEN `NEXT_PROTOCOL.json` still makes R minus S primary. A new protocol should put the development-selected same-information comparator first; retain R minus S as an information-package comparison. Freeze one primary comparator and report the others as registered sensitivities rather than choosing the weakest after evaluation.

## 2. Budget depletion is not efficient stopping

The parent extracted the following existing receipt values. Counts average the two orientation-role assignments within each line; they are not half of a physical plate being purchased.

| Existing arm | Confirmed | Measurements consumed | Rounds | Assay-only minimum days | Hypothetical custom plates |
|---|---:|---:|---:|---:|---:|
| paired_full_R1 | 214.5 | 3,910 | 1 | 4 | 507.5 |
| fixed_split_dev_R1 | 231.5 | 3,958 | 2 | 8 | 663.5 |
| verify_hits_terminal | 252.5 | 3,958 | 5 | 20 | 1,484 |

The paired arm has 48 unavoidable odd-budget units left, so the historical +17.7% is at equal budget caps, not identical actual consumption. Two-round verify-hits obtains 210.5, below the two-round fixed split's 231.5. The five-round advantage does not establish equal-time efficiency.

Natural one/two-round custom-layout figures differ from the five-round implementations in the main report's cost table. Under this hypothetical model, five-round verify-hits uses 2.24 times the natural fixed split's custom plates. Native plate totals differ again; buying a native plate also produces co-measurements not credited by per-pair replay. Neither layout is an authenticated prospective cost model. Unknown prices, labour, capacity and omitted failures stay unknown.

The two-round fixed split buys **789.5 terminal screens**; five-round verify-hits buys **84**. These cannot be verified before campaign end. If utility is limited to confirmed discoveries within that campaign and no future information utility is registered, these screens add no immediate confirmation yield.

As a receipt-only arithmetic diagnostic, retaining the historical confirmation counts while subtracting those terminal-screen measurement charges gives 231.5 / 3,168.5 versus 252.5 / 3,874: approximately **12.1% higher confirmations per measurement for the fixed split**. This is not a new policy evaluation, and does not establish plate or monetary savings. A new stop policy must be frozen and replayed explicitly, with overhead accounting recomputed.

## 3. There is little demonstrated scheduler headroom

The current index compares screening p_sv/c_s with pending verification p_v_given_s/c_v. A simple screen-plus-verify-all-hits pipeline diagnostic is p_sv/(c_s + p_s*c_v). It accounts for an expected downstream cost omitted from the screen index, but is not a finite-horizon optimal policy.

The omitted cost makes screening look better. Correcting it cannot explain away the observed lack of deferred verification; it would generally favour verification further. Do not take this negative scheduler result as a reason to add an LLM. First show legitimate choices in which probability, cost, deadline or an explicitly valued alternative use makes screening, verification or stopping preferable at different times. Otherwise retain the simple policy.

## 4. Preserve the narrow feedback signal without cherry-picking

The same-condition 14-line R2 receipt reports U_lambda = 9.0 versus U_V0 = 7.5 second-round validated discoveries; its historical exploratory interval is +20% [5%, 42.9%]. The absolute difference is only 1.5, with small samples, multiple analyses, shared history and incomplete lineage authentication. **The same receipt also reports U_screen_post = 9.5**: the positive contrast does not establish that fitted shrinkage beats every available feedback comparator.

Role-swapped feedback improves squared error slightly but not candidate ordering. This does not prove that all feedback is useless. Same-condition repeatability and cross-condition transport are distinct questions. Existing MSE stopping decisions remain unchanged; a new development study may explicitly choose a decision endpoint without retroactively converting the old failure to success.

The implementation already fits a two-parameter logistic mapping (`repeats/model_id.py`, class Mapping). Repeating that step is not a new contribution. If a limited feedback diagnostic remains warranted, separate a line-wide correction from the centered candidate-specific correction and permit zero feedback. Compare F with F0 using identical priors, calibration, acquisitions and resources. F minus R is a useful practical comparison but does not isolate feedback when priors differ. Do not add latent blocks or a large model search.

## 5. Data and power gates must match the question

The 150–180-line recommendation uses proxy contrasts rather than the exact R-versus-S_both contrast. It is a conditional planning approximation, not a universal dataset eligibility rule. Power to demonstrate a benefit above 5% requires a true effect above 5%; one cannot assume the true effect equals the threshold and claim 80% power to exceed it.

Freeze the historical training library separately from evaluation where possible. Keep role assignments paired, account for repeated pairs and shared fitted histories, and declare fixed-library versus new-line/new-pair generalization. A line bootstrap or additional lines alone does not resolve every dependence. Recompute precision for the actual planned contrast; simulation plans evidence, it does not supply measured outcomes.

If full-library confirmation is blocked, investigate a design-defined complete smaller menu, selected-menu cross-protocol prediction, authenticated same-condition repeat diagnostics, or randomized policy evaluation. Nair's selected cross-lab menu and BATCHIE's random validation may support narrower questions after their sampling/design contracts are checked; neither automatically supports unrestricted policy replay. Consult original Methods, supplements and raw design metadata before declaring a dead end.

The original cheap-predecision-state problem remains separate: cell identity, historical responses, single-drug functional probes, untreated baseline state and purchased combination feedback are different information sources. No result here establishes STATE advantage, mechanism identification, or net wet-lab benefit.

## Recommended bounded continuation

1. Freeze a campaign contract: operational confirmation endpoint, two-round primary comparison, budget cap, explicit binding resource, stop action, measured menu and unknown costs. Reconstruct a one/two/three-round resource frontier from existing records; do not tune against new outcomes.
2. On exposed development data, compare R and strong same-information simple rankings under this single campaign. Register at most one centered-feedback candidate if a direct decision-space diagnostic justifies it. Do not run a full predictor-by-scheduler factorial yet.
3. Qualify a genuinely untouched evaluation for the chosen estimand using design metadata first. If unavailable, deliver the executed development result, frozen follow-up design, contrast-specific precision analysis and a precise blocker after bounded recovery attempts.
4. Continue only for credible direct decision headroom. Report unresolved when intervals permit both zero and worthwhile benefit; stop for demonstrated harm or a justified upper bound below the registered worthwhile gain. Missing physical evidence blocks deployment claims, not every lower-tier prediction experiment.

## Evidence and verification

Sources: `../reproducible_allocation_20261003/REPORT.md`, `NEXT_PROTOCOL.json`, `allocation/results/replay.json`, `allocation/results/addendum_3_information.json`, `allocation/receipts/accounting.json`, `allocation/addendum_2x2.py`, `repeats/receipts/phase2_key_results.json`, `repeats/plan.json`, `repeats/model_id.py`, and the review power files. Exact checked source hashes and extracted values are in `EXPLORATION_RECEIPT.json`.

This turn verified source-backed extraction and arithmetic; historical bootstrap intervals were read, not independently refitted. No historical test counts are presented as rerun results. No Git commit or push was made.
