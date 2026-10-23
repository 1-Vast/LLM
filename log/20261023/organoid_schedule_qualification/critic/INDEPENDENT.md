# Independent critic: organoid schedule qualification

Status: source-method qualification only; no new numeric response dataset read or fit, no current-phase source/peer report read, no GET. Evidence is cached primary XML `log/20261023/rechallenge_task/root/organoid_primary.body`, Science Advances DOI 10.1126/sciadv.adt1851 / PMC12309667. Author-reported outcomes below are not project replications. Archive acquisition is not asserted.

## Existing contribution and narrow opportunity

The primary already combines real microfluidic spheroid/PDO assays with Gryffin Bayesian optimization of drug concentration, order and duration. Viability CVexp and a Bliss-derived combination index CI are fed back between experimental batches. Consequently an agent recommending schedules, updating a surrogate and recommending another batch is not by itself a new contribution. Exploration/exploitation, domain refinement and termination are manually changed in the reported campaign. Future transfer learning and LLM-assisted optimization are discussed as prospects, not demonstrated inherited update methods or improved improvers.

There is a useful limited opportunity: test prediction of an entire subsequent measured batch from preceding batches under a documented action domain and objective. A short ordinary diagnostic can be scientifically useful without pretending this establishes a virtual cell model or RSI. Actual readiness depends on authentic regimen, iteration, assay and replicate mappings in released files, which this review has not inspected.

## Actual biological tasks and outcome limits

MCF-7 spheroids use DOX, 5-FU and CPA. Concurrent optimization uses dose-response singles and CVtheor equal to the product of the three single-drug viabilities. Sequential optimization fixes the selected concentrations and explores six orders over a total 48 hours. The duration grid changes from four to two hours and the search is switched manually toward exploitation. The target CV50% was not achieved. The selected sequential regimen DOX8h, 5FU32h, CPA8h yields author-reported viability about65%, similar to the concurrent result. The reported75% exposure reduction is a concentration-duration comparison, not demonstrated normal-tissue toxicity reduction. Ki67 differs despite similar viability; these endpoints cannot be substituted for each other.

The breast PDO experiment is one line, described in Methods as established from a PDX, using olaparib and IBET-762 over96 hours. It is not a series of independent patient tasks. Sequential scheduling at the selected concentrations performs substantially worse in the reported best case (CV87%) than concurrent treatment (CV42%); the sequential target50% also fails. This is useful negative evidence against a universal sequence advantage. Moving from MCF-7 to this PDO changes model, drugs, duration and objectives together, so it does not cleanly identify inherited-policy transfer.

The LIVE/DEAD endpoint uses calcein-AM/PI image fluorescence intensity and control normalization. It is not a physical count or single-cell death-time trajectory. Values above100% can be meaningful under the measurement contract and must not be clipped automatically. Destructive Ki67/H2AX validation is a separate endpoint, not an established per-array early-state input. Arrays, rows and wells may share treatment and device effects; biological replicate IDs and hierarchy must be authenticated before independence is claimed. The primary has inconsistent generation wording and some apparent regimen labels; exact table/schema reconciliation is required rather than silently repairing identifiers.

## What logs can and cannot validate

Three questions must remain separate:

1. Whole next-batch endpoint prediction given only earlier batches. This can be evaluated chronologically if exact domains, chronology and replicate grouping are available.
2. Retrospective finite-pool selection among regimens whose responses were measured. This can be meaningful under explicit pool restrictions, but measures that selection task only.
3. Counterfactual adaptive optimization by a new policy. Sparse Gryffin trajectories do not supply outcomes for unmeasured recommended schedules. A fitted surrogate used as an oracle would favor its own assumptions and cannot establish improved real experimental optimization.

Later optimization generations are adaptive observations, not independent later research tasks. A world dynamics contribution is also not established merely because a predictor accepts ordered actions: no within-regimen observed cell-state trajectory is established here. A terminal schedule-response predictor is a mandatory direct control.

Information parity requires that domain refinements, human constraints and initial data be either supplied equally or frozen under an authenticated chronological protocol. In particular, concentrations chosen using future concurrent outcomes cannot be treated as an earlier prior. A duration-matched single-drug comparator is required for sequential Bliss claims; full48/96-hour single curves cannot be multiplied uncritically for shorter individual exposures.

## Minimum strong controls and falsifiers

For chronological forecasting, compare a direct full-regimen model (order, each duration, concentration and permitted assay context), simple schedule-specific/pooled means, and ordinary sequential refitting. Use batch/biological replicate aggregation, proper uncertainty, and both absolute error and decision-relevant ranking under a frozen endpoint. A dose-only model is an insufficient direct baseline.

If counterfactual response support or new experiments later permit actual search, the exact original Gryffin configuration with matching constraints, initial batch and assay budget is essential, alongside ordinary GP/categorical BO, random or space-filling search, and simple mixtures. Count failed assays, single-drug calibration and validation assays when comparing experimental budgets. Equal software-search and model-selection budgets are needed if an updater is proposed.

A candidate reusable updater must be specified as an actual algorithm and transferred unchanged to independent subsequent tasks. A proposed RSI strategy must additionally improve subsequent updater discovery compared with an unchanged strategy at equal budget; reporting another successful refit is insufficient. No such candidate mechanism or supporting inheritance evidence follows from this primary alone.

Proceed locally only if chronological eligibility and authentic objective/response mapping can be reconstructed. Stop a forecast claim if it requires future selected parameters, future domain decisions or validation outcomes. Stop an arbitrary search claim if off-policy outcomes are unavailable. Stop a mechanistic/updater novelty claim if its benefit vanishes against same-information direct/refit/BO controls or reduces to a simple mixture. Failure of a local source to support these claims is not a global reason to stop other lawful small diagnostics.

## Independent recommendation

QUALIFY LIMITED SCHEDULE-RESPONSE FORECAST OPPORTUNITY, CONDITIONAL ON RELEASED SCHEMA. DO NOT QUALIFY WORLD-MODEL, INHERITANCE OR RSI SUCCESS. The task has real functional feedback and a helpful opposite biological result, but substantial prior Bayesian schedule optimization and limited independent task diversity make a minimal direct-model test the next defensible step. No additional editor, agent hierarchy or latent state is justified by this evidence.
