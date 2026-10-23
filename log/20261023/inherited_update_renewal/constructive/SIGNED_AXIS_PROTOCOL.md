# Frozen exact signed-axis test

Run only after independently sealed API_REVIEW/CROSS; root requested this new check. Root API_CHECK.json and its code have not been read. This test checks the cancellation objection, not root's three checks.

Use API six-dimensional linear setting; controls e1..e4, J_X=I, and q=e5+2e6. Epsilon=1/10 is finite. Lambda_R=0, explicitly testing unregularized target scalar fitting. Two histories: positive case (q,3q); signed-axis case (q,-q). Analytic mean-fit solution s=sum(g_h)/(H+epsilon). All histories have exact same rank-one second moment span(q). Ordinary rank-one basis estimated from their second moment uses q as an arbitrary scale representation. Verify S=q q' times sum of squared history amplitudes and S*q positive multiple of q, rather than handing the direction only to candidate.

Target q, allowed feedback xF=e5+e6,y3, held xQ=e6,y2. Fit alpha=3/(xF.s) unless s0; for s0 any alpha has identical zero output, choose0. Compare exact held prediction/squared error and feedback fit. Positive mean should be nonzero and exactly fit after amplitude rescales. Opposite histories should return mean s0 but ordinary rank-one basis should fit exactly. Print exact rational arithmetic and hashes. No biological result, noise claim, runtime advantage or Level3 assertion. Do not vary parameters after results.
