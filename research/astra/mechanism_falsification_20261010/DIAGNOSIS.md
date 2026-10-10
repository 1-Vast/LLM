# Diagnosis of the existing dual core (before block M)

Sources: the code under `src/`, `research/EVIDENCE.md`, `research/REPORT.md`, `task.md`,
`Innovation.md`, and the frozen study packets they cite. Each answer names its evidence.

| Question | Current state | Evidence |
|---|---|---|
| 1. How does the agent reason, plan and use tools? | LLM components (task triage, contrast planner, repair planner, tool router, figure inspection) emit validated JSON; a deterministic layer (`maestro.contrast.MAESTROAgent`) builds and repairs the mechanism contrast; CaseStore owns execution facts. | `src/agent/llm.py` `COMPONENTS`; `src/maestro/contrast.py` |
| 2. How does the virtual cell predict? | Condition-bound STATE RNA forecasts with identity and applicability checks; basal-similarity context transfer for Tahoe phenotypes; an empirical-Bayes combination world. | `src/virtual_cell/state_adapter.py`, `context_transfer.py`, `combination_world.py` |
| 3. How are hypotheses and predictions represented? | Hypotheses are categorical labels inside a `MechanismContrast`; predictions are per-condition response vectors. A prediction is conditioned on the *perturbation*, never on a *mechanism hypothesis*. | `src/maestro/models.py`; STATE takes a drug identity |
| 4. How does the agent use virtual-cell output? | The production default (`select_expected_coverage`) uses declared detection power; virtual-cell output is logged, not used. `select_discriminating_action` (opt-in) uses predicted readings per hypothesis. `world_model_value` admits a forecast only past a value ceiling. | 2026-09-27 gated-plan audit; `src/maestro/acquisition.py`; `world_model_value.py` |
| 5. Do predictions change decisions? | Rarely and not beneficially: readout repair lowered MSE 2-8% with identical selections; permuted world-model priorities reproduce every acquisition gain; boundary acquisition equals knowledge gradient. | EVIDENCE.md rows "STATE readout repair", "Boundary acquisition"; 2026-09-27 external validation |
| 6. How are reliability and applicability judged? | Named refusals (`BRIDGE_NOT_SAME_UNIT`, `CONTEXT_UNDERCOUNTED`, `WM_CEILING_BELOW_MUB`), platform identity checks, interval-based measure-or-predict planning. Elimination of hypotheses is *not* calibrated: wrong-elimination forecasts were about 5x too low externally and scenario-card P(wrong) 2-19x too low. | `world_model_value.py`; 2026-09-27 belief planning and external validation |
| 7. How does feedback update reasoning? | Purchased observations update residual models; across pairwise, V3 and Jaaks studies, feedback gave no reliable decision gain. | EVIDENCE.md "Conditional pairwise correction", "Dual-source residual transfer v3" |
| 8. What has demonstrated value? | Engineering contracts; the certified-discovery loop (in-context EB world model + random audit, confirmatory pass on NCI-ALMANAC); basal-similarity transfer; the world-model value gate refusing STATE correctly; stopping rules that avoid unused purchases. | `src/maestro/certification.py`; `research/certified_discovery`; phenotype-anchor and block K packets |
| 9. What has failed? | STATE transport across platforms; LLM planners against deterministic routing; MAP knowledge against Morgan fingerprints; feedback; measurement-choice planners against a fixed order (small headroom on the MoA proxy task); risk certification coverage. | EVIDENCE.md; 2026-09-26/27 blocks |
| 10. Which components are foundations? | `certification.py` (conformal p-values with design-based exchangeability); `acquisition.py` outcome-forecast interfaces; `world_model_value.py` admission and abstention; named-refusal conventions. | as listed |

## What blocks complementary contributions

1. **The world model cannot speak about hypotheses.** It predicts a response for a perturbation, so
   it cannot say what each competing mechanism predicts, which observation separates them, or that
   two mechanisms are indistinguishable. Discrimination has been approximated by response
   magnitude, which is why permuted priorities reproduced the gains.
2. **Falsification is uncalibrated.** Hypotheses are eliminated by likelihood or card thresholds
   whose wrong-elimination rate was several-fold above forecast. A falsification-driven agent built
   on that rule would discard true mechanisms confidently.
3. **The agent's knowledge is not executable.** The LLM routes, triages and adjudicates; its
   biological knowledge never becomes a prediction that data can contradict, so its contribution
   cannot be measured except as routing accuracy (where deterministic code wins).
4. **No output for an exhausted hypothesis set.** `task.md` requires marking the set invalid when
   all hypotheses conflict with evidence; no code implements it.
5. **Headroom.** Earlier measurement-choice tasks had a fixed order near the oracle. A test of
   design value must report the oracle and the no-design baselines first.

Block M addresses 1-4 directly and reports 5 as a measured quantity rather than assuming headroom.

## Constraints carried forward

* STATE `final.ckpt` remains the scoped foundation for Tahoe-platform 24 h single-cell responses.
  Its admission gate refused it for the endpoints tested so far, and block K showed it does not
  transport to another platform. Block M does not use STATE: its observations are bulk L1000
  landmark signatures at 6 h and 24 h, a platform and time STATE was not trained on. The block's
  world model is a separate, reference-fitted, mechanism-conditioned model, and is labelled as such.
* Predictions never upgrade evidence; a surviving hypothesis is "not falsified by the menu", not
  "confirmed".
