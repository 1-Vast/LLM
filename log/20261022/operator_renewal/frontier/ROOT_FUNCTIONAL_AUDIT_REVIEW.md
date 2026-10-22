# Opposing check of root's continuous optimum and uncertainty stress

2026-10-22. Read root FUNCTIONAL_AUDIT_PROTOCOL.md, FUNCTIONAL_AUDIT_RESULT.json and audit_functional.py after my independent functional critique was sealed. I did not run root's writer or change its artifacts. A separate implementation in verify_root_moment.py reads only the saved synthetic result and directly rebuilds the original ratios from exact designed means.

**The claimed fixture-wide continuous optimum is supported.** Independent calculation uses the simplified upper bound U(b,s)=s-(b-s)^2/(1-b)-(b-s)^3/(1-b)^2, rather than root's affine dual construction. For f(c)=L(a,r_i c)-U(b,r_j c),

    f''(c)=6 r_i^3 c/a^2 + 2 r_j^2/(1-b)
            +6 r_j^2 (b-r_j c)/(1-b)^2 > 0

throughout the valid interval. Independently computed f'(max C2)=-625450/691757<0. Therefore f' is negative across the interval and the global minimum is at max C2. It equals **10919/143748**, strictly above the conservative original **11841/170368**. The original per-gene extremizers can be chosen independently at the same common c2; root constructs all three simultaneously and verifies the pooled constraints. Thus this is an attained sharp shared-gauge lower contrast, not only a finite-grid observation. Root's finite grid checks alone would not prove the all-point claim, but its factorized dual proof and this derivative proof do.

I also rechecked the explicit saved probability laws for the 3/4 and 1/2 hypothetical anchors: nonnegative masses/support, unit total mass, all first and second moments, shared ratios and negative fourth-moment difference. **30 exact assertions pass** in ROOT_MOMENT_VERIFICATION.json. The negative differences are exactly -7101600829809/3298324480000000 and -23842384422271/18031749120000000.

These stresses show existence of alternative admissible worlds at those hypothetical anchor values. They do not estimate assay noise, establish a confidence interval, locate a sharp calibration-tolerance threshold, or prove that a real anchor is inaccurate. The true-anchor no-reversal grid entry is harmless because the continuous certificate already proves the stronger result. Root's claims are appropriately restricted to one designed fixture.

The stronger sharp certificate supplies the full optimized ordinary moment comparator discussed in my first review. It reinforces the positive mathematical information lemma and removes any need to compare against an artificially expensive grid solver. It does not establish new-method superiority or prior-art absence. Biological interpretation still requires the same pool's absolute survival anchor, a valid exposure-composition law and joint finite-sample uncertainty. No outcomes, fits, new sources or biological experiments were used in this check.
