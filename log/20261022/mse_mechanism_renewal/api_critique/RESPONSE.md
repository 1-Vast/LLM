## Verdict up front

**Demote.** No substantively new core survives the critique. The candidate reduces to a supervised transformed-response residualization with a sign target, and its proposed drug-ranking line is either algebraically inert (common correction) or an ordinary drug-dependent regression (not new). I keep the same candidate only in a demoted, explicitly conventional form, and I do not introduce a replacement.

## Defect-by-defect

**1. c is continuous overlapping abundance, not indicators.** Accept. The prior reply's `{0,1}` framing is wrong. Any repair must treat `c_g ∈ R^13` as measured continuous composition abundances with parent/subtype overlap. No latent indicators, no unobserved fields. This alone does not kill the candidate, but it removes the "indicator nuisance" reading and forces the model to be a plain continuous-covariate regression.

**2. Logistic P(s≠0|c) does not identify E[s|c].** Accept, and this is fatal to the stated subtraction. `P(s≠0|c)=P(+1|c)+P(−1|c)` is invariant to flipping the conditional sign mean. The same `q` is compatible with `E[s|c]=+q` or `−q`. Therefore `bar_s_d − Ê[s_d|c]` is **not computable** from the specified fit. A minimal repair would require fitting a signed-mean model, e.g. `E[s|c]=tanh(w^T c+b)` or a two-class softmax giving `P(+1|c)−P(−1|c)`. But that repair is exactly ordinary signed-response regression, so it does not rescue novelty. As written, the operation is undefined; repaired, it is conventional.

**3. Common nuisance correction leaves TopK unchanged.** Accept. If `m(c)` is drug-independent, subtracting the same scalar from every `bar_s_d` cannot reorder drugs; TopK is invariant. So the "probe feedback alters drug ranking" claim fails for the stated line. If drug-dependent signed probabilities are intended, the extra operation is a per-drug conditional model `P(s=+1|c,d)`, i.e. response regression on drug features — ordinary transformed-response regression/residualization with the same information. The conventional comparison must include this, not just linear bivariate means. Accept that narrowing.

**4. Single-well identity does not license inversion; sign residual ≠ joint positive raw depletion.** Accept. In the simplifying example `RCN−RCF=(M/M0)(T0/T−1)` is total retained-count change, not an identified control artifact versus genuine cancer reduction. Because the source uses separate medians/averages, the identity does not authorize inverting aggregate scores. Nothing in the sign residual alone defines a source-relative or therapeutic terminal utility, and nothing connects it to joint positive raw depletion of both RCN and RCF. A repair would need an explicit terminal utility, e.g. a declared monotone function of raw paired depletion with a stated direction and a stated control-relative normalization. That is a **new objective definition**, not a property of the sign residual, and it is not specified here. Without it, the ranking target is unmoored from the stated goal.

**5. Model/procedure transfer ≠ improved discovery capacity.** Accept. Learning `w,b` and showing better cross-group ranking is transfer of a fitted procedure, not evidence of improved capacity to find future improvements. A genuine test requires identical fresh predictor/program start and identical later search/feedback budget for the changed improver. **No such operation is specified.** So the "improver" claim is untested by construction.

**6. Difference from one baseline ≠ novelty; absent citation ≠ novelty.** Accept. Exact transformed-response residualization is ordinary supervised prediction; a distinct output target is not a new learning rule. Systematic difference from a bivariate conditional-mean ranker is not decision gain, and an imprecise gain estimate is not proof of absence. Absence of a citation is not positive evidence of novelty.

## Minimal repair that preserves a new operation?

I cannot construct one from the fixed batch. The only candidate repairs are:
- fit a signed-mean model (repair of #2) → ordinary signed-response regression;
- add drug-dependent probabilities (repair of #3) → ordinary drug-response regression/residualization;
- define a terminal utility on raw paired depletion (repair of #4) → a new **objective**, but not a new **operation**, and it is not specified.

None yields a substantively new operation. The "sign-disagreement frontier" is a relabeling of supervised residual ranking. **Demote.**

## Nearest conventional primary method

For signed-probability / nuisance residualization, the nearest conventional family is **supervised residualization / outcome regression with a transformed response**, i.e. fit `E[g(y)|x]` and rank residuals. Canonical primary references:
- Rosenbaum & Rubin (1983), *Biometrika* 70:41–55, DOI 10.1093/biomet/70.1.41 — propensity/residual adjustment framing (nuisance correction).
- Robins, Rotnitzky & Zhao (1994), *JASA* 89:846–866, DOI 10.1080/01621459.1994.10476818 — semiparametric residualized estimating equations.
- For signed/probability targets specifically, ordinary **logistic or softmax regression on a signed label** is the standard; no separate "sign-residual frontier" primary method is known to me.

I am **not confident** of a specific 2025–2026 primary work that is the direct nearest neighbor; I therefore decline to name one rather than invent a citation. (Marked: no verified recent primary citation supplied, consistent with the request.)

## What algebra establishes vs. what remains untested

**Established by algebra:**
- `P(s≠0|c)` does not determine `E[s|c]`; the subtraction in #2 is undefined as written.
- A drug-independent `m(c)` leaves TopK invariant (#3).
- The single-well identity is a total-count change, not an identified artifact/genuine split (#4).
- A distinct output target is not a distinct learning rule (#6).

**Untested / undefined:**
- Any finite-budget utility gain from the sign residual.
- Any connection between sign-residual ranking and joint positive raw depletion.
- Any improved discovery capacity under matched fresh start and matched search/feedback budget (#5) — no such operation is specified.
- Any source-relative or therapeutic terminal utility — not defined.

## Conclusion

**No new core survives.** The candidate is demoted to: *supervised signed-response residualization on continuous overlapping composition abundances, with an unspecified terminal utility and no matched-budget improver test.* That is conventional. The bounded scout ends here; no further candidate is introduced.