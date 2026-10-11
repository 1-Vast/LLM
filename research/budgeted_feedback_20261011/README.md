# Sparse feedback under a common total budget

This 2026-10-11 study delivers a cross-field literature supplement, an official-source
data audit, a reproducible two-round development experiment, and a tested common-budget
contract. **The new policy does not establish superiority over the strongest batch
method.** Only resource accounting is promoted to `src` and `tools`.

## What was tested

The experiment reused 701 reference compounds, divided 281 already-exposed development
compounds into 141 fit and 140 calibration cases, and evaluated 421 already-exposed replay
compounds. Each episode fixes one drug, purchases discovery-cell-line readouts and
selects ten sensitive terminal cell lines. This is not fixed-context drug selection.
No new biological measurements or LLM calls were made.

The total cap is 18 declared read equivalents: one measurement costs 1 and a turnaround
costs 2. Batch buys 16 measurements in one round; a two-stage design buys four then ten.
A gate fitted before replay can stop after the first four. The strongest comparator was
selected from seven source-only/Gaussian IVR/KG choices; the old strongest IVR batch of
16 was selected again. A fixed split and shuffled-feedback control separate adaptive
choice from the value of correctly assigned observations.

## Results

| Metric | Frozen batch | Gated feedback |
|---|---:|---:|
| Mean measurements | 16.000 | 8.442 |
| Mean turnarounds | 1.000 | 1.444 |
| Mean declared resource use | 18.000 | 11.330 |
| Raw terminal utility | 0.15894 | 0.15309 |
| Net utility under the declared prices | 0.14094 | 0.14176 |

The gate stopped after four readouts in **55.58%** of episodes. Resource use fell
**37.05%**, but raw utility also fell. Net gain was **+0.00082**, with mechanism-cluster
95% interval **[-0.01102, +0.01290]**. This is not evidence of superior decisions,
noninferiority, or monetary cost effectiveness. Fixed two-stage adaptation added only
+0.00189 over the same-resource fixed split, interval [-0.00701, +0.01017]. Correct real
feedback beat shuffled feedback, but that contrast does not prove adaptive selection
beats batch.

Selected-path coverage was **87.89%**; on 101 active drugs it was **67.33%**, below the
90% target. The diagnostic covers the selected terminal cell lines along the allowed
decision path. It is not numerically interchangeable with the earlier all-terminal
coverage endpoint. Calibration is a post hoc audit and does not control purchases.
Old model tuning used the development population; no new conformal guarantee is claimed.
The exploratory success flag also lacks a coverage-confidence or useful-width criterion.

The paired secondary comparison had only **120** eligible episodes: effect **-0.01772**,
cluster interval **[-0.05640, +0.01575]**. The 301 missing/ineligible episodes and
selection-dependent availability preclude a full-population confirmation claim.

The run took about **403 seconds**, generated 8,424 arm/episode results including gated
replays, and made zero API calls. An independent ledger audit reconstructed utility,
path errors and all resource charges; maximum utility discrepancy was 4.44e-16.

## Deliverables and promotion

- [Design and next confirmation gates](DESIGN.md): method assumptions, complete-policy
  reliability, matched Agent comparisons, graph/transfer controls and independent endpoints.
- [Literature review](literature/REVIEW.md): 13 verified paper records spanning CV, NLP,
  robotics, optimization, selection-aware inference and the requested MAP paper; exact
  sources, inspected scope, hashes and retrieval failures are retained. These supplement
  the earlier review and are not all previously unseen references.
- [Data strategy](data/DATA_STRATEGY.md): 17 retrieved official sources, actual local
  availability and a small input-only feasibility check. BBBC021 and PRISM share only
  five strict structure matches; this does not create a matched phenotype bridge.
- [Experiment](experiment/README.md): frozen protocol, behavior tests, row-level outputs,
  source receipts, limitations and fresh-directory reproduction instructions.
- [Core budget contract](../../src/maestro/campaign_budget.py): a byte-identical promotion
  of the tested [research prototype](contract/budget.py). It enforces a common cumulative
  cap including measurement, turnaround and declared other resource costs.
- [Paired evaluator](../../tools/evaluation/decision_report.py): optional common total
  resource cap, explicit additional resource/utility costs, and unchanged legacy defaults.
  This is a report check; purchase callers must explicitly use the core check beforehand.

The policy, group bootstrap gate, posterior, calibration and biology stay in research.
The next scientific step should qualify an endpoint/cheap-observation bridge on independent
culture units, retain context/transcriptional transfer as strong priors, and test KG
additions against shuffled-graph controls. More LLM reasoning or additional feedback
rounds are not supported by these results. LLM contribution requires separate same-tool,
same-information, same-budget comparisons.

## Verification and reproduction limits

The full production suite has **780 passes and one pre-existing failure**: the repository
shape test requires root `Innovation.md` to be absent, but it is tracked and present.
The baseline before edits had 772 passes and the same failure. That unrelated file was
preserved. Seven research budget tests and nine experiment behavior tests pass. The
ledger audit checks all 8,424 results for budget, duplicate/terminal purchases, utility
and path-score consistency. [ENGINEERING_RECEIPT.json](ENGINEERING_RECEIPT.json) pins
the delivered engineering files and records these checks.

Run from the repository root with `D:/anaconda/envs/maestro/python.exe`:

```powershell
& D:/anaconda/envs/maestro/python.exe -m pytest
& D:/anaconda/envs/maestro/python.exe -m pytest research/budgeted_feedback_20261011/contract/test_budget.py
& D:/anaconda/envs/maestro/python.exe -m unittest discover -s research/budgeted_feedback_20261011/experiment -p test_study.py -v
& D:/anaconda/envs/maestro/python.exe research/budgeted_feedback_20261011/experiment/verify.py
```

Large original/derived inputs and compressed full ledgers are locally retained, not
distributed by the Git checkout. The experiment README specifies prerequisites and
how to rerun into a fresh sibling directory without changing the original freeze.
Missing inputs are not substituted with synthetic outcomes. Preserved summaries are
not a substitute for a rerun, and engineering verification is not biological validation.
