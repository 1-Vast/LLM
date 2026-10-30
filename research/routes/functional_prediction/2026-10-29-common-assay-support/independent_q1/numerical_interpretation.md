# Independent one-shot Q1 numerical interpretation

The single independent run supports all three frozen H_Q1 conjuncts for these synthetic densities. This is a local numerical result, not biological validation or a floating-point interval certificate.

| Quantity, natural-log units | A | B | B-prime |
|---|---:|---:|---:|
| Raw source MI-LB | -0.15354981190975092 | -0.4807176680319176 | -0.41531165006134896 |
| Exact-merged MI-LB | -0.15354981190975048 | -0.13414407775194492 | -0.13414407775194492 |
| Model-mean disagreement | 0 | 0 | 0 |
| Fixed tau=0.5 Bernoulli BALD | 0 | 0.0032757894893255986 | 0.0032757894893255847 |
| Continuous-MI reference | 0 | 0.02847468939165506 | 0.02847468939165506 |
| Q1 lower bound | 0 | 0.028457338330361997 | 0.028457338330361997 |
| Q1 upper bound | 0 | 0.04838031056491763 | 0.04838031056491763 |
| Final leaves | 4 | 218 | 218 |
| Splits | 0 | 214 | 214 |
| Computed leaves including cached history | 4 | 432 | 432 |

A's four initial leaves were computed and checked. A then stopped using the exact identical-distribution guard. Its [0,0] is not attributed to adaptive refinement. B and B-prime each stopped at width 0.019922972234555632, below 0.02 and far below the 2048-leaf cap. Their lower bound exceeds A's upper bound plus 1e-8.

The raw source formula ranks A over B while true MI is zero at A and strictly positive at B. A negative MI lower bound is mathematically allowed and does not invalidate the source lower-bound theorem. B-to-B-prime changes neither distribution and changes both Q1 bounds by exactly zero in this implementation. It changes raw MI-LB by 0.06540601797056866. The raw lower-bound representation dependence is therefore observed here.

The exact-merged source comparator is material: it already ranks B above A and is unchanged for B-prime. Fixed-threshold Bernoulli BALD also ranks B above A, although it retains less information than the continuous observation. Neither simple comparator may be hidden to imply Q1 is necessary. These data establish no advantage over those comparators for the decision between A and B.

Each reference was integrated once over [-16,16], epsabs=epsrel=1e-12, limit=300, with no warnings and no retries. For B/B-prime, QUADPACK's estimated error is 8.008931218658502e-13 and the additional tail bound is 4.428347100022751e-58; their sum is below 1e-10. The entire estimated reference ranges lie inside the corresponding Q1 bounds with the frozen 1e-8 allowance. A has zero integrand and estimated quadrature error; its general-purpose tail bound is 4.2400952565695243e-39. B's quadrature includes signed model contributions: 483 negative individual terms were counted. Summation used math.fsum, but the quadrature error remains an estimate and is not a formal certificate. Gaussian CDFs and arithmetic were not outward rounded.

Total counts: 10,836 scalar Gaussian log-density evaluations; 2,620 scalar log-CDF and 2,620 scalar log-SF evaluations; 987 quadrature integrand evaluations; 868 computed leaves; 428 splits. Per-comparator counts and CPU times are in result.json. For B, Q1 took 0.21875 process-CPU seconds and the reference took 0.078125 seconds; for B-prime they took 0.203125 and 0.0625 seconds. Timing is coarse and the workloads differ. No speed advantage is claimed. All candidates retain analytic observation cost 1 and zero wet experiments.

Windows Job Object enforcement was installed before releasing the worker: user CPU limit 120s, private-memory limit 1,073,741,824 bytes, active process cap 1, kill-on-close. An external 10ms monitor additionally counted worker kernel/user CPU plus guardian CPU and checked output size. Output protection also exists in the worker writer. The job exited naturally with code 0. Worker CPU measured externally was 1.453125s; guardian CPU 0.28125s; total 1.734375s. Worker peak working set was 85,430,272 bytes; peak private commit 66,801,664 bytes. The pre-receipt directory contained 2,144,225 bytes. Authoritative limits and measurements are in resource_receipt.json. The internal worker timer starts after gate release and therefore excludes interpreter/gate startup, explaining its smaller 1.265625s reading.

Independence: I read only the three designated frozen documents and the designated original-source HTML before implementing, then my own files. I neither read nor executed the root implementation or its numerical results. Input/protocol/source hashes were saved before implementation, and implementation/input/protocol hashes were saved before this sole numerical execution. An exclusive execution marker prohibits relaunch. No network/API calls, installation, real functional response, protected dataset, GPU, or wet experiment was used. No parameters, tolerances, frozen inputs, or code were changed after the run. No rerun was performed.

This result does not establish novelty, drug-hit benefit, experimental cost savings, real-data utility, or multi-round shared learning. The source framework's fixed P_Z is not evidence that this additional shared-z Bayesian experimental interpretation has been validated. Q1 remains a research-only calculation; no core-code promotion is warranted by this run.
