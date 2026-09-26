# Prediction-to-measurement link: pre-registered evaluation

Frozen on 2026-09-26, before any SciPlex3 episode was run with the repaired selector or the
one-reference forecasts. Parameters are in [`protocol.json`](protocol.json). The SHA-256 of both
files and the freeze time are in `log/20260926/0926/run-notes.md`. A later change is a new
version with its time recorded, never an edit in place.

## 1. What is being tested

The audit (section 3 of [`README.md`](README.md)) found five breaks between the virtual-cell's
predictions and the measurement MAESTRO buys:

1. The power-aware path drops every world-model priority. `from_workspace`, the CLI and the
   public loop all use this path.
2. Per-hypothesis outcome forecasts can reach a selector only as one detection probability, so
   wrong-elimination risk is lost.
3. Cost is compared before any prediction.
4. Per-action queries state the template's exposure time.
5. A thinly supported forecast deletes its action.

The repair is `maestro.acquisition.select_discriminating_action` together with the orchestrator
wiring. This evaluation asks whether the repaired selector makes better **decisions** on the
same episodes, validator, budget and costs as the 2026-09-26 block-2 study. Profile similarity is
not an endpoint.

## 2. Data, held-out unit and what was already seen

The data are the block-2 preparation of SciPlex3:
- A549, K562 and MCF7 at 24 h.
- A549 at 72 h.
- The frozen detection null, validator and per-fold floor/margin calibration.
- The same tiers, folds, episode list and seeded hypothesis order.

**Held out:** compounds, by the frozen five-fold skeleton split, in cell lines that were seen in
training. This is **not** validation on unseen cell contexts.

**Seen before this freeze:**
- Every block-2 result. That includes all block-2 arms and the card audit: 550 of 2,616 tier-A
  menu actions were refused, 13.6% of them would have resolved correctly, and one-reference
  shadow cards had ECE 0.089 (A) and 0.053 (B).
- Phase-B counts taken from block-2 records: step-2 wrong shares among eliminations and the
  `dyn_model` forecast-driven outcomes.

The repair's one-reference rule and its wrong-risk gate were designed knowing that the refusal
caused block 2's loss. **This evaluation therefore cannot support promotion; it can support
SHADOW at most.**

No SciPlex3 outcome has been computed with the new selector or the one-reference forecasts.

## 3. Forecasts (the world model's per-hypothesis output)

For each fold and tier, condition and contrast, each hypothesis's branch comes from the training
compounds of that class measured at the condition. Each such reference is read by the frozen
validator, leave-one-out, against the other class, and the reading is mapped to the four
registered labels:
- `profile_matches_h1` (removes h2);
- `profile_matches_h2` (removes h1);
- `profile_unresolved` (removes nothing);
- `no_detectable_response` (removes nothing).

Support is the number of references. The support rules differ by forecast version:
- **v2 (repair):** zero references is a named refusal; one reference is served, flagged
  `low_support` and shrunk by the Jeffreys prior.
- **v1 (block 2):** fewer than two references is a refusal.

What a label removes comes from the registered rules, never from the forecast.

## 4. Arms

All arms are deterministic and share the same validator, the evidence path through
`InterpretationTable` and `EvidenceState`, the budget of two measurements taken one at a time,
the stop at the first elimination, and the utility: +1 correct, 0 undetermined or deferred,
−2 wrong. Each measurement costs 2 treated wells plus 4 vehicle wells per new line and time, and
takes 6 days at 24 h or 8 days at 72 h.

| Arm | Selector | Forecast input |
|---|---|---|
| `cost_only` | `BudgetedEvidenceSelector`, no priorities | none (zero arm) |
| `production_before` | `select_expected_coverage`, priorities dropped (power-aware path before the repair) | none |
| `production_after` | `select_expected_coverage` with magnitude priorities (power-aware path after the repair) | magnitude |
| `magnitude` | `BudgetedEvidenceSelector` with magnitude priorities (block 2's "current MAESTRO") | magnitude |
| `ec_cards_2ref` | `select_expected_coverage`, detection power = pooled p_correct (block-2 `separation`) | v1 |
| `ec_cards_1ref` | the same selector | v2 |
| `da_2ref` | `select_discriminating_action` | v1 |
| `da` | `select_discriminating_action` (**the repair**) | v2 |
| `da_permuted` | `select_discriminating_action` | v2 with class labels permuted among training compounds (block-2 seed) |
| `da_dynamic` | `select_discriminating_action`; step 2 conditioned on the step-1 reading category (block-2 `dyn_ref` rule) | v2 |
| `fixed` | tier B: 10 µM A549 then MCF7; tier A: 10 µM 24 h then 72 h | none |
| `oracle` | hindsight best sequence | — |

Magnitude priorities are those of block 2: five nearest training structures, with a 72 h query
refused as in the served rung. They are the last tie-break inside every `da` arm, as in the
runtime.

## 5. Endpoints

**Primary (P-A).** The correct-decision rate at budget 2, `da` minus `magnitude`, in tier B and
in tier A separately. Intervals are 95% skeleton-clustered bootstrap intervals (2,000 draws,
seed 20260926), paired on episodes.

**Secondary:**
- **S1:** `production_after` minus `production_before`: correct-decision rate and utility, per tier.
- **S2:** the selector effect, `da` minus `ec_cards_1ref`, and the support effect, `da` minus
  `da_2ref`.
- **S3:** `da` minus `ec_cards_2ref`.
- **S4:** `da` minus `fixed` (tier A).
- **S5:** `da_permuted` minus `magnitude`, and `da` minus `da_permuted`.
- **S6:** `da_dynamic` minus `da`.
- **Every arm:** wrong-elimination rate, utility, regret against the oracle, deferral rate,
  measurements, days, wells, days to the first elimination, action distribution by time, dose
  and line at steps 1 and 2, and per-class correct-rate differences for `da` against `magnitude`.
- **Calibration:** over every step-1 menu action with a served v2 forecast, the pooled
  shrunk P(correct) against whether the validator would eliminate correctly for that compound
  there. Report ECE (10 bins) and Brier, both pooled and on the true hypothesis's branch.
  Report means by support stratum (1, 2–3, 4–8, more than 8). Report whether the realized mean
  discrimination is at least the mean one-sided lower bound in each stratum.

**Consistency checks** are equalities of code paths, not results. If one fails, it is a defect
and is fixed before any result is read.
- `production_before` equals `cost_only`.
- `production_after` equals `magnitude`.
- `ec_cards_2ref`, `fixed` and `oracle` reproduce the block-2 `separation`, `fixed` and `oracle`
  finals episode for episode.

## 6. Classification (decided before the run)

- **PROMOTE** is unavailable from these data (section 2).
- **SHADOW** if every one of these holds:
  - P-A is positive, with the interval excluding zero in at least one tier, and the other tier's
    lower bound is above −0.02.
  - `da`'s wrong-elimination rate is no more than 0.02 above `magnitude`'s in each tier.
  - The utility difference against `magnitude` does not have an interval entirely below zero in
    either tier.
  - `da_permuted` falls short of `da`'s gain over `magnitude` in every tier where `da` gains.
  - Served-forecast ECE is at most 0.10 in each tier.
- **REJECT** if either of these holds:
  - P-A is negative with the interval excluding zero in either tier.
  - `da`'s wrong-elimination rate is more than 0.02 above `magnitude`'s in either tier.
- **INCONCLUSIVE** otherwise.

**The wiring repair (S1)** stays in the runtime if `production_after`'s utility exceeds
`production_before`'s with the interval excluding zero in both tiers. Its change in the
wrong-elimination rate is reported beside that result. It restores the tie-break semantics the
runtime already documents for the non-power-aware path, so it is kept or removed on this rule
alone. The discrimination selector stays opt-in (`discrimination_selection=True`) unless
promoted.
