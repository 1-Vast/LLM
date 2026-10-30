# Independent preimplementation review

Only candidate_q1_v1.md, protocol_q1_v1_1.md, preexecution_q1_freeze.json, and the original HTML source were read. No root implementation, numeric output, record, or other report was accessed. Source equations 12, 13, and 14 agree with the frozen raw MI-LB definition.

For each bin, the chain rule gives the remaining information as b_j times the conditional average KL of the posterior against q_j. It is bounded by H(q_j), since conditional posterior entropy is nonnegative. Separately each posterior coordinate is bounded by r_zj, so pointwise KL <= log(max_z r_zj/q_zj), since posterior weights sum to one. r need not sum to one. Taking the smaller of these two bounds after expectation is valid. This is an exact-arithmetic argument, not a floating-point certificate.

Exact merging makes B and B-prime identical input distributions. A permits an exact identical-model guard, but its four initial leaves will still be computed and checked before that guard is applied. Raw MI-LB remains a separate comparator; merging will never replace it in H. Model-mean disagreement, fixed-threshold BALD, and continuous integration are retained. Each model has zero mean in the frozen examples; no outcome is inferred here for the other scores.

No blocking ambiguity was identified. The input/protocol hashes were saved before implementation; code hashes will additionally be frozen before the sole numerical run. Independent implementation will use log-domain Gaussian masses and density envelopes, a cached left-to-right partition, no clipping, no tolerance changes, and a Windows Job Object plus external monitoring. No retries or result-dependent repairs are authorized.

Any eventual positive result is confined to this synthetic local calculation. It cannot establish novelty, drug discovery value, real experimental savings, or multi-round shared learning.
