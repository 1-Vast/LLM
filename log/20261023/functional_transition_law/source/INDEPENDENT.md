# Independent biological review: time-to-function updating

**Decision: one concrete delayed-death update examined; NONE qualified as a new algorithmic law.** An exact VUScope falsifiable restriction is identified, but violation in real data has not been established. A hazard-delay correction needs independent death observations and reduces to ordinary delayed-hazard refitting when implemented as a single lag parameter. No biological fitting or data matrix was used.

## Objective, prior stops, and evidence

Read the full goal and feedback_law_discovery/DECISION.md. The ordinary growth-clock/constant-q mechanism and fixed consistency configuration remain stopped. No old CDK, AML/ALL, CRISPR implementation-strength or exposure-identity branch is reopened. Local rg deduplication found only earlier delayed-death counterexamples, not a saved primary analysis of the source below.

Existing downloaded VUScope primary XML/text: log/20261023/feedback_law_discovery/source/GET2_PMC12904834.*, DOI 10.1093/bioinformatics/btaf679, 4 February2026. This phase made three bounded GETs: two targeted EuropePMC searches (the first included irrelevant clinical mortality hits, transparently retained), then original full text **Genome-wide profiling identifies the genetic dependencies of cell death following EGFR inhibition**, DOI **10.1016/j.jbc.2026.111414**, PMC13133947. REQUESTS.jsonl records URL, HTTP status, timestamp, body hash and purpose; bodies are saved. No numeric supplemental data or author code was retrieved.

The JBC study explicitly says net growth cannot identify the contributions of growth suppression and death. It applies prior GRADE/FLICK methods and observes EGFR-inhibitor growth suppression in several lung-cancer lines while strong killing is concentrated in PC9. FLICK uses SYTOX Green dead-cell fluorescence, an independently lysed time-zero plate and final total-cell lysis; live values are inferred from total minus dead fluorescence. Drug kinetics are fit by existing custom scripts. This provides a concrete precedent for why independent death/total measurements matter; it is not a new birth/death separation method created by us. The article's lethal-fraction/hour values should not be silently interpreted as a directly measured instantaneous per-live-cell hazard.

## What the VUScope formula actually forbids

VUScope specifies f(z,t)=(alpha(t)−delta(t))/(1+10^[beta(t)(z−k_gamma)])+delta(t), where z=log10 dose, beta(t)=k_beta*abs(alpha(t)−delta(t)), and k_gamma is time-independent. Thus, for a nondegenerate dynamic range,

u(z,t) = [f(z,t)−delta(t)]/[alpha(t)−delta(t)]

satisfies **u(k_gamma,t)=1/2 for every time**. It also ties the logit dose slope to the dynamic range. This is a precise surface restriction, not an assertion that every definition of “50% inhibition relative to control” has fixed IC50. A fixed half-range midpoint is different from the absolute dose where f equals half the control; changing the lower asymptote can move the latter.

A constructed incompatible pair is u(c,t1)=1/(1+c/2) and u(c,t2)=1/(1+c), with known asymptotes. The half-range doses are2 and1, respectively, so no common k_gamma can exactly fit both. These positive curves can describe increasingly strong effects over time. They do **not** prove delayed death caused that shift; target engagement kinetics, growth, adaptation, or observation changes could also produce it. Six finite doses with uncertain asymptotes need not identify the midpoint cleanly. A real falsifier must use raw observations and a same-information flexible joint model; fitted full120h GRIVUS is not independent truth for such a test. Delayed death alone does not imply VUScope must fail: evolving asymptotes can capture some delayed changes.

## One explicit candidate: transport an independently observed death-hazard onset

Application: a new temporal functional observation shows that the onset of killing is delayed relative to the source model; revise later viable-count trajectories without pretending the discrepancy is changed basal growth or ATP-per-cell.

Assume legally available live risk counts N(c,t), actual cumulative death events D(c,t), an independently established source birth-rate function b0(c,t), and source death hazard h0(c,t). Under that explicit birth/death model, dN/dt=[b0−h0]N and dD/dt=h0*N. A local estimate of death hazard needs death increments divided by live exposure, not only N(t). For observed intervals define h_obs(c,k)=DeltaD(c,k)/integral_interval N(c,t)dt, with its interval-censoring/measurement uncertainty.

The attempted correction is a shared within-context death-onset shift delta across the observed doses:

delta_hat = argmin_delta sum_(c,k in observed) w(c,k) [h_obs(c,k)−h0(c,t_k−delta)]^2,

h_new(c,t)=h0(c,t−delta_hat),

N_new(c,t)=N(c,s)*exp(integral_s^t [b0(c,v)−h_new(c,v)]dv).

Death hazard is extended as zero before a declared source onset, not evaluated at a fabricated negative-time observation. This operation rewrites an entire future trajectory, preserves positivity, and changes timing rather than a constant-q growth correction or a time-varying potency covariate. It requires the substantive and falsifiable restriction that the same additive timing shift transfers across doses while post-onset hazard shape and birth law remain valid.

However, fitting delta in a shifted death-hazard model is **exactly ordinary delay-parameter refitting**. The above equation supplies no distinct learning algorithm or new conserved biological quantity. Giving it a transport name would not create an innovative updater. An ordinary joint birth/death model with the same delay parameter and observations is an exact operational opponent, not merely a broad model-family analogy. We therefore reject its promotion as a new law before fitting. A more complex transport/hidden-state mechanism is not added to escape this equivalence.

## Minimal counterexamples and genuine feedback requirements

Counts alone are insufficient: N(t)=N0 is compatible with b=h=0 and with b=h=k>0. The latter has cumulative deaths k*N0*t and continuing replacement; the former does not. Their observed live trajectories agree while the death processes differ. Net-count or GR residuals cannot select the correct hazard update. ATP adds another ambiguity because ATP(t)=a(t)N(t); arbitrary drug-induced a(t) changes can alter ATP without changing N. Paired ATP/count disagreement is evidence to calibrate an observation model, not to infer a death hazard or actual exposure strength for free.

A common delay also fails if one dose changes only division while another changes killing amplitude/shape, if the dose-specific latency changes are unequal, or if the birth law drifts. The two-state replacement example is a mathematical construction, not measured biology. The JBC observation of growth-only versus killing responses demonstrates why such decomposition is biologically relevant but does not authenticate paired death observations for the VUScope panel. VUScope's described cell-by-cell imaging counts and CTG do not by themselves supply death-event risk sets, source birth functions, or a true target-engagement clock. Root is independently checking the public manifest; this review does not assume those assets exist.

## Required fair test and stop

A bounded raw dose-time diagnostic could test whether the fixed VUScope half-range/slope restriction causes a repeatable forecast error. It must compare ordinary VUScope refit, a free-time-midpoint joint surface, a strong same-information dose-time direct predictor, and ordinary delayed-hazard/birth-death refit where the extra measurements actually exist. Later comparisons would include continual/replay updates, active acquisition, simple mixtures, meta-updates and equal-budget program search, with identical paid feedback and observations. Post-onset observations or future asymptotes cannot enter one arm free of charge.

An innovation claim requires an explicit operation not identical to these ordinary alternatives and a repeatable functional error that it corrects beyond them. Current evidence establishes neither. The fixed-midpoint restriction is a testable modeling assumption, not a new learning law. No world-model/agent/RSI claim follows. Current next mechanism action is **NONE qualified**; preserve the exact restrictions and do not use delayed-death rhetoric to restart GR correction or ordinary measurement/joint refitting as a new core.
