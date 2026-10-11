# Review and next experiment: shared feedback in a held-out cell context

Reviewed 2026-10-11, Asia/Shanghai. The requested scope is review and a next-round plan. This packet records inspection of the current repository, existing results, primary literature and three agent audits. It introduces no implementation, new biological benchmark or scientific promotion. The existing studies and their failures remain unchanged. This is a candidate design, **not a registered execution protocol**.

## Decision

Keep the current per-drug cell-line task as a regression benchmark. Make the next scientific question narrower and different:

> For a cell context whose drug-response outcomes are unavailable to the fitted model, can a small, shared batch of measured probe-drug responses improve selection of other, unmeasured drugs enough to pay for that batch?

First test the information and cross-drug error transfer, using a fixed probe batch. Test adaptive probe selection only if that diagnostic succeeds. Add knowledge-graph features as a separate attribution experiment; evaluate a language agent only after a deterministic policy has a defensible role and endpoint. The supplied attachment's ordering is sound, subject to the exposure, ranking and guarantee corrections below.

## What the current results actually establish

The [budgeted-feedback study](../budgeted_feedback_20261011/README.md) is transparent about exposed data, scenario prices and a failed scientific gate. Its 14 engineering-receipt file hashes match the current files. Existing row summaries and paired arithmetic support the reported results.

| Quantity on the 421 exposed replay compounds | Batch GP, 16 reads | Gated feedback | Interpretation |
|---|---:|---:|---|
| Raw terminal utility | 0.158935 | 0.153087 | Mean biological utility decreases by 0.005848 |
| Measurements per episode | 16.000 | 8.441805 | 47.24% fewer purchased values |
| Turnarounds per episode | 1.000 | 1.444181 | 44.42% more simulated turnarounds |
| Declared resources per episode | 18.000 | 11.330166 | 37.05% fewer read equivalents |
| Scenario net utility | 0.140935 | 0.141757 | Increment +0.000822, uncertain |

There are 234 stop episodes and 187 continuation episodes. Total declared resources are 4,770 versus 7,578. The 37.05% result is a reduction in `reads + 2 * turnarounds`; it is not a 37% reduction in rounds, laboratory expenditure or biological experiments.

The primary mechanism-string cluster interval for net utility is [-0.011024, +0.012902]. The same-resource adaptive-versus-fixed-split contrast is +0.001894 [-0.007007, +0.010172]. Neither confirms a useful adaptive decision gain. The group continuation fit uses two bins and a bootstrap of individual drug means; its lower estimate is neither a per-episode certificate nor a joint-batch NetEVSI bound.

Current raw utility loss and resource saving imply the descriptive price sensitivity

`delta_net(lambda) = -0.00584825 + 6.66983373 * lambda`,

where lambda is utility per declared read equivalent, preserving the assumed 2:1 turnaround-to-read tariff. The sample-mean break-even price is approximately 0.00087682. This explains the small positive mean at the frozen 0.001 price; it does not select a valid price, supply uncertainty for the break-even point or prove real cost effectiveness. Prices or noninferiority margins must not be chosen from these outcomes.

Complete selected-path coverage is 370/421 = 87.89%; the active-drug subgroup is 68/101 = 67.33%. This is a different event from the earlier all-terminal interval. It remains a postexecution diagnostic, with prior parameter tuning on the old development population; it does not certify selection-conditional or active-set coverage. Secondary comparison has only 120 eligible paired episodes, leaving 301 unavailable/ineligible; delta -0.017721, cluster interval [-0.056398, +0.015748]. Availability depends on the selected set, and doses differ.

The experiment made zero LLM/API calls. Recorded tests and 8,424 verified arm/episode ledgers support the implementation and bookkeeping. No full-suite or biological replay was rerun for this review. Arithmetic verification does not supply independent biological units. A new split of already exposed outcomes does not restore a fresh biological holdout.

Two future objectives remain legitimate but separate: superior net decisions, or noninferior biological utility with a predeclared minimum cost saving. Neither is established here. The latter must be registered before new evaluation, with a defensible allowable utility loss, cost definition, reliability conditions and multiplicity treatment.

## Corrections needed before the proposed task can be run

### Seal the target context, including every derived statistic

The current [transcriptional transfer](../../src/virtual_cell/transcriptional_transfer.py) predicts a drug profile from measured profiles of other drugs across already represented cell lines. Its reference profile matrix includes outcomes at the target column. That is valid for its existing task. It supplies unavailable target-context information if carried unchanged into a cold-start cell-context task.

Seal the complete target response column for **every drug**, including source/reference drugs, before fitting means, response factors, covariance, feature selection, normalization, nuisance axes or hyperparameters. Release only the explicitly purchased probes. A target response must not enter a source-drug embedding or a global centered response matrix through another route. Poisoning all unpurchased target responses should leave priors, probe identities, updates and committed terminal decisions unchanged.

Target basal expression may be allowed as shared, unlabeled deployment input; standardization and feature selection come from reference contexts. State whether the claim concerns known drugs in an unseen outcome context, unseen drugs, or an unseen lineage. The first is the proposed initial task. Public drug targets and structures are allowed for known drugs; removing all drug nodes is required only for the separately claimed strict inductive drug regime.

Basal-context transfer has useful evidence for Tahoe's scoped relative-survival endpoint. It is a strong baseline family to test, not a prevalidated PRISM predictor. Conversely, successful PRISM transcriptional transfer does not validate new-cell response transfer. Existing local data are still exposed, so the first masked-context experiment is retrospective algorithm diagnosis.

### Require differential errors that can change decisions

For a fixed context, adding the same `b_c` to every drug leaves top-k mean rankings unchanged. A positive affine transform `a_c * m(d,c) + b_c` also preserves them. Such arms are useful for calibration, absolute-threshold or nuisance checks, but cannot explain a top-k ranking improvement. This conclusion assumes the terminal rule remains ranking of means; threshold and uncertainty-based rules are different objectives.

The informative hypothesis is that a probe's error reveals **drug-dependent** errors in other drugs. Start with the smallest shrinkage model that can express that:

`y(d,c) = m(d,c) + u_d^T z_c + b_batch + epsilon(d,c)`.

Fit the fixed drug features/loadings `u_d`, rank, regularization and residual/noise structure on reference contexts, using leave-context-out prediction residuals. Estimate `z_c` only from purchased probes. Do not use in-sample fitted residuals or target-wide response decompositions. A context effect and a batch effect may be confounded when a context is observed on one plate; controls and separate culture/plate repeats are required before calling an inferred factor biological.

Earlier [conditional residual transfer](../decision_value/pairwise_v3/README.md) failed its RNA decision gate. Retain an endpoint-compatible version of that method as a comparator. Do not import its RNA weights into a PRISM functional endpoint or describe the same factorization as a newly established mechanism.

### Name the reliability claim precisely

Three questions require different guarantees:

| Claim | Event being evaluated | What a frozen episode replay can supply |
|---|---|---|
| Marginal selected-path coverage | All selected candidates at all allowed snapshots are covered for a random episode | A max-path score can be calibrated on independent, exchangeable whole episodes; useful widths and support still need checks |
| Selection-conditional coverage | A particular candidate is covered conditional on being selected, possibly within a declared selection category | Requires a compatible selection-aware construction and its assumptions; freezing alone is insufficient |
| False coverage-statement rate | Expected fraction of reported intervals that miss | An FCR result; it is not simultaneous or per-candidate conditional coverage |

[Jin and Ren's JOMI](https://doi.org/10.1093/jrsssb/qkaf016) provides a selection-conditional construction using calibration/test swaps and rerunning the selection rule. Its theorem assumes the specified conditional exchangeability and permutation invariance. It does not automatically cover the entire selected vector or a feedback policy with queried labels. [Bao et al.](https://doi.org/10.1093/biomet/asae010) chiefly control FCR. [BatchBALD](https://arxiv.org/abs/1906.08158) addresses joint information and redundancy, not any of these coverage guarantees.

For the first diagnostic, report selected-set/path error, coverage, width, abstention and active-subgroup error honestly as diagnostics. For later confirmation, choose one primary reliability event, freeze the whole operational policy, and obtain separate calibration contexts/units. Any calibration rule that changes purchases or stopping becomes part of the policy and must itself be evaluated; audit intervals attached afterwards do not control runtime risk.

Biological activity defined from hidden outcomes may define a prespecified evaluation subgroup, not deployment selection or calibration features. Surprising but condition-valid observations remain measurements: reject identity or QC failures, and treat model mismatch as a reason to reconsider predictions or request a costed confirmation. Do not discard strong responses simply because their innovations are large.

### Clarify budgets, fallback and units

[CampaignBudget](../../src/maestro/campaign_budget.py) is presently a reusable arithmetic check, and [decision_report](../../tools/evaluation/decision_report.py) can validate reported cap compliance. Neither automatically reserves turnaround/API costs in the orchestrator. The existing production decision-value contract uses myopic hypothesis-decision loss, not the proposed PRISM top-10 objective; reuse provenance and authorization contracts without pretending the biological objective has already been integrated.

Future purchase code must reserve the complete proposed batch, charge its turnaround once, and include retries, QC failures, API/tool charges, cancellations and remaining commitments. A prefeedback batch alternative can be part of a registered strategy. After four reads and one turnaround, the example cap leaves 12 read equivalents: buying a fresh 16-read batch plus its turnaround would total 24, exceeding the cap of 18. A refused forecast cannot be rehabilitated by a fallback that uses the same unqualified forecast.

A physical acquisition batch and an independent statistical cluster are not synonymous. Related wells, pooled cell-line measurements or split cultures may remain dependent. Choose analysis clusters from the actual culture/plate/day design and estimand. Report response-context heterogeneity separately; seeds, readouts and cells do not create additional independent cultures.

## The minimum next-round experiment

### 0. Qualify one task and its data

Use a single-drug functional assay in one declared setting. The practical first candidate is local PRISM primary HTS at exactly 2.5 uM, with its documented exposure protocol. Verify treatment metadata, aliases, replicate aggregation and assay exceptions before assembling a matrix. Existing cached averages must not be presumed dose-pure. Do not call normalized viability an absolute apoptosis or causal-mechanism measurement.

The read-only metadata audit found 3,939 unique HTS treatment-column names at exactly 2.5 uM, present in the raw response header; these are treatment columns, not a verified unique-drug count or complete-response library. The 561 CCLE matches refer to the entire 578-line primary matrix, not a qualified dose-filtered evaluation population. The old split groups treatment columns by lowercased compound name and the tier extractor averages them: 36 of its 1,403 compounds have mixed-dose columns. For example, AZD7762 combines 2.5/2.52 uM and GDC-0879 2.38/2.5 uM. This does not alter the existing budget arithmetic, but it makes a new exact-dose matrix and condition audit necessary before claiming a fixed-dose endpoint.

Use CCLE basal features and public structures/targets as potential priors. Compare reference mean drug potency, basal kNN and a regularized predictor on development contexts; freeze the strongest supported prior. If transcriptomic features are added, their source conditions and acquisition cost are explicit and they must not smuggle target-context viability into the prior.

The response split is by complete cell context, with distinct reference/model-fit, development, policy-calibration and evaluation groups. Fit aliases/identity grouping from metadata. Lineage-held-out performance is a separate, harder sensitivity analysis. Reference responses for the terminal drugs are allowed: this first study claims transfer to a new response context, not chemically unseen drugs. No exact sample-size or confirmation count is justified until qualified contexts, dependence and cluster-level variance are known.

Pass this step only when response rows, permitted prefeedback inputs, outcome exposure and source/plate limitations are explicit. A missing plate/culture lineage permits retrospective prediction diagnosis, not independent laboratory confirmation.

### 1. Diagnose shared information with one fixed probe batch

Choose eight probes from reference-only information as a small starting panel. Use four and sixteen only as declared development sensitivity analyses, not a search for the best held-out result. Every update arm receives exactly the same probe values in one batch. Freeze a common terminal drug pool, excluding the probes and their aliases. Fix top-k in development, for example ten. No terminal response is purchasable in this diagnostic.

| Arm | Inputs and update | Purpose |
|---|---|---|
| No update | Frozen prior; purchased probe results ignored for ranking | Matched-cost attribution control |
| Offset / positive affine | Same probes, nuisance calibration only | Ranking-invariance and measurement-calibration control |
| Small regularized residual correction | Same probes; fixed reference-derived features and shrinkage | Test cross-drug error transfer |
| Identical correction, shuffled probe identities | Same values and budget; preregistered identity permutation | Test whether correctly associated feedback carries the gain |
| Compatible earlier residual-transfer method | Refit only on the permitted reference contexts | Check that complexity adds to the existing method family |

Choose the smallest supported residual model in development: fixed-feature ridge before a richer learned factor model. Lock rank and penalties before the evaluation contexts. Include a distinct zero-purchase prior when evaluating deployment net benefit; the matched-cost no-update arm is for attribution and must not be confused with it.

Two information references can help diagnose failure. Model-predicted probe outcomes are a sanity control if generated by the same prior: they are not new evidence and must not artificially narrow uncertainty as if measured. An independent predicted cheap modality requires a qualified endpoint bridge and a separately frozen mapping. A full-target-information fit or exact best top-k is an explicitly undeployable retrospective reference, never a purchased observation or training input. The former is model-dependent and not a mathematical ceiling.

Primary evaluation is terminal top-k measured utility per context. Record mean paired improvement, harmful versus helpful selection changes, overlap, boundary-ranking errors, probe-to-terminal residual predictability and context/lineage sensitivity. MSE or correlation alone cannot pass the decision gate. Charge the probe batch once per campaign; improvements over many downstream drugs share this expense rather than inventing new independent replicates or multiplying the same benefit.

Proceed only if correctly associated feedback produces a useful, reproducible terminal-utility gain over the strongest frozen prior and simple corrections. A future confirmation requires its lower paired-cluster interval to exceed a defensible predeclared useful margin. Failure at this stage means keeping the strong prior and fixed batch; it does not justify another acquisition-function search.

### 2. Test knowledge-graph contribution without confounding it with acquisition

First hold the same probes fixed and compare representations: structure/target features without graph topology, actual graph, relation-type/node-degree-preserving shuffled graph, and the no-graph prior. Match permissible information, representation size, reference fitting, calibration and compute. Keep unknown targets as missing, not negative. Audit outcome-derived edges, aliases, direction and source snapshots.

If available data contain only drug-target incidence, it may encode the same information as a target-feature vector. Call this an information or representation test; do not claim a multi-hop graph-topology contribution without independently varying topology. Frozen MAP embeddings also contain non-graph modalities; their incremental gain alone is not graph attribution.

Only after a representation benefit passes, hold that fitted posterior fixed and compare a reference-chosen, random/diverse, numerical-value and graph-informed probe panel at the same paid budget. If graph information changes posterior correlations or likelihoods, evaluate that as a model change. It cannot also be called pure acquisition improvement under an identical model.

This ordering uses a small graph or embedding packet and reuses local assets. Retraining MAP or downloading large image archives is not necessary to answer the first question.

### 3. Decide whether adaptive purchases earn their cost

Use the now-supported posterior and compare a strong one-shot batch with a deterministic, at-most-two-batch policy and the same-resource fixed-split control. Preserve no-purchase and stop actions. Choose every batch before revealing its members. Joint terminal value, rather than the sum of marginal information scores, is the appropriate quantity to estimate; approximations must be labeled and checked against realized continuation gains.

Separate two estimands. The disjoint-probe diagnostic measures benefit on later unmeasured drugs. A complete discovery campaign may count actual probe hits, but every arm must then share the full eligible library and an explicitly fixed cumulative endpoint. Do not silently change the terminal set when a drug is measured, or exclude the batch arm's already confirmed hits. Include every setup/probe/failed-measurement expense in cold-start accounting; report common existing paid history separately.

Keep resource caps separate from utility valuation. Real monetary and latency costs need declared conversion weights before subtracting them from phenotype utility. Until quotes/timestamps are available, price curves are scenario sensitivity, not actual NetEVSI validation. Register either useful net superiority or biological noninferiority plus cost saving before confirmation; do not switch from one to the other after outcomes.

Freeze complete-policy calibration and evaluate useful widths, refusal rates, selected/path error and predefined activity strata on separate units. Use a selection-conditional method only after demonstrating its assumptions for the actual interactive policy. Decide whether the study's sample size is sufficient from independent context/culture/plate variation and missingness; otherwise label it feasibility.

### 4. Assign an identifiable role to the agent, then confirm

Same tools and constraints alone are not an Agent contribution. If the deterministic evaluator enumerates the same complete menu and chooses the maximum, an LLM proposing that same action has no distinct decision mechanism to test. A meaningful candidate role is constructing distinguishable explanations and legal measurement bundles under model/context disagreement, or improving supported exception handling. Predefine the remaining degree of freedom and evaluate the resulting terminal effect.

Use deterministic planner, ordinary LLM tool loop and proposed agent; retain the strong batch benchmark. All share model, information, source snapshots, legal menu, deadlines and total budget. Record all repeated runs, invalid actions, recovery, actual API/tool cost and final choices. Scientific gain, interface convenience and workflow reliability are separate claims.

Independent confirmation needs distinct measured units, control randomization, explicit culture/day/plate identities, measurements of both methods' recommended sets, and a registered random sample of unselected drugs to evaluate omissions. An external combination dataset such as BATCHIE tests a different task; secondary PRISM alone does not supply unbiased whole-library confirmation. Early RNA/image observations require a qualified paired bridge to the declared later endpoint. For an early-to-late bridge, both times and the transport model must be explicit; it is not a same-time surrogate measurement. Destructive assays require matched sister cultures rather than pretending the readouts came from one intact cell.

## Literature and plausible contribution

The supplied literature is directionally useful, with the guarantee distinctions above. [BATCHIE](https://doi.org/10.1038/s41467-024-55287-7) already uses probabilistic responses, batch active learning and budget/convergence stopping. This does not establish cost-adjusted terminal stopping for MAESTRO. [BatchBALD](https://arxiv.org/abs/1906.08158) supports accounting for correlated batch information. [MAP](https://doi.org/10.1038/s42256-026-01286-w) supports knowledge-driven transcriptomic response modeling; its reported outcome is not this functional decision or an independent graph-cost attribution.

Shared latent factors and side-information transfer are also established: [Gonen and Margolin, KBMTL](https://doi.org/10.1093/bioinformatics/btu464) and [Ammad-ud-din et al., personalized QSAR](https://doi.org/10.1021/ci500152b). The former's model/prediction sections were checked; the latter was checked at abstract level. The publisher abstract of [PrePR-CT](https://doi.org/10.1038/s42256-026-01202-2) additionally overlaps cell-specific graph transfer for sparsely observed perturbations. [SHIFT-DRP](https://doi.org/10.1021/acs.jcim.5c02453) and [LUDRP](https://doi.org/10.1093/bioadv/vbag246) overlap active drug-response acquisition; this review checked their abstracts, not their full experiments or wet-lab cost claims.

[KnowNo](https://proceedings.mlr.press/v229/ren23a.html) and [sim-to-real adaptation](https://arxiv.org/abs/1810.05687) provide useful design analogies. Their robot scenario/execution assumptions do not prove low-rank biological errors or selected-drug reliability. Existing [source records](../budgeted_feedback_20261011/literature/sources.json) and [review](../budgeted_feedback_20261011/literature/REVIEW.md) retain the previous thirteen citations and reading limits. The older targeted review contains opaque citation markers and a stronger set-coverage formula than the cited single-unit theorem; use resolvable primary links and the corrected claim when preparing a paper. This review does not assert an exhaustive novelty search.

The credible potential contribution is identifying conditions in which a small paid, condition-qualified probe set reveals a reusable drug-dependent context error, improves later drug choices, and supports a useful stop/abstention rule on independent functional measurements. A low-rank correction plus knowledge graph plus an agent is not sufficient novelty. Positive attribution and bounded failure regimes are the evidence that would make the method valuable.

## Bounded engineering findings

Two report-contract issues were reproduced with tiny in-memory inputs. They do not change the present study, whose endpoints are uniform and utilities are small.

1. `decision_report.py:85` checks endpoint equality within each paired campaign, but permits mixing different endpoint units across campaigns in one mean. A viability gain of 1.0 and RNA-correlation gain of 0.1 are accepted as a mean 0.55. Require a common declared utility/endpoint schema, or an explicit predeclared transformation, before pooling.
2. `decision_report.py:88` can overflow the difference of finite values (+1e308 minus -1e308) to infinity; exact sign-flip comparisons then produce p=0 and the CLI can serialize nonstandard `Infinity`. Reject nonfinite derived differences/costs/statistics before inference and serialization.

These are small integrity fixes for a later implementation turn, not reasons to replace the biological experiment or relax its failed gate. The runtime cumulative-budget integration described above is a separate engineering prerequisite for actual purchases.

## Recommended next commitment

Prepare and freeze only the fixed-context, fixed-eight-probe shared-error diagnostic first. Its required outputs are a response/condition/exposure manifest, complete target-column masking check, frozen strong prior and update controls, terminal selection ledger, paired context-level effects and price sensitivity. These decide whether low-rank feedback and graph experiments deserve more work. Keep acquisition, reliability integration and Agent comparisons as conditional follow-ons. No production predictive policy should be promoted from the existing resource-saving result.

[REVIEW_RECEIPT.json](REVIEW_RECEIPT.json) identifies the reviewed inputs, checks, scope and three audit roles. It authenticates this review's inputs and conclusions, not a new scientific experiment.
