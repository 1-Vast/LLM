# Report: case-memory production integration and the untouched-source evaluation

Historical integration/evaluation record. For the current production candidate and subsequent
development experiment, see [SCIENTIFIC_REPAIR_V3.md](SCIENTIFIC_REPAIR_V3.md). The frozen
external measurements below are not measurements of the version-3 estimator.

> **File summary**
> - **Path**: `research/case_memory_integration/REPORT.md`
> - **Purpose**: the final report of the case-memory integration task: what was built, what the
>   untouched LINCS 2020 evaluation measured, which gates failed, what was integrated, and what
>   remains unvalidated.
> - **Depends on**: `PROTOCOL.md` (frozen), `AUDIT.md`, `DESIGN.md`,
>   `outputs/case_memory_integration/`.

Statements are labelled by what they rest on: **measured** (an executed command whose output is
stored in the repository), **model prediction**, **historical analogy**, **curated annotation**,
**qualified evidence** or **speculation**. A number without a label is measured.

## 1. The answer, question by question

| Question | Verdict | Evidence |
|---|---|---|
| Was production integration completed? | **Yes, behind the flag, defaults unchanged.** | 11 production modules; the gated path `user data -> compiler -> graph -> retriever -> forecaster -> ranking -> branching plan` is tested end to end through the orchestrator; with `MAESTRO_CASE_MEMORY_ENABLED` unset the orchestrator is byte-for-byte the old behaviour (tests in `tests/test_case_memory_orchestrator.py`). |
| Was external validation completed? | **Yes, as an exploratory stratum.** | LINCS 2020 Level 5 (untouched source), frozen protocol, 6/6 integrity checks, 112 forecast items on 26 unseen units. The confirmatory population minimum is not met; everything here is stratum-level or descriptive. |
| Do directional features improve prediction? | **Resolution yes, calibration no.** | Directional accuracy 0.80 (combined/full) against 0.67 (scalar); discrimination 0.32 against -0.00 nats. Forecast NLL is worse: full minus scalar +0.109 [+0.018, +0.205] (primary endpoint). |
| Does the system improve terminal decisions? | **No evaluable signal.** | All planners equal the fixed order (0.538 correct, n=26); the oracle headroom is negative (-0.19) because most unseen units have one condition; the headroom gate fails by construction. |
| Does the system improve calibration? | **No.** | Directional arms sharpen but miscalibrate (NLL 1.02-1.09 against 0.93-0.99 for the class-frequency memories; wrong-elimination Brier improves slightly, 0.168 against 0.201). |
| Does the system reduce experiment cost? | **Not evaluable.** | Every episode offered one measurement; no cost difference exists to measure. |
| Robustness to unseen contexts? | **Mixed and honest.** | Directional retrieval keeps 0.74-0.80 directional accuracy on genuinely novel chemistry; class-frequency memories calibrate better. |
| Strong enough for default activation? | **No.** | Three independent gates fail: exploratory stratum, headroom gate, primary endpoint. `case_memory_enabled = false` remains the default. |

## 2. What was measured on the untouched source

Population (frozen pool rule): 5 mechanism classes (Opioid receptor agonist, Opioid receptor
antagonist, Angiotensin converting enzyme inhibitor, PARP inhibitor, JAK inhibitor - **curated
annotations**, proxy truth), 65 reference blocks, 26 unseen test blocks (InChIKey connectivity
blocks absent from GSE92742 and GSE70138), 112 (unit, condition, contrast) forecast items.

Forecast level (per arm: NLL / Brier of wrong elimination / directional accuracy / discrimination
in nats):

| arm | NLL | Brier | dir. acc. | disc. |
|---|---|---|---|---|
| scalar (status quo) | 0.988 | 0.201 | 0.670 | -0.002 |
| signed direction | 1.075 | 0.168 | 0.790 | 0.317 |
| pathway direction | 1.019 | 0.169 | 0.740 | 0.283 |
| combined | 1.067 | 0.168 | 0.800 | 0.319 |
| mechanism prior only | 0.955 | 0.193 | 0.710 | 0.000 |
| case memory only | 0.934 | 0.195 | 0.710 | 0.019 |
| full (integrated) | 1.089 | 0.170 | 0.800 | 0.279 |
| oracle (clairvoyant) | 0.000 | 0.000 | 1.000 | - |

Primary endpoint, paired NLL difference full minus scalar: **+0.109 [+0.018, +0.205]** (unit-cluster
bootstrap, 2,000 draws, seed 20260929) - the full arm is worse calibrated with the interval
excluding zero. Wrong-elimination observed 0.259; class-frequency memories forecast 0.24-0.30,
directional arms 0.24-0.25.

Decision level (26 episodes): fixed, random-legal and every planner arm are identical (0.538
correct, 0.308 wrong, 1.00 measurement) because most unseen units carry one core-scope condition;
the clairvoyant oracle decides 0.346 and defers 0.654, so the headroom gate
(oracle - fixed >= 0.04) fails by construction.

**Reading of the result.** Directional information is real and retrievable on untouched chemistry
(+0.13 directional accuracy, +0.32 nats discrimination), but similarity-weighted sharpening is
miscalibrated at this support level, so the primary endpoint fails. This mirrors the development
verdict (hypothesis-conditional forecasts are worth having; scalar selection is harmful; no
decision improvement) and extends it one step: the directional signal survives contact with an
untouched study, and so does the calibration problem.

## 3. Visual verification (measured)

Seven figures in `outputs/case_memory_integration/figures/` (hashed in `figures_manifest.json`)
were drawn from pipeline files and inspected: the pathway heatmap reproduces the expected
anti-proliferative pattern (JAK and PARP inhibitor centroids suppress E2F/G2M/MYC programmes),
the calibration panels show the directional arms' overconfidence directly, the domain-shift panel
shows most test units' best reference cosine below 0.3, and the norm panel confirms the frozen
5th-percentile detection thresholds sit at the left edge of the reference distribution.

## 4. Claim boundaries

- **Exploratory stratum.** 26 unseen units (93 at the wider core scope) do not meet the
  confirmatory minimums of protocol v2; every statement here is stratum-level or descriptive.
- **Proxy task.** Mechanism classes are **curated annotations** (LINCS 2020 `moa` strings); no
  conclusion here is about biological ground truth. No wet-lab result exists; nothing here is
  **qualified evidence**.
- **The production estimator remains uncalibrated by declaration.** It now prefers realised
  multi-state case measurements and applies support-aware shrinkage using Kish support and domain
  shift, but it carries `calibration_status: uncalibrated`, no calibration dataset, and stays out
  of default production action selection until a held-out development calibration is fitted.
- **The case memory changes nothing by default.** The feature flag is off; the orchestrator's
  default path is unchanged and tested so.

## 5. Integration status

Integrated into `src/` and `tools/` (all behind the flag or the research-mode boundary): the scm-2
episode schema and append-only store, directional features, the hypothesis graph, adaptive
retrieval, the case-memory outcome forecaster with `UserStateContext`, decision-value ranking and
branching plans, the problem compiler, the gated pipeline, the orchestrator wiring, the
conditional virtual-cell forecast contract, and the `case_memory` runtime tool with typed
refusals. Not enabled by default; the heuristic planner is not part of default action selection.

## 6. What remains unvalidated

1. Any confirmatory claim: needs an untouched population of at least 200 (exploratory) to 500+
   (confirmatory) label-compatible independent units. LINCS 2020 at wider scope or a second
   untouched study (the protocol-v2 candidate list also names a Tahoe-100M subset after a
   training-overlap audit) are the registered directions.
2. Calibration of the new support-aware forecasts at low support; its constants are explicit but
   still require a development-only fit and a second untouched evaluation. The frozen replay
   numbers above are the pre-fix baseline and are not post-fix performance claims.
3. Decision-level value: needs a task where episodes offer more than one condition and the oracle
   has positive headroom.
4. Real user episodes: the schema and compiler are tested, but no qualified real user episode has
   closed the loop end to end.

## 7. Reproduction

```bash
python -m tools.case_memory.workflow sources   # verify sources, write external_source_manifest.json
python -m tools.case_memory.workflow pack      # build the hashed data pack
python -m tools.case_memory.workflow replay    # frozen replay -> results.json + forecast_items.jsonl
python -m tools.case_memory.audit quality      # 6 integrity checks
python -m tools.case_memory.build_cases        # reference episodes (scm-2, with typed outcomes)
python -m tools.case_memory.workflow graphs
python -m tools.case_memory.workflow evaluate  # evaluation_summary.json + activation verdict
python -m tools.case_memory.audit figures      # 7 figures + figures_manifest.json
python -m pytest research/case_memory_integration -q
```

## 8. Post-integration scientific correction

See `SCIENTIFIC_FIX_AND_DATA_PLAN.md`. The production candidate now refuses unlabelled branches,
requires explicit conditioning and contrast, uses independent-unit effective support, and prevents
proxy labels from entering production evidence. The new development-only grouped holdout uses 54
training and 11 held-out reference compounds (156 items): candidate NLL 1.372004 vs Jeffreys
frequency baseline 1.353464. This is not an improvement claim and is not comparable to the frozen
external experiment above. The external test set was not reused. Default activation remains off.
