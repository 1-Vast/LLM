# Block N protocol: where does an LLM add value to a virtual cell?

Registered 2026-10-11, before any confirmation value was read. The machine-readable form is
`PROTOCOL_CONFIG.json`. `FREEZE.json` hashes this file, the config, all code, the development
receipts, the literature store and every agent output that existed at the freeze. The question and
design intent are in `PROBLEM.md`; the development trail is in `feasibility/README.md` and
`development/`.

## 1. Question and claims

Can the dual core predict *which* cancer lines a compound kills (PRISM 19Q4, 578 lines, 2.5 uM),
and does the LLM add anything that the virtual cell and strong non-LLM methods do not?

* **Virtual cell (VC), `L`.** Transfer from the 5 reference drugs with the most similar L1000
  responses (GSE92742, 9 lines x 6/24 h, 10 uM).
* **Agent: frozen flash prompts, thinking off.** Every arm uses the novel-class regime: same-class
  references are removed from the pools and from the agent's vocabulary.
  * Forecaster: `route_lit` (literature), `route_nolit` (no literature).
  * Critic: `adjudicate_lit` judges the VC's 10 nearest transcriptional neighbours.
  * Explainer: `explain_full` sees the top and bottom 20 of 40 discovery lines, proposes genomic
    features, and is scored on 281 unseen test lines.
  * Trust: the critic's keep count and expected killing are combined with the VC's own similarity
    to rank which VC predictions to act on.
* **Strong non-LLM comparators:**
  * target kNN `T` (Hub target Jaccard);
  * chemical kNN `C` (Morgan, r=2, 2,048 bits);
  * the z-mean ensemble `E` of L, T and C;
  * the annotated class mean `A` (known class);
  * mining of the drug's own partial screen: top-5 features or RidgeCV on 40 or 160 discovery
    lines.
* **Zero arm.** The generic profile `G` (mean reference profile) scores selective r = 0 by
  construction. A random trust ranking scores the mean utility.

## 2. Units and tiers

* **Units.**
  * 421 confirmation drugs (split within mechanism class, seed 20261011; `SPLIT.json`).
  * Their PRISM primary and secondary profiles are in the sealed tier
    (`block_n_prism_sealed.npz`, sha 7b94a735...).
  * `tiers.load("sealed")` refuses with `TIER_SEALED` until FREEZE.json exists.
* **Reference pool at confirmation.** The 701 reference + 281 development drugs (982). Development
  used the 701 reference drugs only.
* **Populations.**
  * *Killers*: confirmation drugs with log fold change < -1 in >= 5% of lines. Expected ~103 from
    the development rate of 69/281. Used for the prediction, own-screen, agent and secondary
    contrasts.
  * *All* 421 confirmation drugs: used for the trust contrasts.
* **Endpoint.** Selective r: Pearson r over lines after residualising prediction and observation
  against `G`. Own-screen and explainer contrasts use Pearson r on the 281 test lines between
  prediction and the residualised observation.
* **Secondary screen.** An independent re-screen of the same compound (different plates and run),
  at the dose closest to 2.5 uM. Used for killers with >= 50 secondary lines.

## 3. Registered contrasts, predictions and decision rule

* **Bootstrap.** Each contrast is a mean of paired per-drug differences, or for trust a difference
  of whole-sample statistics. Mechanism-class cluster bootstrap, 4,000 draws, seed 20261011.
* **Family-wise level.** Bonferroni within each family: 8 VC contrasts and 7 agent contrasts,
  alpha 0.05, so two-sided 99.375% and 99.29% intervals.
* **Verdicts.**
  * PASS: lower bound > 0.
  * HARM: upper bound < 0.
  * NOT_SUPPORTED: otherwise.
* **Missing predictions.** A missing or undefined prediction scores 0.

How the predictions in the table were set (`prereg_power.py`):
* The development estimate is treated as the true effect.
* Its standard error is shrunk to the expected confirmation count.
* The prediction is the most probable verdict. It is a forecast, not part of the rule.

| id | claim | contrast | development (n=69 killers / 281 drugs) | P(PASS) / P(HARM) projected | predicted |
|---|---|---|---|---|---|
| V1 | VC beats target transfer, unseen class | `novel_class:L` − `novel_class:T` | +0.118 [+0.069, +0.171] | 1.00 / 0.00 | PASS |
| V2 | VC beats chemical transfer, unseen class | `novel_class:L` − `novel_class:C` | +0.118 [+0.061, +0.178] | 0.98 / 0.00 | PASS |
| V3 | VC alone beats the L+T+C ensemble, unseen class | `novel_class:L` − `novel_class:E` | +0.058 [+0.024, +0.096] | 0.88 / 0.00 | PASS |
| V4 | VC adds to the class mean, known class | `known_class:A+L` − `known_class:A` | +0.030 [+0.005, +0.062] | 0.41 / 0.00 | NOT_SUPPORTED |
| V5 | unseen-class VC beats ridge on a 40-line partial screen | `own:Lnovel_test` − `own:ridge@40` | +0.057 [−0.001, +0.117] | 0.34 / 0.00 | NOT_SUPPORTED |
| V6 | unseen-class VC adds to ridge on a 160-line partial screen | `own:Lnovel+ridge@160` − `own:ridge@160` | +0.049 [+0.017, +0.083] | 0.81 / 0.00 | PASS |
| V7 | VC beats target transfer on the independent secondary screen | `secondary:L` − `secondary:T` | +0.126 [+0.067, +0.188] | 0.99 / 0.00 | PASS |
| V8 | VC's own similarity selects its better predictions | top-25% utility by `top_sim` − mean utility | +0.115 [+0.056, +0.183] | 0.94 / 0.00 | PASS |
| A1 | forecaster beats target transfer, unseen class | `agent:route_lit` − `novel_class:T` | +0.016 [−0.035, +0.060] | 0.03 / 0.00 | NOT_SUPPORTED |
| A2 | forecaster adds to the VC | `agent:L+route_lit` − `novel_class:L` | −0.014 [−0.031, +0.001] | 0.00 / 0.28 | NOT_SUPPORTED |
| A3 | literature improves the forecaster | `agent:route_lit` − `agent:route_nolit` | −0.004 [−0.020, +0.013] | 0.00 / 0.02 | NOT_SUPPORTED |
| A4 | critic of the VC's neighbours beats the VC | `agent:adjudicate_lit` − `novel_class:L` | −0.060 [−0.103, −0.021] | 0.00 / 0.80 | HARM |
| A5 | explainer beats top-5 mining on the same 40 lines | `agent:explain@40` − `own:top5@40` | −0.027 [−0.053, −0.003] | 0.00 / 0.48 | NOT_SUPPORTED |
| A6 | explainer adds to the unseen-class VC | `agent:Lnovel+explain@40` − `own:Lnovel_test` | −0.024 [−0.049, +0.000] | 0.00 / 0.36 | NOT_SUPPORTED |
| A7 | agent judgement improves the VC's trust ranking | AUCC(`vc+agent`) − AUCC(`vc`) | +0.004 [−0.004, +0.019] | 0.04 / 0.00 | NOT_SUPPORTED |

Development intervals in the table are 95%. All development values come from the rehearsal
`rehearsal/dev_llm/RESULTS.json`, which reproduces the development receipts exactly.

**Headline rules (fixed now):**
* *VC value confirmed* if V1 and V6 both PASS.
* *Agent value shown* if any of A1-A7 PASSes. Any HARM is reported as harm.
* No other contrast can change either headline.

## 4. Controls

* **Outcome poisoning (negative control).**
  * Every query's primary and secondary profile is permuted across lines (seed 1), without the
    agent, so the explainer never sees a poisoned screen.
  * Rehearsed on development drugs (`rehearsal/dev_poison1/`): all eight VC contrasts
    NOT_SUPPORTED, estimates within ±0.008.
  * `verify.py` repeats it on the confirmation tier. Any PASS there invalidates the run.
* **Leakage.**
  * The agent never sees a viability value except the explainer's 40 discovery lines, which are
    excluded from scoring.
  * Retrieved abstracts mentioning PRISM, Corsello, Repurposing Hub, DepMap or Dependency Map were
    dropped at retrieval. `verify.py` rescans the stored abstracts.
  * Memorised knowledge of the PRISM release cannot be excluded. It could only inflate agent
    scores; in development, masking the drug name changed nothing (route_nolit − masked_nolit
    −0.008 [−0.030, +0.017]).
* **Identity.**
  * Agent outputs are cached by drug. No confirmation drug has an output before the freeze
    (checked by `verify.py` against the freeze manifest and each record's `created_utc`).
  * Development outputs are hashed and must not change.

## 5. Not registered, and why

* **Capability (thinking mode, pro).** Development only, on the 69 development killers:
  * flash_think and pro changed no forecaster or explainer result;
  * pro's critic beat flash's critic on 14 drugs (+0.095 [+0.009, +0.216]) but did not beat the VC
    (−0.007 [−0.072, +0.046]).

  A pro critic on ~103 confirmation killers would cost ~$3.6 at ~$0.035 per call, over the
  remaining budget. The lead is reported as unresolved.
* **Known-class VC alone vs class mean.** In development, `known_class:L` (0.177) equals `A`
  (0.180). The VC's distinct value is expected only for unseen classes (V1-V3) and as a complement
  (V4). This scope statement is reported descriptively.
* **Explainer at 80 and 160 lines, explainer without VC evidence, prior-only explainer.**
  Development only (`development/explain_pilot.json`). No arm beat mining.

## 6. Disclosures (exposure before the freeze)

* **Shaped by development data.** The contrasts and both headline primaries were chosen after
  development results, all on open drugs.
  * During the rehearsal, V4, V5 and A6 were redefined: the known-class-L versions were replaced
    by an `A+L` contrast and by unseen-class own-screen versions.
  * `V1, V5` was replaced by `V1, V6` as the headline after the power projection.
* **Development exposure.** The trust probe, capability ablation and explainer pilot read every
  development profile, and those drugs now join the reference pool.
* **Literature.** Confirmation drugs' literature was retrieved before the freeze, from text only
  (no viability values).
* **Not blind.** The registering analyst saw development results. Confirmation values are unseen.

## 7. Costs

* **Lab units.** None purchased. All inputs are local public files.
* **Provider spend.**
  * Before the freeze: $6.22 of the $10 block ceiling (`tmp/mechanism_routing_spend.json`; pro
    calls booked at reservation).
  * Confirmation (expected): 842 trust-arm calls + ~103 `route_nolit` + ~103 explainer calls at
    flash rates, about $1.3.
  * The ledger refuses calls past the ceiling. Any refusal is reported as a missing prediction
    (scored 0).

## 8. Procedure

```
python research/astra/mechanism_routing_20261011/freeze.py           # writes FREEZE.json once
python -W ignore research/astra/mechanism_routing_20261011/evaluate.py --tier sealed
python -W ignore research/astra/mechanism_routing_20261011/verify.py  # writes VERIFIED.json
```

The sealed evaluation runs once. Any rerun or change after the freeze is logged in
`DEVIATIONS.json`.
