# H_MEAN.v1 — frozen before response access

2026-10-29. This protocol and the frozen design below are canonical together. No control/drug response has been accessed. This is one empirical prerequisite check under the parent2-run ceiling, not a novel co-learning algorithm or a biological rate-validation study.

## Hypothesis and scientific use

On these seven fixed vehicle plates, does a common raw-count exponential mean adequately predict the validation-row mean trajectory relative to a one-curvature-parameter rival? A reproducible conditional prediction gain for curvature blocks the common homogeneous-mean default for the parent covariance-to-rate interpretation on these frames. It does not identify the cause. Every outcome stops this test; no outcome authorizes drug-specific birth/death interpretation, white-noise validation or code promotion.

Read `design_worker/recommended_design.md` in full for the exact estimand, source assumptions, formulas and scope. Its content is frozen by the SHA256 in protocol_receipt.json; any scientific change requires a preserved version and review. This protocol adds only the following explicit numerical/IO contract before independent review.

## Data, frozen roles and information

Original HTS001 size/hash and metadata are in record.md and metadata_qualification.json. Access only rows with drug1 exactlycontrol, concentration0, and time<72hours. Parse cell.count as an unrounded finite nonnegative float ONLY after those metadata conditions. Do not access/convert count values in drug rows or later frames. Missing/conflicting source identity, cells, plates, well/time coordinates, unit or required control count stops the operation. No deletion, imputation, interpolation, response-based exclusion or window change.

Cell order BR1,DS3,DS7,DS8,DS9,MGH,PC9. Each cell has one fixed plate,28wells,columns02/23,rowsB–O. TrainB,D,F,H,J,L,N (14trajectories); validationC,E,G,I,K,M,O (14). Retain complete observed trajectories in each role, using all9–15available pre72frames. No validation count estimates any nuisance, including initial amplitude or scale. Raw training and validation arithmetic means are compared at the same observed irregular frames. Frame weights are equal within plate; plate weights equal across the seven fixed plates. No culture-population or certified physical-replicate inference.

## Models, score and deterministic numerics

Use the exact m0,m1,D_c,Delta definitions in recommended_design.md: exponential mean exp(beta0+beta1*u) versus exp(gamma0+gamma1*u+gamma2*u²), u spans each plate's first to last eligible frame. The score is normalized heldout raw-mean squared-loss difference using the TRAINING mean-square count magnitude s_c². Means, nuisance parameters and scale are refit independently on every resampling draw.

For optimization, divide training means by s_c=sqrt(mean(ybar_train²)); fit normalized exponentials, add log(s_c) back to fitted intercepts for raw predictions. This is algebraically the same raw-count least-squares objective. Baseline start(log(mean(ybar_train)/s_c),0); rival start(converged baseline coefficients,0). SciPy least_squares,methodtrf,analytic Jacobian,ftol=xtol=gtol=1e-10,max_nfev200,unbounded parameters,double precision. Solver failure/nonfinite values/nonpositive training scale/unresolved nestedness violation makes the run INCONCLUSIVE; no extra starts or dropped fit/draw. Nestedness tolerance is1e-10*(1+baseline normalized training SSE), a numerical resolution rule, not a scientific effect margin.

Report original fitted parameters/predictions/training SSEs and all7D_c plus Delta. No fitted curvature-sign hypothesis is added. The covariance and autocorrelation diagnostics are NOT RUN.

## Conditional stability and stop rule

B=500,seed20261029,NumPy Generator(PCG64). Generate one integer draw array with shape(500,7,2,7),integers0..6. Axes are draw,fixed-cell,role(train/validation),rowblock. Each selected row contributes both columns and its entire temporal vector. Sample train/validation roles independently within each fixed plate. Store the draws and their hash so a separately written verifier can use the same declared resampling inputs without reading primary numerical results first.

Refit every training nuisance and scale on every draw. Report allDelta*,linear-interpolated empirical5th/95th percentiles and fractionDelta*>0. This is conditional row-block resampling stability, NOT a calibrated confidence interval, p-value or independent biological uncertainty. Unknown cross-row/plate/culture dependence remains unrepresented.

If numerical checks pass and the5th percentile isstrictlypositive: CONDITIONAL_HELDOUT_CURVATURE_GAIN, and stop using the common exponential mean as the default for this particular control-prediction task. If95th isstrictlynegative: EXPONENTIAL_PREFERRED_IN_THIS_COMPARISON, without model/white-noise validation. Otherwise, or any failed metadata/numerical/resource check: INCONCLUSIVE. No practical biological effect margin or power is certified. Seven per-plate scores describe contributors, not seven extra hypothesis claims.

## Execution and verification

Installed maestro Python; perimplementation CPU<=120s,wall<=180s,peak working set<=512MiB,cooperative checks/measurements with an outer timeout,not OS hard limits. One primary run and one independent written verification under the same scientific-test record. A receipt is written before count parsing; no automatic replay. No network,author-code execution,installs,GPU,new wetlab,protected outcomes or core changes.

The fresh reviewer receives this protocol and original sources without a desired outcome. Preserve initial objections before any response. Execute only after it finds the test interpretable under stated limits. The verifier independently reads the original whitelist and implements the frozen equations; save its point/bootstrap outputs before comparing to primary output. Numerical disagreement or protocol drift remains visible and blocks adopting the affected result; do not keep rerunning until agreement.
