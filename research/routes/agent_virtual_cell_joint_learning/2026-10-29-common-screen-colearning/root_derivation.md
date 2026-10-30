# Root reasoning before outcome access

2026-10-29. These are conditional mathematical deductions, not a new algorithm, a result on HTS001, or a claim that ordinary images identify molecular killing.

Consider a homogeneous linear birth–death process X with rates b,d and r=b-d. For gap h, a=exp(rh), E[X_next|X]=aX and Var(X_next|X)=X(b+d)a(a-1)/r, with continuous limit X(b+d)h at r=0. Its centered transition innovations eta_i=X_(i+1)-a_i X_i are pairwise uncorrelated. Suppose Y_i=X_i+epsilon_i with zero-mean observation errors independent of the entire latent process and each other, Var(epsilon_i)=v_i. Then the observed transition residual R_i=Y_(i+1)-a_iY_i satisfies:

- Cov(R_i,R_(i+1))=-a_(i+1)v_(i+1), including unequal time gaps.
- Cov(R_i,R_j)=0 for |i-j|>=2.
- Var(R_i)=E[X_i](b+d)a_i(a_i-1)/r+v_(i+1)+a_i^2 v_i.

With population moments, known a_i and enough genuinely repeated trajectories, adjacent residual covariance therefore separates internal-frame observation variance from latent transition variance. The inference is conditional on the process/measurement structure. Heterogeneous evolving populations, serial segmentation error, random effects or time-varying growth can violate it. Two technical wells per drug condition are not a precise covariance estimate; pooling creates additional assumptions. Estimated a_i must be learned from separate wells or its fitting uncertainty must be propagated. A negative adjacent covariance alone is not proof of measurement noise, nor is zero nonadjacent covariance proof of a birth–death mechanism.

This is a state-space/localization-error principle already covered by ordinary joint trajectory inference; Wu2025 Sec27–29 is a direct biological baseline. An agent choosing time gaps by the resulting model is ordinary experimental design unless a concrete scientific object or resource theorem changes. Do not freeze it as a novel co-learning algorithm just because BESTDR's inspected transition implementation differs.

One potential useful empirical action is a preregistered necessary-assumption diagnostic on the 28 vehicle trajectories per cell, with an untouched set of wells and propagated nuisance estimation. It could falsify a narrow white-error/Markov-transition model; it cannot validate birth/death labels, independent cultures, drug benefit or actual measurement savings. Do not access counts until the final diagnostic, primary statistic and independent review are frozen.
