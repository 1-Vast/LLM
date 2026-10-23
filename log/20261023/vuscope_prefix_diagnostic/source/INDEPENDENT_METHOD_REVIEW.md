# Independent biological/method review before a 72→120h diagnostic

Scope: read saved VUScope original primary Methods2.2/2.6/2.7 and Results3.2; saved Zenodo manifest/archive-name/README metadata; SCHEMA_METADATA_ONLY.json; and the archive's preprocessing.py, utils.py and fit_surface.py **as text only**. No author code was executed, numeric data member decoded, outcome value inspected, new GET issued, or critic report read. The root-reported early-prefix display failure does not make this external confirmation; this reviewer did not open SCHEMA.json or its displayed values. This is an independent design review, not review of an as-yet-unwritten final executable protocol.

## Exact six-parameter model and units

With d=log10(positive concentration) and t in days since the chosen normalization origin,

alpha(t)=a_alpha*2^(k_alpha*t)/[(a_alpha−1)+2^(k_alpha*t)],
delta(t)=a_delta*2^(k_delta*t)/[(a_delta−1)+2^(k_delta*t)],
beta(t)=k_beta*abs(alpha(t)−delta(t)), gamma(t)=k_gamma,
f(d,t)=[alpha(t)−delta(t)]/[1+10^(beta(t)*(d−k_gamma))]+delta(t).

Parameter order in released utils.py is k_alpha,a_alpha,k_beta,k_gamma,k_delta,a_delta. The original function predicts initial-normalized **cell counts**, not log counts. README's ambiguous “normalizes ... and log10-transforms them” does not override preprocessing.py: it log10-transforms **doses only**. Raw count, normalized count and log count are different endpoints; the diagnostic must name which is scored.

For alpha!=delta, the dynamic-range-normalized midpoint u=(f−delta)/(alpha−delta) obeys u(k_gamma,t)=1/2. This does not fix the dose giving 50% of untreated count when delta varies. Beta's dependence on the dynamic range is a second simultaneous restriction. A free gamma(t) comparison isolates one relaxation only if all other parameter/bound/loss choices are matched; a wholly different model win cannot be attributed solely to fixed gamma.

The released bounds constrain k_alpha,k_delta to[0,2] per day; a_alpha,a_delta and k_beta are nonnegative; k_gamma lies inside the tested log-dose range. a below1 still gives a declining trajectory for positive k, so nonnegative k does not by itself exclude count shrinkage. Exactly a=0 at t=0 yields a numerical0/0 boundary; a documented positive epsilon bound is a numerical implementation restriction, not an observed biological finding. The manuscript permits real k, so code-bound and manuscript-family claims must remain separate.

## Prefix normalization and calendar time

The released configuration discards elapsed times below6h. Preprocessing renames the remaining time columns so6h becomes zero, divides each well's subsequent count by its own retained initial count, and finally converts hours to days. The scientifically clean diagnostic uses the actual original elapsed-time field for information exclusion: **no observed outcome with elapsed time>72h may enter fit, normalization, quality selection or optimizer choice**. The 120h target is an actual future measurement, not a full120h model fit or GRIVUS.

If the origin is6h, fit t=(elapsed−6)/24, prefix6..72h, and forecast actual120h at t=114/24 days. The author's native72 wildcard is divided by24 and generally applied to already shifted time without subtracting6h, which can admit actual78h in a regular3-hour export. That is a code-path concern, not proof about the authors' complete executed experiments. Do not reproduce it in a hard72h diagnostic. Preserve actual timestamps explicitly rather than infer them from column offsets or a date string.

N6 normalization is lawful because its denominator is prefix-observed and gives f(d,0)=1. It must be per-well, using no late controls, global120h minimum/maximum, late viability exclusions, or outcome-selected normalization. An observed N6<=0 cannot be divided; its handling must be frozen and reported before inspecting late outcomes. Noise in a shared denominator correlates all times, so normalized observations are not independent replicates. A baseline6h count forecast can be multiplied by that known N6 if absolute-count error is wanted. If scoring N(t)/N6 instead, call it raw-measurement-derived normalized count error, not unnormalized absolute cell-count error. Both differ from model-derived GRIVUS.

Drug-treated counts need not be divided by future untreated counts for this task. If a ratio to control is introduced, actual late control is also a target and cannot be supplied only to selected methods. DMSO wells can support prefix control characterization; zero concentration must not be passed as an ordinary finite log dose or silently replaced with an arbitrary pseudodose. An analytic d→−infinity control limit or explicit exclusion/independent control model must be specified.

## Release-specific preprocessing and fit discrepancies

Released preprocessing selects global sorted dose positions[0,2,4,5], reducing the dose grid, before splitting drug curves. This is an outcome-independent metadata rule, but it is not automatically equivalent to all six doses described in the manuscript. A diagnostic may freeze all available positive drug doses or faithfully use that subset; state which before outcomes and give every method the same observations. Do not select the subset by later error or drug-specific fit success.

The released least_squares solver minimizes unweighted **raw residual squares**. It then chooses among parameter starts using a MAPE-like score, called with prediction as the first argument; the score therefore uses prediction, rather than observed count, in its denominator. It is inaccurate to describe this literal implementation as direct optimization of observed-denominator MAPE. A clean independent diagnostic can use declared SSE and select the best prefix objective, or audit the literal code choices separately; neither should be mislabeled exact replication. The finite multistart set, bounds, convergence/failure handling and optimizer calls must be frozen and recorded. A late-error-selected start is forbidden.

## Replicate, control and inference grouping

Preserve archive/file, vessel/plate label, cell line, drug, concentration, wellID, replicate metadata and real time before any averaging. The headers share vessel labels between LN229/LN308 and between T98G/UW228-3; do not claim four independent physical plates solely because four files exist. The metadata seen so far does not authenticate independent biological batches or a particular replicate count. A repeated timepoint from the same well is longitudinal measurement, not an independent sample; wells within a dose/plate and shared controls are likewise not independent biological tasks.

Drug-specific curves can average or jointly fit technical wells only by a frozen rule. Evaluate all predeclared eligible drug/line profiles with identical targets, including fitting failures; do not retain only favorable convergence cases. Aggregate at least by dose/drug/line so abundant timepoints or wells do not manufacture sample size. A single-plate, four-line release supports an exploratory within-assay extrapolation screen, not population-level biological inference or external validation. Any uncertainty interval must respect the small grouped design; no time-row bootstrap may masquerade as independent-biology confidence.

## Strong comparisons and allowed claims

At minimum compare the six-parameter family to a matched ordinary joint refit relaxing gamma's constancy, a flexible same-information dose/time predictor, and simple per-dose extrapolation/persistence controls. Ordinary recent-window log-linear or logistic extrapolation is a valid baseline even though renaming it as a new growth-clock law is stopped. Keep doses, times, controls, prefix outcomes, optimizer/tuning opportunities and forecast horizon matched. A flexible model may overfit; tune only within prefix histories or use frozen settings, never the hidden72→120 errors. Additional parameters and solver work must be reported.

The primary target should be actual later count measurements, preferably all predeclared times in(72,120] plus a separately reported120h endpoint, under an explicit normalization. Forecast error against a full120h fitted surface is not raw-target validation. MAPE can explode at zero/near-zero counts; an absolute/squared normalized-count metric avoids arbitrary denominator rescue and must be chosen before targets. A dose ranking metric, if used, remains within the tested cell/drug/dose panel and actual assay duration, not clinical potency.

A credible failure of the restricted family requires a stable same-information advantage over a competently fitted baseline, not merely finding one unstable asymptote fit. Such evidence would establish a response-surface limitation or ordinary forecasting advantage. It would not identify delayed death, irreversible commitment, ATP-per-cell change, target engagement, a new updater, virtual-cell necessity, agent value, inheritance or RSI. No death/washout/commitment observations have been authenticated here.

Recommendation: proceed to a frozen raw-observation prefix diagnostic once its executable choices satisfy these contracts and independent review. No numerical result or new mechanism GO is asserted by this design review.
