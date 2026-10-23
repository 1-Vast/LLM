# Postseal response: specify the ratio-mixture observation law

2026-10-22. Root correctly challenged the original's under-specified endpoint coupling for day5 vehicle-normalized live counts. The sealed original is retained. Its displayed linear mixture is valid for raw additive expected live counts with appropriate starting-population scaling, or suitably reweighted normalized responses; it is not generally valid for the actual normalized endpoint using initial clone fractions. No new calculation, fit or biological value was opened to correct this.

Let p_ir be clone fractions **at the start of the functional assay**, N0_r the initial live population, and R_i(a,c,t) the expected number of live progeny at time t per initial clone-i cell under assay drug a/concentration c. Under independent additive clone contributions,

E[N_r(a,c,t)]=N0_r sum_i p_ir R_i(a,c,t).

For the primary's vehicle-normalized day5 count, the corresponding population response is

Y_r(a,c,t)=[sum_i p_ir R_i(a,c,t)]/[sum_i p_ir R_i(vehicle,t)].

This is a ratio of expected counts, not a claim that the expectation of a noisy count ratio equals the ratio of expectations. A measurement model must address both counts if their noise matters. The same initial fractions in treated and vehicle wells are a plating/randomization assumption to verify. Endpoint barcode fractions taken before further passage need not equal assay-start fractions without an authenticated sample/timing join.

If h_i=R_i(a,c,t)/R_i(vehicle,t), then Y_r=sum_i q_ir h_i with **vehicle-expanded weights**

q_ir=p_ir R_i(vehicle,t)/sum_j p_jr R_j(vehicle,t).

Initial p weights suffice only when vehicle progeny multipliers are equal across clones (or another justified restriction gives the same q). Raw additive counts are already a conditional model: interactions and density effects can invalidate history-independent clone multipliers. These assumptions must be shared with direct/refit controls, not supplied as privileged world-model truth.

IC50 is obtained by fitting a nonlinear functional of the full normalized response curve. It is not the initial-fraction-weighted or vehicle-weighted mean of clone IC50 values. GR metrics also apply nonlinear growth normalization. The proposed future likelihood should therefore use the actual released count/curve observation law; none has yet been fitted here.

**Correct scope of the original nullspace argument:** for raw or denominator-conditioned expected responses, and an authenticated assay-start mixture matrix P, y=P R_a (or d_r Y_r=(P R_a)_r with known d_r=(P R_vehicle)_r). Holding the vehicle law fixed, R_a and R_a+epsilon*v with v in ker(P) leave source numerators and thus source normalized responses unchanged. A later mixture outside the identified row span can change its response, provided its denominator is positive. If working with normalized clone h, the appropriate matrix is Q of vehicle-expanded weights; it is not automatically the endpoint P. No actual P/Q rank has been computed. This argument does not establish any particular separation of fitted IC50 values, and should not be quoted as doing so. Unknown denominators or history-dependent multipliers require the correspondingly broader model rather than an unjustified linearization.

The correction strengthens the need for the released assay/culture/normalization contract and does not create a new mechanism. The literal candidate remains ordinary selection plus ratio-mixture estimation; its distinct-algorithm/old-versus-new-improver gaps remain unchanged. Awaiting sealed independent CDK peer notes before cross-reading their new conclusions.
