# Independent challenge of I304.v1

Date: 2026-10-30  
Scope: independent challenge of the candidate and the four supplied audit files. I read only the cited older source excerpts needed to check the closest precedents. No code was changed and no experiment was run.

## Executive assessment

I304 is a useful **failure-analysis specification**, but its central algorithmic and practical claim is not established as a new mechanism. The broad loop (proxy prediction, independent functional feedback, adaptive assay selection and score/model revision) is already covered by DrugReflector, MDA and Bayesian active-learning drug screens. The proposed residual distinction, “localize the wrong layer and then locally reuse or quarantine it,” can be represented by a standard hierarchical measurement-error/model-selection model with a latent error-source indicator, posterior predictive checks and cost-aware VOI. I therefore recommend **parking the algorithmic innovation claim** until a qualified paired matrix and a formal separation test show a utility gain over that ordinary model. The candidate may remain as a conditional research hypothesis or an information/identifiability audit.

## 1. Is the central claim covered by recent precedents?

The claim has several parts, and the precedent status differs by part:

| I304 component | Challenge result |
|---|---|
| Functional readout disagrees with an omics/proxy score, then revise the proxy or ranking rule | **Covered in broad operation.** DrugReflector uses paired transcriptomic and phenotypic measurements to refine a screening signature and reports a later hit-rate increase. This is a closer biological precedent than a generic active-learning analogy. |
| An agent proposes/checks hypotheses and chooses informative experiments under a budget | **Covered as a method pattern.** MDA combines candidate model structures, out-of-sample predictive failure, model expansion, Bayesian posterior updating and VoI experiment design. BATCHIE demonstrates budgeted Bayesian adaptive selection in a real drug-screening setting. |
| A disagreement is represented by discrete error sources (response model, proxy-to-function map, batch/readout, both) | **Not found as the exact virtual-cell package in this bounded audit, but not enough for novelty.** A latent model/source indicator and competing likelihoods are ordinary Bayesian model comparison or a measurement-error model. The cross-domain map also finds established fault-diagnosis, behavioral-test and intervention-equivalence patterns. |
| Update only the supported layer; reuse locally and quarantine an affected family/background | **Currently a policy description, not a demonstrated new operation.** Partial pooling/no-pooling, random effects, posterior predictive gating, leave-domain-out refitting and robust outlier exclusion implement the same behavior unless I304 supplies a different objective or a proof of a decision advantage. |
| Improve held-out functional ranking with fewer expensive assays | **Unverified and currently untestable.** The supplied data gate has no open row-level matrix satisfying the required proxy/function identity and splits. |

The bounded search did not find one paper with every I304 label in the same diagram. That is only “not seen in this audit,” not a first-use or novelty result. The broad scientific operation is already occupied, so the claim must be narrowed to a formally specified, empirically superior source-localization policy.

## 2. Can current cheap data identify the proposed layers?

No. The resource status in `data_gate.md` blocks the decisive test:

* OMIX017117 is controlled-access in the inspected snapshot; the compound, dose, donor/well and raw functional pairing needed for this test are unavailable.
* Rhaister Emerald Bay supplies economical drug/cell response support but no independently measured function endpoint, so it cannot separate a response-model error from a proxy-to-function error.
* The eLife RPPA/resazurin resource is one background with nominally different times (24-hour RPPA versus 72-hour resazurin), incomplete row-level pairing/scale details and no qualified cross-background transfer. It can support a contract or descriptive check, not layer attribution or savings.
* LINCS/L1000 joins to PRISM/GDSC are not paired evidence until exposure, dose, time, preparation and endpoint semantics are matched row by row.

Even with a future matrix, the candidate observations do not guarantee identification. A matched proxy repeat tests repeatability; it does not by itself tell whether the response model or the proxy-to-function map is wrong. An orthogonal functional endpoint can share a time shift, batch effect or latent state with the first endpoint. A target/genetic reference only helps if intervention identity, timing and causal relation are qualified. I304 correctly says to abstain when states remain equivalent, but that abstention is a frequent expected outcome under the current contracts, not evidence of a useful layer-specific algorithm.

## 3. Strongest ordinary explanation

The strongest rival is a hierarchical probabilistic measurement model:

\[
p(y,z\mid x,s,\theta)=p(z\mid x,\theta_r)\,p(y\mid z,\theta_f,\theta_b),
\]

with a latent source indicator \(s\in\{r,f,b,both\}\), shared and drug/background-specific effects, replicate and batch random effects, and a posterior predictive check. Standard Bayesian model comparison updates \(p(s\mid D)\); cost-aware VOI chooses a repeat or orthogonal assay; partial pooling reuses information where the posterior supports it; a posterior-predictive gate or no-pooling random effect quarantines a drug family/background when transfer is poor. This reproduces the stated “layer localization + local reuse/isolation” behavior without an agent-specific mechanism.

Other ordinary policies that must be beaten under equal cost are direct functional measurement, complete refitting of the response-to-function map, robust multi-fidelity calibration, random/fixed-panel selection and uncertainty/active-learning selection. A natural-language explanation or role split does not distinguish I304 from these policies.

## 4. Minimal counterexample to generic layer attribution

Take one drug/background, one proxy measured at 24 hours and one function measured at 72 hours. Let the observed joint distribution be the same under two worlds:

* **World R:** the proxy state is measured correctly and the proxy-to-function map is correct, but the intervention-response model extrapolates incorrectly at 72 hours.
* **World F:** the intervention-response model is correct for the proxy state, but the map is wrong because the 24-to-72-hour mapping changes under this drug/background.

Choose the latent state and the two error terms so that both worlds induce the identical distribution for the proxy, its matched repeat, the functional endpoint and any orthogonal endpoint available at that time. With no qualified upstream intervention, every legal observation has the same likelihood under R and F. The factorization into “response model” and “mapping” is therefore non-identifiable. The correct result is to retain the equivalence class (or H_both) and abstain; any layer-specific update would be false attribution. This counterexample is compatible with the candidate's own abstention rule and shows why a generic performance gain cannot be assumed.

## 5. Required modification or stop rule

Before claiming a mechanism, I304 must specify a source model and an identifiability gate:

1. For every proposed observation, publish the predicted distributions under each source state, including batch/time and replicate noise; require a predeclared separation threshold and positive decision utility after assay cost.
2. Quantify the fraction of candidate failures that remain observationally equivalent. Treat that fraction and abstention calibration as primary results, not discarded cases.
3. Use a public or newly released matrix with drug, dose, time, background, preparation/plate, independent repeat, proxy and independent function at matched condition identity. Hold out complete drugs and at least one background or batch.
4. Compare equal initial data and total assay budget against the hierarchical latent-source/partial-pooling + standard VOI rival, direct functional measurement, complete refit, random and uncertainty policies. Primary endpoint: held-out functional utility or fixed-threshold simple regret; secondary endpoint: calibrated source localization and correct quarantine decisions.
5. If the ordinary hierarchical/VOI rival matches I304, or if the data do not permit source separation, withdraw the algorithmic and savings claims and report only the information audit.

## Bottom line

I304 should not currently be promoted as a new virtual-cell mechanism or as a demonstrated low-cost assay-saving method. Keep the explicit error-state ledger, legal-observation contract and abstention language as a disciplined specification. Park implementation and efficacy claims until the paired data gate and the ordinary-model challenge above are passed.

