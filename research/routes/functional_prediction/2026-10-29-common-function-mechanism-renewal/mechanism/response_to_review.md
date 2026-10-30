# Bounded response to the independent initial review

2026-10-29. I read `../review/initial_assessment.md` after the candidate had been frozen. I accept its endpoint objection and parameter-domain clarification. This is one response concerning the existing model and its assay interpretation; it adds no hypothesis, data access, calculation run or proposed experiment. `candidate_v1.md`, `developed_mechanism.md` and the original review remain unchanged.

## The observation unit must be a challenge-entry cell, not an original founder's whole family

The phrases “one-colony-per-founder” and “founder-survival endpoint” in the developed candidate are ambiguous. They must not be read as scoring whether any descendant of one **original pretreatment founder** succeeds. The intended additive interpretation is:

`one original type-z unit -> N_z viable cells at B entry -> challenge each entry cell separately -> count the successful entry cells`.

Here `N_z` is a nonnegative random integer and `w_z = E[N_z | z]`. Let `Y_zi` be the binary reproductive-success outcome for the i-th individually isolated **challenge-entry cell**. Under the stated unchanged-response null, each existing descendant has conditional expected outcome `b_z` under the same B challenge, including conditioning on N_z and the relevant preparation information. The additive output is

`S_z = sum_(i=1)^N_z Y_zi`, so `E[S_z | z] = w_z*b_z`.

Linearity of expectation does not require the Y_zi to be mutually independent. It does require their conditional means to remain b_z under the defined null. Competition, density dependence, interference, descendants with changed response states, or selection dependent on an unaccounted challenge-response variable can violate that mapping. Those conditions cannot be silently absorbed into a claim that all nonconversion mechanisms were excluded.

For this binary **entry-cell** outcome, `b_z in [0,1]` and hence V=1. An original founder may supply several successful entry cells, so S_z can exceed one. V bounds the outcome per challenge-entry cell; it does not bound S_z per original founder. All counts, sampling/dilution factors, m, U and response denominators must use that distinction consistently. Within-family and within-preparation dependence must remain in uncertainty analysis; separated endpoints do not create independent biological preparations.

Accordingly, the intended readings of the frozen wording are:

- “one-colony-per-founder” means at most one scored colony from each individually isolated **cell entering B**, with colonies summed over those entry cells;
- the thought example's “founder-survival endpoint” means that same per-entry-cell probability, not success of the original pretreatment family;
- the proposed qualification in item 1 requires isolation/counting at B entry and an additive endpoint. It does not claim that this assay mapping is available in the inspected public resources.

This is a necessary correction to the proposed assay wording, not merely a stylistic preference.

## Whole-family binary success is a different, nonlinear endpoint

If one instead scores `F_z = 1{at least one descendant succeeds}` for an entire original pretreatment family, then for a deterministic number n of descendants with conditionally independent successes of common probability b,

`E[F | N=n] = 1-(1-b)^n`.

For random N under those conditional-independence and common-b assumptions,

`E[F] = E[1-(1-b)^N]`.

It is generally neither `E[N]*b` nor `1-(1-b)^E[N]`. Without conditional independence, even that expression must be replaced by the relevant joint failure probability. Therefore the whole-family binary endpoint cannot be inserted into `E[wb]`, the sharp interval or the inverse frontier as if it were the additive entry-cell output. No replacement bound for that distinct endpoint is proposed here.

Likewise, bulk CFU after challenge growth can be additive in an appropriate assay yet exceed one per challenge-entry cell. Its V=1 claim would still be invalid. Clumping, filamentation, colony merging or nonlinear signal conversion can further break additivity. The present OD/CFU/CTG resources remain unqualified for the proposed V=1 interpretation.

## Explicit mathematical domain and endpoints

The nondegenerate theorem assumes finite `U>0`, finite `V>0`, `0<m<=U`, `0<=q<=V` and `0<=r<=V`, on one common reference probability space, with `0<=w<=U`, `0<=b<=V`, `m=E[w]`, `q=E[b]` and `mr=E[wb]`.

Within that domain, the interval remains

`max(0, V-U*(V-q)/m) <= r <= min(V, U*q/m)`.

For `0<q<V`, its sharp inverse remains

`U_required(V) = m*max(r/q, (V-r)/(V-q))`.

The endpoint rules are explicit:

- q=0 permits only r=0; q=V permits only r=V. In either compatible case the smallest U is m. An incompatible r has no finite-U representation under that bounded null. Do not evaluate the displayed ratios through 0/0.
- With interior q, r=0 and r=V are valid and are attained by the existing two-type construction; no special continuity assumption is needed.
- V=0 is a separate trivial case: q=r=0 and U must be at least m. It is outside the displayed ratio formula.
- m=0 leaves r undefined and is excluded. For m>0, U=0 is impossible.
- m>U, q outside [0,V], or r outside [0,V] fails the stated observation/parameter contract before the inverse can be used. Such a failure alone does not identify induced susceptibility.

Any empirical application must handle joint measurement and bound uncertainty before deciding which domain or endpoint case applies. Rounded zeros or apparent saturation do not certify exact support endpoints.

## Effect on the conclusion

The independent review's algebraic assessment stands: the bounded-moment theorem, inverse and sharpness construction remain unchanged for the additive model. The correction narrows and clarifies its proposed assay mapping. If “founder” had been interpreted as a whole original pretreatment family, that proposed application would be invalid and would require a different mathematical model; it is not covered by the present result.

No source now qualifies the full mapping, U, V, reference distribution and independent-unit contract. The candidate remains parked as a conditional analytical diagnostic. No Agent advantage, empirical exclusion, practical cost saving, new biological mechanism or theorem novelty is claimed.

Activity for this response: two local reads and this Markdown write; zero network/API, raw outcome access, scientific execution, new hypothesis or changes to frozen records. Native effective model/tokens/cost remain unknown.
