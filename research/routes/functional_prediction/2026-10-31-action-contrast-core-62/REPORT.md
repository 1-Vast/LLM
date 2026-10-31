# Action-contrast core research checkpoint

Date: 2026-10-31 (Asia/Shanghai)  
Episode: `2026-10-31-action-contrast-core-62`  
Status: **DATA_QUALIFICATION_PENDING / NO_NUMERICAL_RUN / VIRTUAL_CELL_NOT_ADMITTED**

## Decision

The research now has one defensible core candidate and no admitted numerical experiment. The candidate is a bounded biological law: for one cell background, two prespecified prior histories, and exactly two supported subsequent actions, an inexpensive pre-action state may preserve the later A-versus-B effect contrast across the histories and an independently prepared block. The candidate is useful only if it survives the same-cost ordinary response-panel/history-interaction rival and reduces actual assay cost or decision regret.

This is a research object, not a new architecture. Predictive-state representations, reward/value equivalence, decision-focused optimization, active system identification and causal transport are established principles. Dynamic BH3 profiling and functional precision medicine already cover the broad early functional measurement to later treatment-response workflow. No broad novelty or “virtual cell” claim is supported.

## Evidence that changed the direction

The static decision-focused surrogate remains parked. Its saved development observations were raw-k20 top-set overlap `0.21203` and regret `0.99476`, ordinary ridge `0.19857` and `1.03248`, and binary top-set ridge `0.18684` and `1.12913`. That last model is a surrogate label regression, not a direct SPO/regret optimization test. It cannot reject decision-focused learning in general and does not provide dynamic history/action evidence.

The targeted closest-prior challenge found that the broad combination is already occupied by: dynamic BH3 or another early functional panel, ordinary response-panel reconstruction with known-history and history-by-action terms, Rhaister-style few-measured-response completion, and established action-conditioned sufficiency/transport theory. The remaining possible contribution is the specific response law and its failure boundary, not the formula or encoder.

The resource audit found no ready numerical benchmark:

- **PA14 CAR→GEN, Nature Communications 2026:** method-level A→B exposure, medium exchange, optional drug-free pause and CFU/OD endpoints. The source workbook and MIC table were not readable in this pass. It is the smallest future bacterial bridge, not evidence for cancer-cell transfer.
- **Sarcoma temporal collateral sensitivity, Communications Biology 2025:** 14-day mTKI pretreatment followed by a 14-day infigratinib switch and growth/viability readouts. The joined early-state/A-B table and repeat nesting are unavailable; the key temporal panels have limited replicate structure.
- **UPEC ampicillin, npj Antimicrobial Resistance 2026:** real pre-ampicillin growth-rate measurement and washout/regrowth, but rechallenge is on selected survivors and the all-starting-population A/B matrix is absent or unresolved.
- **ALK dynamic BH3, Cell Death & Disease 2025:** strong prior for early functional priming followed by later death and sequential combinations, but no authenticated public row-level held-history/action table.

These are access or identifiability failures, not biological negative results. No numeric cells, protected outcomes or response arrays were opened.

## Frozen candidate and falsifier

Candidate `I-ACT-02 v2` is recorded in [CANDIDATE_V2.md](CANDIDATE_V2.md). Keep the measured state `S` separate from the history `H`; a history identifier cannot be placed inside `S` to make invariance tautological. The initial action menu and oracle are exactly `{A,B}`. A larger menu is a separate contrast-by-contrast claim.

For lower-is-better outcome `Y`, test on a declared common-support region:

```text
E[Y(A)-Y(B) | S=s,H=h] = tau(s)
```

The minimum design is two histories × two randomized next actions, exchangeable sister cultures for destructive probes, independent preparation blocks and one fixed later endpoint. Freeze dose, time, washout/carryover, denominator, margin, model, costs and abstention rule before holdout outcomes. The design audit proposes four blocks as a feasibility floor (three source blocks plus one prospective holdout) and an absolute viability margin of `0.10`, subject to replacement by a source-independent precision/headroom justification before final unblinding.

The measured-state law is falsified when the history difference in the A-versus-B contrast reproducibly exceeds the prespecified consequential margin within overlapping `S` support across independent preparations. Wide intervals are inconclusive. A failure of this state does not prove that no richer state exists. Absolute efficacy, safety, tail risk and unseen-action generalization are separate claims.

## Independent challenge disposition

A fresh `gpt-6.1-sol/high` challenger recorded `CHALLENGE_INITIAL.md` before reading the additional cited source passages, then wrote [CHALLENGE.md](CHALLENGE.md). It independently reached `NO_NUMERICAL_ADMISSION`: the closest rival is same-cost DBP/fixed functional panel plus ordinary response-panel reconstruction with history-by-action terms; PA14 is only a future metadata-gated bridge; sarcoma and UPEC do not currently support the complete run; organoid and Agent extensions are premature.

The independent review does not certify novelty or biology. It confirms that the candidate has a concrete falsifier, a minimal distinguishable observation and a restart rule. It also confirms that adding a larger model or an Agent cannot repair missing row-level joins, positivity, carryover or exchangeability.

## Next executable step

Do not fit any current resource. Restart only when a public or newly generated resource passes the following metadata whitelist before outcomes are opened:

1. one lossless row-level key with history, subsequent action, dose/MIC, order, pause/washout, time, cell/background, preparation and technical replicate;
2. both A and B in each eligible history and preparation, plus same-unit controls;
3. a pre-action state measured on exchangeable sisters or a validated nondestructive equivalent;
4. common support and action positivity; no selected-survivor-only estimand when claiming all-starting-population behavior;
5. an independently justified equivalence margin and a sealed preparation holdout;
6. same-cost ordinary response-panel/history-interaction, kinetic/count, and appropriate mechanism-specific baselines.

If no existing resource passes, the smallest changed-premise path is a designed two-history × two-action bridge with bulk count/growth/viability first. Add a functional probe only after endpoint-only data show a documented blind spot. If the ordinary panel matches the candidate at the same cost, stop the special representation claim and retain only the bounded biological law if it remains informative.

Only after this cell-level gate passes should a minimal organoid test ask whether composition, matrix or exposure breaks the law. An Agent may then be tested as a measurement-selection policy against deterministic value-of-information and fixed/random controls at matched observations, actions and assay/time budget. It must earn admission through a held-out decision gain; prose or planning cannot supply missing biology.

## Scope, budget and preservation

This was a focused continuation, not an exhaustive 2025–2026 survey. New public acquisition was limited to free/local sources. The current round used 8 coordinator/agent HTTP attempts and 228,521 known response-body bytes: resource audit 5/23,559 B, prior challenge 2/183,436 B, and one coordinator direct-path check 1/21,526 B. The fresh challenger and design audit used no network. A nominal ceiling of 30 requests and 150 MiB was set for this bounded pass; no paid API was used. Requested delegated model was `gpt-6.1-sol/high`; effective serving metadata is unavailable.

All candidate, source, failed-access, challenge and design files remain in this episode. No `src/` or `tools/` changes were made, no Agent/AIVO implementation was started, and unrelated dirty worktree changes were not rearranged.

## Reusable handoff

The next researcher should begin with [CANDIDATE_V2.md](CANDIDATE_V2.md), [resource audit](../2026-10-31-resource-audit-62/REPORT.md), [closest-prior challenge](../2026-10-31-prior-challenge-62/REPORT.md), [minimal design](../2026-10-31-minimal-action-design-62/REPORT.md), and [independent challenge](CHALLENGE.md). The current default is **parked until data admission**, not a model-training request. A new round must name the changed evidence or premise before spending another search budget.
