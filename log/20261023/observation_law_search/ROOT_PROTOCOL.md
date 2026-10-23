# Snapshot-equivalence and intervention decision: bounded mathematical falsifier

2026-10-23. Before execution. No new biological values or model tuning. HEAD 47a0e2dea5a7dd42379fa17eb3621caf6bd0114c. Previous goal turn NO_PROGRESS (status reconciliation only). Full objective ACTIVE / NOT_ACHIEVED.

## Question and prior boundary

Could removing capture ambiguity alone make a snapshot-fit drift/diffusion/growth decomposition uniquely ground intervention choices? Test with ideal continuously known absolute densities, no capture error. These are classical inverse-problem constructions, not new algorithms. They do not estimate real bias, refute all constrained identifiability theorems or reproduce a paper's trained model. Sources include actual DiffusionOT and GRNvelo fulltexts. Identification theorem assumptions must be read before interpreting them.

## Frozen constructions

1. Time-dependent drift with fixed growth: n(x,t)=exp(gamma*t)N(t,1), gamma=.1, d in {.25,2}, v=1-d(x-t). Exact PDE is partial_t n=-partial_x(v*n)+d*partial_xx(n)+gamma*n. Both have identical nonstationary absolute snapshot densities for all t. Known shared extra constant force u=-1 makes delta'= -d*delta+u, delta(0)=0; at T=1 the mean response is u(1-exp(-d))/d. This construction ALLOWS explicit time-dependent drift. It is not inside a strictly autonomous drift class.

2. Autonomous directed drift with fixed diffusion: initial N(0,I_2), d=.1, kappa=.25, omega in {-2,2}, R=[[0,-1],[1,0]], K=-kappa*I+omega*R. Covariance s(t)I where s(t)=d/kappa+(1-d/kappa)*exp(-2*kappa*t) is nonstationary and independent of omega sign; absolute mass exp(gamma*t) also identical. Known constant force actions A=(-1,0), B=(0,-1) both have norm1 and same duration T=1. Gaussian mean m(T)=integral_0^T exp(K*s)u ds. Hypothetical adverse functional burden is exp(gamma*T)*P(X1>0); lower is better. Test whether preferred action reverses. This drift has nonzero curl and is OUTSIDE a gradient-flow-only class.

## Execution / verification

Implement exact analytic snapshot/PDE calculations and independent solve_ivp mean/covariance dynamics. Analytic mean for case2 from complex integral z=(exp((-kappa+i*omega)*T)-1)/(-kappa+i*omega), matrix [[Re(z),-Im(z)],[Im(z),Re(z)]]. Check (i) PDE residual <1e-12 on fixed grid t=linspace(0,1,9), x=linspace(-4,5,31), (ii) IVP/analytic means/covariance <1e-8, (iii) case2 variance changes and both decisions strictly reverse, (iv) equal force norms. Save all formulas/arrays/cost and hashes, no stochastic seeds, fits, GPU or functional biological read. Freeze protocol+code hashes before single run. Fail/stop witness if any check fails; do not alter parameters to obtain reversal.

## Interpretation / decision

If passed, deny ONLY the unsupported claim that snapshot fit plus total abundance and constant diffusion necessarily identifies unrestricted transport dynamics or off-policy function choices. Shared known multi-intervention responses or individual transitions can distinguish the worlds; disclose this explicitly. One exact known-force mean response identifies d in case1 under its stated family; cross-state responses distinguish rotation sign in case2. Neither implies existing pair-function feedback is useless. More snapshots on the same orbit do not resolve these constructions, whereas an appropriate intervention can.

No algorithmic GO follows. A prospective candidate must supply an explicit restriction or real independent identifying feedback, explain what simpler conditional/direct/union estimator cannot match at equal information/cost, and undergo independent cross review before biological values. Full WM/agent/inheritance/joint/RSI obligations remain unchanged. Do not open protected outcomes or revive previous STOPs.
