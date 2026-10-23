# Interval hazard correction after constructive challenge

Constructive identified a real discretization limitation in the independently sealed candidate. Source accepts it. DeltaD/integral N is a live-risk-weighted interval-average hazard, not an instantaneous hazard at t_k. Regressing it directly on h0(t_k−delta) can turn unequal interval widths or within-interval risk weighting into a false estimated onset shift.

The physically aligned ordinary delay fit instead predicts each observed death increment using

DeltaD_hat(c,k; delta) = integral_(interval k) h0(c,v−delta) * N_observed(c,v) dv,

and fits those increments with their legal measurement/interval uncertainty. This still requires observed risk trajectories and genuine death increments; point sampling does not provide their integrals for free. Inferring unobserved within-interval curves introduces explicit ordinary modeling assumptions.

This is a correction to the candidate's measurement contract, not evidence of a new operation, a rescue experiment, or reversal of NONE qualified. It remains ordinary death-delay parameter fitting and does not resolve birth/observation identifiability. The prior independent report/seal are retained unchanged.
