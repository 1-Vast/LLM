# Measurement choice for mechanism discrimination

Can a virtual cell help MAESTRO's agent choose the **measurement** that separates two competing
mechanisms, for example, tell "the perturbation failed" from "the proposed mechanism is wrong"?
Today the virtual cell enters measurement choice only as a tie-break on predicted response
magnitude. This directory holds the pre-registered test of whether reference-based scenario
cards, a time-aware policy, a learned population transition model, and language-model planners do
better. It was run on 2026-09-26 on SciPlex3 (A549, K562 and MCF7 at 24 h; A549 at 72 h).

The frozen protocol is [`PROTOCOL.md`](PROTOCOL.md) with [`protocol.json`](protocol.json); their
hashes and freeze time (15:19:45 +0800, before any 72 h value or outcome) are in
`log/20260926/0926/run-notes.md`. Every number in the day record comes from the generated report
`outputs/dynamic_world_model_20260926/analysis/report.md`, copied to
`log/20260926/0926/measurement_choice_report.md`.

## Result in one paragraph

No world-model component met its promotion rule, and none is promoted.
- **Separation cards.** Choosing measurements by cards built from measured reference compounds was
  worse than the current magnitude tie-break: correct decisions −0.044 [−0.083, −0.004]. The loss
  comes from deferring when a class had too few references; on the episodes where a card was
  served, the two tied.
- **Time-aware cards.** They did not beat magnitude (+0.054, interval includes zero), and a fixed
  "24 h then 72 h at 10 µM" protocol beat them by 0.190.
- **Learned transitions.** Gene-space ridge predicts a compound's 72 h, other-line or other-dose
  profile far better than carrying the source profile over (time: cosine +0.283). The forecast
  still names the mechanism class no better than persistence does, and using it to plan changed
  nothing (+0.003).
- **Branches versus class mean.** Treating each reference compound as its own outcome branch
  predicts what a measurement will show much better than a single class mean (log loss −0.599).
  The data are heterogeneous within a mechanism.
- **Language models.** Cards did not help DeepSeek (+0.006). Jev with cards reached the card
  policy's outcome in every episode, and Jev without cards mostly deferred.
- **Where the value is.** Knowing that some mechanisms act late: DNA methyltransferase, BET and
  Aurora inhibitors become decisive only at 72 h. The current magnitude rule never chooses 72 h.
  DeepSeek without cards did, and beat that rule in the time tier (+0.190). This last finding is
  post hoc and is the next experiment to confirm.

## Files

| File | Role |
|---|---|
| `prepare_time.py` | One streaming pass: 24 h and 72 h replicate shifts on the frozen gene universe, vehicle wells, cell-cycle scores and cell counts, with the identity-marker guard and a check that the 24 h shifts reproduce the frozen preparation |
| `common.py` | Data loading, the vehicle-well detection null, the frozen validator and its per-fold calibration, the reference scenario cards, and the route of every executed measurement through `InterpretationTable` and `EvidenceState` |
| `episodes.py` | Every deterministic policy (random, fixed, cost_only, magnitude, separation, separation_permuted, dyn_ref) and the oracle, over all registered episodes |
| `transition.py` | Transition arms for time, dose and context transfer, and the fitted forecasts `dyn_model` uses |
| `dyn_model.py` | The step-2 policy that forecasts the held-out compound's own next profile |
| `card_audit.py` | Card calibration over the whole menu, refusals versus shadow estimates, and T5 (branches, single mean, pooled marginal) |
| `agent_arms.py` | DeepSeek and Jev planners under identical evidence and budget, through the spend ledger |
| `repeatability.py` | DeepSeek repeat agreement on 30 first-step states |
| `case_study.py` | The pre-registered anchors and a closed-loop replay through `CaseStore`, with raw counts re-extracted from the release, round records, and a failed-measurement state |
| `state.py` | The minimal population-state and transition records (measured, inferred, predicted, missing) |
| `naive_reader.py` | Post hoc: what the validator's gates prevent against naive readings |
| `analyze.py`, `analyze_transition.py`, `report.py` | Scoring, clustered intervals and the generated report |
| `test_validator.py` | Invariants: absence eliminates nothing, a prediction cannot eliminate, a failed measurement is a named non-success, Gram leave-one-out equals the direct computation, and a rerun reproduces the recorded episodes |

## Reproduce

```
python research/dynamic_world_model/prepare_time.py --output outputs/dynamic_world_model_20260926/prepared
python research/dynamic_world_model/episodes.py
python research/dynamic_world_model/transition.py
python research/dynamic_world_model/dyn_model.py
python research/dynamic_world_model/card_audit.py
python research/dynamic_world_model/agent_arms.py          # paid; needs .env; ledger-capped
python research/dynamic_world_model/repeatability.py        # paid
python research/dynamic_world_model/case_study.py
python research/dynamic_world_model/naive_reader.py
python research/dynamic_world_model/analyze.py <episode files of dyn_model and the provider arms>
python research/dynamic_world_model/analyze_transition.py
python research/dynamic_world_model/report.py
python -m pytest -q research/dynamic_world_model/test_validator.py
```

The deterministic steps run in minutes on 28 cores; `episodes.py` and `dyn_model.py` use a
process per fold and tier.
