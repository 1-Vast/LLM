# T001.v1 independent comparison

The frozen test refutes the unrestricted ordinary-exponential propagation identity within the inspected source-model family. This is a constructed mathematical/source check. It does not establish biological effects, impact on fitted paper results, or a novel method.

The initial review was saved before calculation. The independent `time_result.json` was saved before viewing `time_primary_result.json`; it is preserved unchanged. Afterwards only a numerical comparison was performed, without rerunning either scientific computation. Both results identify the same protocol SHA256. The independent result SHA256 recorded in `comparison.json` is ea85a5ea27634d15d3e0c0e7ab5c103a6ed8bf85b1a3e94b507bcb9985faf9ec.

| Fixed case | Independent plain/ordered max difference | Primary plain/ordered max difference | Cross-implementation ordered max difference |
|---|---:|---:|---:|
| N1 | 0.006822795435005025 | 0.006822795633203899 | 1.9819876295734673e-10 |
| C0 constant | 5.431211036466266e-13 | 7.827072323607354e-15 | 5.413447468072263e-13 |
| C1 commuting | 8.049561017742235e-12 | 3.4083846855992306e-13 | 8.390621530907083e-12 |

The maximum cross-implementation discrepancy across all plain and ordered matrices is 1.9819876295734673e-10, below the frozen 1e-7 tolerance. Independent midpoint refinement from 2048 to 4096 steps changes N1 by 5.947232151193305e-10. Both controls pass. Thus the N1 difference is separated from the observed numerical disagreement by more than seven orders of magnitude; no further numerical execution is warranted.

For x0=(0.5,0.5), the independent total is 1.3679819724905733 under the plain exponential and 1.3708744968117164 under ordered propagation. The primary ordered total is 1.3708744968915576, a cross-implementation absolute difference of 7.984124472670828e-11. The independent signed relative total discrepancy, (plain-ordered)/ordered, is -0.0021099847782348378 (about -0.211%). This percentage describes only the fixed arbitrary constructed case; it is not a biological effect estimate or a threshold for scientific relevance.

The independent computation used 1.7535 seconds wall, 1.546875 seconds CPU, and peak working set 79,839,232 bytes (about 76.14 MiB), including imports. Wall/CPU checks were cooperative with a caller timeout of 60 seconds; memory was measured, not hard capped. No dependency installation, network, response-data access, author-code execution, parameter tuning, or core/index edit occurred.

The unresolved empirical question is whether any actual fitted/executed source case departs materially from its ordered solution. The present result cannot answer that question. Standard nonautonomous linear ODE theory and established ordered propagation remain the simpler prior; this check alone does not achieve the broader research goal.
