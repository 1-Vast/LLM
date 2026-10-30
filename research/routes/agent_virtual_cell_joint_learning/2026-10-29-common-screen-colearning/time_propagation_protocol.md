# Frozen source-formula check T001.v1

Frozen before numerical evaluation on 2026-10-29. No biological outcome or fitted parameter is used. This is a constructed mathematical/source implementation check, not a drug-benefit experiment or a proposed co-learning algorithm.

## Claim and source

Wu2025, DOI10.1038/s41540-025-00560-8, formal JATS Sec30 displays the time-inhomogeneous row-state mean as `e_i exp(integral A(t) dt)`. The paper-linked official repository at full commit `19d42e94af20a2be805c78fbb9b104b9a7265d51` (2025-07-18) implements `integral(A_t,0,Time(i))` then `expm(A)` in `main functions/get_Mean_TD.m` and `_h.m`. Static inspection of `Drug_A_T.m` shows separately time-varying death and asymmetric-birth terms; commutation is not enforced. This establishes only what those files compute, not the executed pipeline or the validity of all paper results.

H_T: the displayed plain-exponential propagation equals the row-state ODE solution for the declared source-model family. A single fixed admissible counterexample refutes the unrestricted identity, not the original empirical conclusions. The rival explanation is that a hidden commutation restriction, time-ordering convention, or a different executed implementation makes the paper's intended use valid.

## Fixed cases and formulas

All times are in one declared arbitrary time unit. Initial row population x0=(0.5,0.5), terminal T=24, dose=1. Source-family Hill exponent=1, E_beta=E_nu=(1,1). Baseline alpha=(0.03,0.02), beta=(0.01,0.005), nu12=0.003,nu21=0.001. Logistic rho(t)=1/(1+exp(k(t0-t))), b_eff=1-rho+rho*b. Hill H=(b_eff+1)/2 at the fixed dose/E=1. Diagonal A_ii=alpha_i-beta_i+log(H_beta_i). Off-diagonal A_ij=max(nu_ij+log(H_nu_i),0), matching the inspected source equation (asymmetric birth, no off-diagonal subtraction).

- N1: k=0.3,t0=12,b_beta=(0.95,0.98),b_nu=(1.02,1.0).
- C0 constant control: same as N1 but k=0, so rho=0.5.
- C1 commuting variable control: k=0.3,t0=12,b_beta=(0.95,0.95),b_nu=(1,1). Then A(t)=A0+q(t)I.

Compute M_plain=expm(integral_0^T A(t)dt), and M_ordered from M'=M A(t),M(0)=I. Root implementation uses SciPy quad_vec and DOP853 (rtol1e-11,atol1e-13), with a tighter-tolerance repeat only if numerical agreement is unresolved. Record max entry difference, row-total response x0 M 1, relative total difference and the commutator A(0)A(T)-A(T)A(0). A matrix max entry difference>1e-7 for N1, with both controls<=1e-7 and independent reference agreement<=1e-7, refutes the unrestricted formula. Threshold is numerical resolution, not a biological-effect criterion. No parameter sweep, optimization, response fitting or clinical interpretation.

Independent verification must implement the same fixed matrices separately, using either an ODE in the transposed column convention or a time-ordered midpoint product with convergence checked at 2048/4096 steps. Compare the fixed numerical outputs only after the verifier saves its result. A fresh reviewer first assesses the claim, cases and scope without root numerical outputs. Challenge may stop this check if source conditions invalidate the premise.

## Resources and stop conditions

Research-only Python source, installed `D:\anaconda\envs\maestro\python.exe`; no author code execution, dependency installation, GPU, network, response-table access or core edits. Per implementation wall<=60s, CPU<=60s, expected memory<256MiB; report actual measurements and enforcement limits. One primary computation plus an independent verification count as one scientific mathematical check under the round's two-run ceiling. Abort on nonfinite values, failed integration or violated controls; preserve a failed run and diagnose before any change. Do not infer new algorithm, inferred plasticity, drug ranking, independent function or physical savings from this check.
