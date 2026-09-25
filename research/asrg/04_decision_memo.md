# ASRG decision memo

## 1. Ranking of the three candidate contributions

| Rank | Option | Expected scientific value | Complexity | Cost | Evidence still needed |
|---|---|---|---|---|---|
| 1 | **(a) Simple response ranking** — cheap predictor + nearest-signature selection over the registered library | Moderate and reliable. It is the honest floor, it is deployable from structure, dose and context alone, and recent benchmarks suggest it is hard to beat | Low. Ridge or Tanimoto retrieval plus argmin; largely present in the repository already | Low: one public asset, CPU-scale fitting | G1–G3 only. No new mechanism claim |
| 2 | **(b) Action-supported geometry** — measured anchor with out-of-fold shrinkage, reachability certificate, shared-error-aware query planning | Potentially real but unproven. It is the only part of the original ASRG that is not an algebraic identity, and it targets the repair setting MAESTRO actually has | Moderate. One new module; no new training objective beyond κ̂ | Low incremental over (a); the anchor measurement already exists in a repair case | G4: κ̂ interval excluding zero **and** regret separation from the best arm in (a) |
| 3 | **(c) Learned repair policy** — operation-value model over predicted residual, uncertainty, support and remaining budget | Low for now. It can only be attributed once (b) is established, and out-of-fold training data at this scale is thin | High. New model, new training set, new leakage surface | Moderate | G5, after G4. Reject if it does not separate from (b) at equal real cost |

**Recommendation.** Ship (a) as the baseline and the reported result. Test (b) once, under the
frozen protocol, with the rejection criteria already written. Do not start (c) until (b) has
passed. If (b) fails, say so and keep (a) as the contribution — a clean negative result about
measurement anchoring in perturbation selection is publishable and useful.

**On the original framings.** The `ideal_hat`-based dual-residual experiment should not be
presented as an experiment about biological failure causes at all, because the decomposition is
not identified. Keep it only as a named internal diagnostic with its existing `corrupted`
control arm, or retire it. The analytic gain identity should be presented as the baseline it
is, not as the method.

## 2. Go / no-go gates

| Gate | Condition | If it fails |
|---|---|---|
| **G0 Protocol** | `asrg_protocol.json` frozen and digested; audit recorded with evidence labels; arms, budgets, metrics and rejection criteria fixed before any outcome | Do not run anything |
| **G1 Data** | Pilot table rebuilt from the public asset with verified digest; measured wall time, peak memory, row counts, refused conditions; doses and time window confirmed **from the table**, not from memory | Stop; the cheap-data premise is unproven |
| **G2 Prediction** | The cheap predictor beats zero-shift and train-mean baselines on **perturbation-specific** error, with a cluster-bootstrap interval excluding zero, on held-out compounds | Stop. Nothing downstream can be attributed |
| **G3 Ranking** | Held-out-compound ranking beats random over the menu | Stop |
| **G4 ASRG (the decisive gate)** | κ̂ interval excludes zero, **and** arm 8 beats the best of arms 2–6 on measured regret at K = 0 and at ≥1 tested K, **and** A1, A5 and A8 behave as specified | Recommend (a); report the negative result and the estimated κ̂ |
| **G5 Learned policy** | Certificate precision ≥ 90% on flagged tasks; the shared-error update separates from arm 11; only then fit the operation-value model and require separation from arm 9 | Keep (b) without the learned model |
| **GB Biological claim** | Orthogonal functional, genetic or rescue evidence in matched context, time and dose, from data not used to fit anything | No mechanism, engagement or efficacy language, ever |

## 3. Verifiable milestones

| # | Milestone | Verifiable artifact |
|---|---|---|
| M1 | Audit and protocol frozen | `01_repository_audit.md`, `asrg_protocol.json` + digests |
| M2 | Pilot table rebuilt | `conditions.csv`, pseudobulk archive, `data_audit.json` with measured cost |
| M3 | Coordinates and predictor fitted on training folds | `model_parameters.npz`, held-out metrics with cluster intervals (G2, G3) |
| M4 | κ̂ estimated out-of-fold | κ̂ with bootstrap interval per context and similarity band — **the pivot of the whole design** |
| M5 | Frozen public plan | `public_plan.json`: tasks, menus, goals, budgets, arm list, artifact digests |
| M6 | Scored run | Per-arm regret with cluster intervals, cost ledgers, ablations A1–A8, and an explicit gate verdict |

M4 is the cheapest decisive step: it can be computed from M3's out-of-fold residuals alone,
before any selection machinery exists. If κ̂ is indistinguishable from zero, the project stops
at (a) having spent very little.

## 4. Unavailable assets

| Asset | Status |
|---|---|
| SciPlex3 `.h5ad`, State checkpoint and isolated env, prior prediction artifacts, `log/` records | Not in this checkout; `import state` fails here |
| Frozen chemCPA checkpoint / any independently valid `ideal_hat` | Recorded as not registered; the original E0 experiment cannot be completed |
| Private final observations for a fresh confirmatory run | Not available |
| Declared paid-API authorisation and spend ceiling for provider arms | Not declared |
| arxiv.org, openreview.net, zenodo.org, figshare API, huggingface.co, NCBI, PMC, ai.meta.com | Blocked by this environment's network policy; file sizes and a few venue statuses are index-reported and marked unverified |

Never substitute a training-response mean for a missing `ideal_hat` and call the original E0
experiment complete.

## 5. Unresolved assumptions, ordered by how much they matter

1. **Are prediction errors shared within a context?** The entire value of (b) rests on κ > 0.
   Untested on real data. Resolved cheaply at M4.
2. **Is the reachability certificate informative or vacuous?** If candidate effect vectors span
   the coordinate space, the orthogonal complement is trivial and the bound is zero. Cheap
   pre-check: the singular-value spectrum of the menu's predicted changes. If the spectrum is
   flat, drop the certificate rather than reporting a bound that never binds.
3. **Can `W` and `τ` be justified without touching outcomes?** They must come from stated
   biological intent, fixed at G0. If they cannot be defended, the objective is not well posed
   and the regret numbers mean little.
4. **Is a reference-action goal a fair proxy for a design goal?** It is convenient and public,
   but it is another compound's response, not a therapeutic target state. State this limit
   wherever regret is reported.
5. **Do the pilot's doses and time window match what the protocol assumes?** Verify at G1.
6. **Does the decision rule transfer to morphology?** Different modality, line and window; the
   external branch tests the rule, not the predictor, and cannot be pooled.
7. **Is one measured anchor enough in a new cell line?** The held-out-context family will show
   whether anchoring helps or misleads under extrapolation.

## 6. One-line summary

Build the simple ranking baseline, spend one cheap step estimating whether prediction errors
are shared within a context, and let that number decide whether action-supported repair
geometry becomes MAESTRO's methods contribution or a documented negative result.
