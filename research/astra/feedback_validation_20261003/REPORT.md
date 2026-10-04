> **File summary**
> - **Path**: `research/astra/feedback_validation_20261003/REPORT.md`
> - **Purpose**: main report of the 2026-10-03 continuation (`../NEXT_RESEARCH_PROMPT_20261003.md`).
>   It covers four audit workstreams and one pre-registered primary experiment on untouched data:
>   does in-context feedback produce more independently validated combination-synergy discoveries
>   than the strongest static alternative? It also reports the exploratory follow-ups.
> - **Core points**:
>   - Primary verdict (Jaaks 2022, untouched; validation on disjoint plates): **NO_MEANINGFUL_GAIN**.
>     Feedback found 274.5 validated discoveries against 277.5 for the best static arm, G = −1.1%
>     [−4.0, +1.4].
>   - Feedback raises screen-level calls by about 3% on every screen. The decisions it changes buy
>     candidates that are worse on the independent measurement. The drug-in-line effects it learns
>     do not transfer across orientations (cross-orientation R² < 0).
>   - Single-agent "context" is not cheap predecision state, and DepMap state fails its gates.
>     Certificates are valid but not useful as nomination lists. The LLM planner's failure is an
>     id-format artefact; its picks follow presentation order and displayed scores.
>   - Spending part of the budget on verifying screen hits gives 238.5 measured-confirmed
>     discoveries at equal measurements (exploratory). Feedback adds nothing there either.
> - **Interfaces / data**: `protocol/` (protocol, freeze, vault log), `results/`, `workstreams/`,
>   `ADDENDUM_certified_discovery.md`, `RUN_MANIFEST.json`, `NEXT_PROTOCOL.json`.
> - **Depends on**: `research/certified_discovery/` (frozen world model and loop, imported
>   unchanged), `tools/datasets/combination_screens.py` (vault).

# Does feedback produce more independently validated discoveries?

## 1. Answer

No, not on the evidence that qualifies. On an untouched screen, a world model that learns from
the target line's own purchases did not find more independently validated synergies than
static retrieval at equal wells. The verdict, registered before the data were opened, is
NO_MEANINGFUL_GAIN, both against the best static arm and against the pre-specified comparator.

The gain this repository reported earlier is real only on the measurement it learned from:

- feedback adds about 2–15% screen-level hits on O'Neil, ALMANAC and Jaaks;
- it survives a change of single-agent reference when the combination wells are shared (ALMANAC,
  exploratory, +3.1%);
- it disappears when the second measurement is fully independent (Jaaks, disjoint plates, swapped
  drug roles).

The decisions feedback changes trade reproducible synergy for measurement-specific signal.
This is a credible negative result for the feedback component as built.

## 2. What was executed, and what was not

| Kind | Item | Status |
|---|---|---|
| Audits (four subagents) | WS1 feedback/validation, WS2 state/legality, WS3 certification/costs/chronology, WS4 agent/literature | Executed; receipts in `workstreams/` |
| Pre-registered retrospective replay | Jaaks 2022 primary: 125 lines × 2 swap replicates, 14 arms, two budgets | Executed once; vault opened at 21:55:18 against freeze `56286578…de1c` |
| Secondary, registered | Authors' validation rescreen (S11); exploratory ALMANAC re-referencing (E1) | Executed |
| Post hoc (after the verdict, labelled) | Cross-orientation transfer of learned effects; swap analysis; verification-allocation follow-up | Executed; each logged in the vault log |
| API tests | WS4 cardinality diagnosis on O'Neil (117 calls, USD 0.2171); LLM gate test (312 calls, USD 0.1384) | Executed; total USD 0.3555 |
| Development runs | O'Neil parity at 10% and 20%; synthetic dry runs | Executed |
| Physical experiments | none | Not run; nothing here is wet-lab evidence |
| Untouched cross-lab replication | AZ–Sanger DREAM (Synapse account needed), Nair et al. 2023 (not downloaded or verified) | Blocked or not attempted |
| STATE model | Not used: no qualifying predecision-state input contract for these screens | Gate failed (section 7.3) |

## 3. Audit findings that changed the plan

The full corrections to the earlier report are in
[ADDENDUM_certified_discovery.md](ADDENDUM_certified_discovery.md).

- **Receipts reproduce exactly.** All arm totals match (WS1). Certificate records match 1,911/1,911
  on O'Neil and 2,940/2,940 on ALMANAC (WS3).
- **Feedback is purely drug-in-line.** Updating only the line offset buys exactly what the static
  model buys under mean ranking (39/39, 60/60 and 250/250 records). The ALMANAC H1 gain splits
  into +2.45 per line from a better static prior, +2.15 from feedback and −2.02 for the audit.
- **The label shares its reference with the feedback signal.** O'Neil's label is
  100·(1 − expected) − 100·observed, and the expectation comes from single-agent measurements
  reused for every pair in a line. Re-scored on single-agent replicates the model never saw,
  wm_full − history fell from +2.05 to +0.17 [−0.53, 0.85] per line (WS2).
- **No experiment in ALMANAC has an independent second centre.** Within-centre repeats correlate
  at r = 0.29–0.50. O'Neil and ALMANAC agree at r = 0.11 on 1,230 shared triples, matching Zhang
  et al. 2023 (r = 0.12). Cross-study overlap is useless as validation.
- **The confirmatory chronology holds.**
  - The "about 18:05" in the invalid run's note was a clock-estimate slip. Spend records place the
    run at 17:47:49–17:48:49, before the 17:58:20 freeze.
  - All 18 frozen digests still match.
  - Before the vault opened, only design columns of ALMANAC had been read.
- **An untouched qualified screen exists** (WS1): the Jaaks et al. 2022 anchored screen, where
  every pair is measured in both drug orientations.

## 4. Primary experiment (pre-registered)

### 4.1 Design

- **Data.** Jaaks et al. 2022, Nature 603:166, figshare 16843597 (SHA-256 `1188968c…a278`). Before
  the freeze only the header, design columns and one accidentally printed row (disclosed) had been
  read.
- **Plate-disjoint validation.** Each plate holds one cell line, all anchors and a fixed doublet of
  titrated library drugs. A seeded split of the doublets into S and V gives each S × V pair two
  measurements on disjoint plates:
  - screen: the S drug anchored, the V drug titrated;
  - validation: the V drug anchored, the S drug titrated.
  - Zero mixed plates were asserted (`receipts/plate_design.json`).
  - The swap replicate (VS) reverses the roles on the same menu, and each line's value is the mean
    of the two replicates.
- **Second-agent review.** A first design (a per-pair orientation coin) was reviewed and rejected
  before the freeze, because plates shared screen and validation measurements of different pairs.
  Nine further fixes followed (`protocol.json`, "review").
- **Menu, budget and unit.**
  - The menu is 153–168 pairs per line, in 125 lines (51 breast, 45 colon, 29 pancreas).
  - The budget is 20% of the menu in 4 rounds, so about 31–34 purchases per line, with 10% as a
    sensitivity analysis.
  - The unit is the target line.
- **Labels and calls.** The authors' synergy rule decides calls. The screen label agents learn from
  is the maximum over anchor concentrations of ΔEmax × 100. History comes from other lines of the
  same tissue, in the screen orientation only. Context is off.
- **Arms:**
  - random;
  - static retrieval by pair mean label (history_mean) and by pair call rate (history_rate);
  - ridge and GBM static models;
  - feedback (the frozen empirical-Bayes in-context posterior with mean ranking);
  - offset-only feedback;
  - feedback on the retrieval prior and on the GBM prior;
  - a call-rate learner with feedback (rate_feedback);
  - a within-round residual-shuffle control and a wrong-line control;
  - two oracles.
- **Primary contrast and verdict rule.** Validated discoveries (screen call AND validation call):
  feedback against static*, the static arm with the most validated discoveries, re-selected in
  every resample. The interval is a stratified line bootstrap (10,000 resamples, seed 20261003).
  - The meaningful gain is G ≥ 10%, justified by the 4× elapsed time feedback needs and by the
    development evidence.
  - A stop verdict also requires agreement against history_rate.

### 4.2 Results (`results/jaaks_primary/verdict.json`)

| Arm (20% budget, 125 lines) | Screen hits | Validated | Wells |
|---|---:|---:|---:|
| oracle (validated) | 590 | 324 | 80,297 |
| history_mean (static\*) | 694 | **277.5** | 80,738 |
| ridge_static | 692.5 | 277.0 | 80,696 |
| offset_only | 692.5 | 277.0 | 80,696 |
| history_feedback | 722 | 275.5 | 80,528 |
| **feedback** | **721** | **274.5** | 80,535 |
| rate_feedback | 716.5 | 273.0 | 79,933 |
| history_rate | 700 | 272.5 | 80,276 |
| gbm_feedback | 703 | 264.5 | 80,416 |
| gbm_static | 673 | 262.5 | 80,458 |
| shuffle control (10 seeds) | 668.2 | 260.8 | 80,714 |
| wrong-line control (10 seeds) | 650.6 | 256.7 | 80,844 |
| random (20 seeds) | 203.4 | 65.4 | 81,580 |

| Estimate | Value |
|---|---|
| **Primary: feedback vs static\* (re-selected)** | **G = −1.1% [−4.0, +1.4]**; −0.024 [−0.088, 0.032] per line; static\* is history_mean in 73% of resamples |
| vs pre-specified history_rate | +0.7% [−2.5, +4.1] |
| Two-way bootstrap, lines × pairs (S13) | [−6.6, +3.5] |
| **Verdict** | **NO_MEANINGFUL_GAIN** (both comparators) |
| S1 screen hits vs best static | **+3.0% [0.3, 5.4]** (721 vs 700) |
| S3 mean validation label of purchases | −0.30 pp [−0.44, −0.16] |
| S2 validation rate of screen hits | feedback 0.381, history_mean 0.400, random 0.321 |
| S4 feedback − shuffle; S4c feedback − wrong line | +5.3% [2.9, 7.7]; +6.9% [4.0, 9.9] (both controls are worse than static) |
| S5 offset-only = static | 250/250 records |
| S6 validated and efficacious (viability ≤ 0.5) | −1.1% [−4.0, +1.3] |
| S7 per tissue | breast +2.5% [−5.3, 9.1]; colon −3.5% [−10.5, 1.0]; pancreas −1.1% [−4.3, 1.2] |
| S8 10% budget | −2.3% [−7.1, +2.0] vs history_rate |
| S9 feedback on retrieval / GBM priors | −0.7% [−4.0, 2.3]; +0.8% [−3.0, 4.7] |
| S12 rate_feedback − history_rate | +0.2% [−2.8, 2.9] (10% budget: +3.6% [0.2, 7.3]) |
| S14 strict-majority calls | −1.4% [−4.7, +1.2] |
| S11 authors' rescreen (selective) | rescreen confirmation ~0.62 for every arm; feedback 423 vs history_rate 433 confirmed screen hits |

Other run details:
- QC excluded 0 of 296,707 rows (the release is already QC-filtered).
- Wells are equal within 0.3%.
- The stage took 32.6 s on 16 workers, plus 17 s for the verdict.

### 4.3 Why (post hoc, after the verdict; `results/posthoc_*.json`)

- **The learned effects do not transfer.** Drug-in-line effects fitted on all screen measurements
  of a line explain 31–40% of that orientation's within-line residual variance. Their correlation
  with the effects fitted on the other orientation is only 0.16–0.36, and as predictors of the
  other orientation's residuals their R² is −0.03 to −0.05.
- **The changed decisions are worse on validation.** Compared with the experiments history_mean
  bought instead, the experiments only feedback bought had:
  - a higher screen-call rate (8.3% vs 5.4%);
  - a lower validation-call rate (4.6% vs 8.3%);
  - a lower mean validation label (3.6 vs 4.8).
  The comparison with history_rate and ridge_static, and the 10% budget, give the same pattern.

**Strongest alternative explanation.** A drug's synergy tendency may depend on its role, anchored
at a fixed dose or titrated, so the swap measures partly different biology. Three facts weigh
against this being the whole story:
- the static arms' picks validate better under the same swap;
- the authors' rescreen, a separate later experiment at different concentrations, also shows no
  feedback advantage;
- the ALMANAC result (section 5) is consistent with a plate-level, measurement-specific signal.

The design cannot separate role-specific biology from plate-specific noise.

## 5. Exploratory: ALMANAC against an independent single-agent reference (E1)

This is exposed data, so the result carries no verdict. The label was re-referenced to single
agents from a different test date of the same screening centre. The provenance check covered 2.87 M
records: NCI's reference was same-plate or same-date singles for all but 3 of them. Combination
wells remain shared. 7.4% of experiments lack a reference and are reported, never imputed.

At the 20% budget:
- feedback has 3,732 validated against 3,619 for history_rate, +3.1% [0.5, 5.9];
- feedback against history_mean is +6.1%;
- the validation rate is about 0.59 in every arm, random included.

So on ALMANAC the small feedback gain is not an artefact of the single-agent reference. It does,
however, still share the combination wells with the label it learned from.

## 6. Exploratory: screening vs verification at equal measurements (`results/followup_verification.json`)

| Policy (measurements = primary wells) | Verified discoveries (both orientations measured and synergistic) |
|---|---:|
| screen only (static or feedback) | 0 measured-confirmed; 277.5 / 274.5 would validate, unknown to the lab |
| static ranking, verify screen hits as found | 238.5 (573 verification measurements, 14%) |
| feedback ranking, verify screen hits | 237.5 (−0.4% [−4.0, 3.4] vs static) |
| measure both orientations of every pair | static 205.0, feedback 209.0 (+2.0% [−2.4, 6.8]) |

Verifying hits beats measuring every pair in both orientations by +16% [12, 21]. At about 14% of
the measurements, the lab gets 238.5 confirmed discoveries instead of 694 unconfirmed claims of
which about 40% hold. Feedback still adds nothing.

## 7. Answers to the seven questions

### 7.1 Was a qualified task or dataset found, and for which estimand?

**Answer.** Yes. The Jaaks 2022 anchored screen (125 lines, complete S × V panels, two
measurements per pair on disjoint plates, untouched before the freeze) supports the estimand
"validated discoveries per target line found by a policy at equal wells, with a within-lab,
plate-disjoint, role-swapped second measurement". It does not support cross-lab or in vivo
replication.

| | |
|---|---|
| **Evidence** | `receipts/plate_design.json`; vault log; WS1 census |
| **Uncertainty** | Pairs recur across lines (handled by the S13 two-way bootstrap). Validation shares the lab, campaign and cell stocks |
| **Strongest alternative** | Swapping drug roles changes the biology, not only the noise |
| **Next experiment** | The same frozen pipeline on a second untouched anchored screen with both orientations, e.g. Nair et al. 2023, after a design qualification |
| **Scope** | Breast, colon and pancreas lines of the GDSC combination screen and its drug library |

### 7.2 Did feedback improve prediction, action comparisons, selections and validated yield?

**Answer, link by link:**
- **Prediction:** no, on average. At the final round on untested candidates, r went 0.503 → 0.520
  on O'Neil and 0.577 → 0.529 on ALMANAC, with RMSE worse (WS1).
- **Action comparisons and selections:** yes, they change. Purchases overlap 70–77% with the
  static arms.
- **Screen yield:** yes, about +2–3% on ALMANAC and Jaaks and +9–15% on O'Neil.
- **Validated yield:**
  - no on the untouched screen (−1.1% [−4.0, +1.4]);
  - not on O'Neil when re-scored with independent single agents;
  - +3.1% on ALMANAC with a new single-agent reference (exploratory; combination wells shared).

| | |
|---|---|
| **Evidence** | Sections 4–5; WS1; WS2 |
| **Uncertainty** | The primary interval excludes gains above +1.4% (+3.5% under the two-way bootstrap) |
| **Strongest alternative** | Role-specific biology (section 4.3) |
| **Next experiment** | Replicate-aware feedback, which separates orientation- or plate-specific effects from shared drug-in-line effects using purchased verification measurements, tested on a fresh screen against the verify-hits static policy (`NEXT_PROTOCOL.json`) |
| **Scope** | Frozen `TransferWorld` (context off), mean ranking, 4 rounds, 10–20% budgets |

### 7.3 Did genuine inexpensive state add value beyond background and feedback?

**Answer.** Not established; the gate failed.

- **Single-agent "context" is not predecision state.** It is a functional measurement, it is
  uncharged (0.3–2.9× a campaign's records), and it is coupled to the label:
  - on O'Neil, `expected` is the label's own subtrahend;
  - on ALMANAC, it was pooled from plates of unbought combinations.
  Removing it changes nothing on O'Neil: ±0.33 hits per line, and every interval includes 0.
- **DepMap baseline state fails three gates:**
  - there is one profile per line, so state equals identity;
  - it was released in 2024, after both screens;
  - it comes from a different lab.
- **Bounded O'Neil diagnostic** (weighting history lines by expression):
  - +0.26 [−0.09, 0.63] hits per line;
  - against a within-tissue shuffle, +0.25 [−0.05, 0.59];
  - 90% of selections are unchanged.

| | |
|---|---|
| **Evidence** | WS2 `feature_legality.csv`, `coupling_ablation.json`, `state_diagnostic.json` |
| **Uncertainty** | The diagnostic is underpowered for effects below about 0.6 hits per line |
| **Strongest alternative** | Tissue or identity similarity drives the small positive point estimate |
| **Next experiment** | At least 10 backgrounds with at least 2 untreated states each, measured in the same lab before treatment, with matched combination outcomes and a within-background shuffle control |
| **Scope** | O'Neil (35 mapped lines); DepMap 24Q2 |

### 7.4 Did the agent add value beyond strong deterministic alternatives?

**Answer.** Not shown.

- **The confirmatory failure was an id-format artefact.** With 4-digit candidate ids, 0 of 21
  replies returned exactly k ids. With ids of 3 digits or fewer, 20 of 21 did, at the same
  k = 128. Chunks of at most 16 ids worked in 36 of 36 calls.
- **Picks follow presentation, not pharmacology.**
  - With scores shown, the model re-sorts by the displayed score (Kendall tau 0.66).
  - Blind, it copies the presented order (overlap 0.92).
  - On O'Neil, blind mode equalled random within the menu, and named mode equalled the world
    model.
- **Gate test** (`workstreams/ws4_agent_literature/gate_plan.json`, written before the first call;
  O'Neil, 39 lines × 4 rounds, k = 15; 312 calls, all valid on the first attempt; USD 0.1384):
  - With true scores shown, the LLM against deterministic sort-by-score: +0.33 hits per line
    [−0.10, 0.77].
  - With permuted scores, the LLM against "take the first k presented": +0.08 [−0.87, 0.97].
  - 82% of picks are explained by the displayed-score sort, and 94% by order or score.
  - The remaining picks hit at 0.150, against a menu base rate of 0.155.
  - The pre-set rule outputs MODIFY rather than STOP, because the intervals cannot exclude a gain
    of up to about 1 hit per line. No knowledge beyond the displayed numbers is detectable.
  - The plan defined "explained" by the best single rule, which gives 0.82. If "explained by order
    or score" is read as the union of the two rules (0.94), the stop rule would have fired. A
    chance chooser already lands in the union about 75% of the time, which is why the single-rule
    reading was registered.
  - Deviations, disclosed in the plan:
    - the evaluation is one-step: LLM picks do not feed later rounds;
    - `max_tokens` was 600; replies used about 117 tokens and none was truncated.

| | |
|---|---|
| **Evidence** | WS4 `summary.json`, `receipt_audit.json`, gate receipts |
| **Uncertainty** | Public screens may be memorised. Only one provider model (deepseek-flash) was tested |
| **Strongest alternative** | A stronger model might add knowledge. Wainrib et al. 2026 report a feedback effect only for their strongest model |
| **Next experiment** | Only if the gate passes: a matched comparison with an LLM agent with and without world-model information, against deterministic policies (WS4 `agent_comparison_protocol.json`) |
| **Scope** | DeepSeek deepseek-flash, temperature 0, thinking disabled, O'Neil development data |

### 7.5 Were certificates mathematically applicable and practically useful?

**Answer.** Applicable, yes; useful as nominations, no.

- **Why they apply.** The audit is uniform at random inside a shortlist fixed before any audit
  label. That gives finite-population exchangeability, which licenses clipped conformal p-values
  with BH and an exact hypergeometric yield bound per list. Earlier adaptive rounds do not matter.
- **What the guarantee covers.** It is marginal per list, over audit draws. It is not conditional
  on a non-empty list, not simultaneous across lines, not valid under optional stopping (coverage
  falls to as little as 0.83), and not a guarantee of biological replication.
- **Why the nominations are weak.**
  - Only 5.6% of lists are non-empty.
  - A non-empty list has FDP 0.77; BH cannot nominate fewer than 5 candidates when the audit and
    the remainder are each about 128.
  - The best exploiter leaves the sparsest certificate.
- **The yield bound.** It is valid per line, but the summed bound is not a simultaneous
  certificate. Valid aggregates are 82.2 (Bonferroni) and 371.5 (pooled). No certificate changed a
  decision in any run.

| | |
|---|---|
| **Evidence** | WS3 `receipts_metrics.json`, `design_checks.json`, `optional_stopping.json` |
| **Uncertainty** | Empirical checks support the theorem; they are not a proof of it |
| **Strongest alternative** | — |
| **Next experiment** | A terminal decision experiment (buy the remainder or move the budget) comparing a valid pooled bound, the model's claim and a plug-in, on a complete panel (WS3; `NEXT_PROTOCOL.json` part B) |
| **Scope** | Primary-screen labels |

### 7.6 What resource costs were measured, estimated or unknown?

**Measured:**
- combination wells per arm (equal within 0.3%; 14 per Jaaks purchase per plate);
- rounds (feedback 4; any static arm could finish in 1);
- compute: Jaaks stage 32.6 s, ALMANAC stage 105.5 s, core suite 41.6 s;
- provider spend in this continuation: USD 0.3555 for 429 calls (WS4 diagnosis 0.2171 for 117
  calls; gate test 0.1384 for 312 calls), at the ledger's peak rates, against a ceiling of USD 3.
  No retries were needed, and no call went unpriced.

**Estimated:**
- the certify-branch cost difference (−3.4 points per ALMANAC campaign; never recorded by the old
  receipts);
- O'Neil wells, 4× the recorded dose points;
- uncharged context, 0.3–2.9× a campaign;
- verification in the follow-up, about 14% of measurements.

**Unknown:**
- the price per well, labour and plate controls;
- single-agent wells shared on plates;
- days per round for Jaaks;
- the amount actually billed by the provider (the 2026-10-03 holiday off-peak schedule may halve
  it);
- 12 unpriced confirmatory calls from the earlier block (at most about USD 0.07).

### 7.7 What should continue, change or stop, and what remains blocked?

**Continue:**
- the plate-disjoint, role-swapped validation design as the standard test bed for any discovery
  claim;
- verification allocation (verify-hits beat paired measurement by +16% [12, 21]);
- certificates as an audit tool, with valid aggregate bounds;
- static retrieval, run in one round, as the default baseline.

**Change:**
- report every discovery claim at three tiers: screen label, independent reference, independent
  measurement;
- charge context and verification;
- record certify-branch purchases and per-line independent audit seeds;
- give LLMs short positional ids or chunks;
- default to `wm_nocontext`;
- relabel S2b as a kernel-misspecification control.

**Stop:**
- claiming that the in-context empirical-Bayes feedback improves validated discovery;
- the DepMap-state branch on these screens;
- promoting FDR nominations as a decision aid;
- adding model complexity before a replicate-aware feedback test;
- LLM-as-selector comparisons with this model: its picks carry no detectable knowledge beyond
  order and displayed scores (gate decision MODIFY). Revisit only with a stronger model on an
  untouched screen.

**Blocked:**
- cross-lab replication, because the DREAM data need an account;
- a second untouched anchored screen (Nair et al. 2023), not yet qualified;
- any physical experiment;
- STATE, because no qualifying predecision-state input exists.

## 8. Deviations and failures (all recorded)

- **Rate limit.** All four subagents stopped at a session usage limit around 20:08 and were resumed
  with their context at 21:11. No work was lost.
- **Accidental data row.** One data row of the untouched release was printed while reading the
  header. It is disclosed in `protocol.json`.
- **Rejected first design.** The per-pair coin design was rejected by the reviewer before the
  freeze.
- **Budget change.** The primary budget moved from 10% to 20% because the plate-disjoint menu is
  half the size, keeping about 33 purchases per line. This happened before any outcome was read.
- **Guessed timestamps.** The protocol text first carried guessed times (22:05, 22:50). They were
  corrected from file times before the opening, and the two superseded freezes are kept.
- **Parsing fix.** ANCHOR_CONC was parsed with mixed types under chunked reading. It was forced to
  string before the freeze, and the design census was unchanged.
- **Test-summary capture.** An earlier run of the core suite hid its summary line (double `-q`). It
  was rerun with default options: 354 passed.
- **Vault openings.** The vault log has 6 entries: primary, rescreen, ALMANAC E1, two post-hoc
  analyses and the follow-up. Each is labelled with its purpose.

## 9. Reproduce

```powershell
$env:PYTHONPATH = 'src;.'
$py = 'D:/anaconda/envs/maestro/python.exe'
& $py -m research.astra.feedback_validation_20261003.run --stage dry --out NEW_SCRATCH_DIR
& $py -m research.astra.feedback_validation_20261003.run --stage oneil_parity --out results/NEW_DIR
& $py -m research.astra.feedback_validation_20261003.run --stage jaaks --out results/NEW_DIR      # logs a new vault opening
& $py -m research.astra.feedback_validation_20261003.run --stage almanac --out results/NEW_DIR
& $py -m research.astra.feedback_validation_20261003.verdict results/jaaks_primary
& $py -m research.astra.feedback_validation_20261003.posthoc_mechanism results/NEW.json
& $py -m research.astra.feedback_validation_20261003.posthoc_swaps
& $py -m research.astra.feedback_validation_20261003.followup_verification
& $py -m pytest -o addopts= research/astra/feedback_validation_20261003/test_feedback_validation.py
```

Environment and hashes are in [RUN_MANIFEST.json](RUN_MANIFEST.json). Literature claims are
verified in `workstreams/ws4_agent_literature/literature_verification.json`.
