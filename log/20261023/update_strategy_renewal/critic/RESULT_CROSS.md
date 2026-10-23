# Independent algebra and implementation review of paired-credit result

2026-10-23. Read root's pre-execution protocol, freeze, exact script and result after completing reciprocal CROSS.md. I did not rerun the script or access biological data. The initial attempted script filename paired_credit_falsifier.py did not exist; the freeze identified the actual paired_credit_check.py, which was then read. Current script SHA256 c7f84021ce776e329171453d4f06d1b69e089379380ff74f4ca5d20ed09e62f8 and protocol bd48d8677ab7eb3ce2e3de23983ee146a4afc18150c351cefa67b2bfae1e0c24 match their pre-execution freeze.

Independent derivation at the symmetric policy: E[e]=0, e^2=1, so d E[r]/d psi=E[r*e]=a. Under independent unit-variance evaluation errors,

- paired: g=a+e*(eps-eps0), mean a, variance 2;
- two independent returns: g=a+(mu1*e1+eps1*e1+mu2*e2+eps2*e2)/2, variance (tau^2+1)/2;
- same-task antithetic: g=a+(eps_plus-eps_minus)/2, variance 1/2.

Thus for a=1 the reported means 1 and variances paired 2, independent 1/2 or 5/2 for tau^2=0 or 4, and antithetic 1/2 are correct. Sharing exactly the same additive error cancels it for both paired and antithetic, yielding constant 1. With the action-dependent baseline B(e)=r(e)=e the estimator is identically zero while the target derivative is 1; this correctly demonstrates why action independence matters.

The script enumerates uniform independent Rademacher coordinates with Fraction arithmetic, computes population rather than sample moments, includes all 16/64/8 configurations for paired/independent/antithetic, and checks frozen input hashes before writing a previously absent result. Repeating irrelevant nuisance coordinates merely repeats outcomes uniformly and does not change moments. I find no arithmetic/result mismatch.

Budget and access limits are material: this uses exactly two equal-price evaluations; both candidate actions and a reference are legal and executable; the same task nuisance is available to both antithetic evaluations; independent errors have equal variance. Antithetic is an ordinary two-action estimator of the same symmetric-policy gradient in this grammar. Restricted edits, unequal costs, shared noisy labels, cached reference amortization, or different task access require a new analysis. The factor of four is not a universal method ranking. This establishes no learned updater, world-model utility, biological result, inheritance or improved-improver effect.

Decision: accept the exact toy result and stop the present paired-credit novelty/cost rationale. It is insufficient to claim biological failure or impossibility of future task-specific update mechanisms. Semantic-witness NO_NEW_CORE_GO also remains unchanged; no rescue fit follows.
