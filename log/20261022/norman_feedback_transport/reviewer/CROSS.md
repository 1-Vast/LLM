# Actual reciprocal cross-review

2026-10-22. Written after independently sealed INDEPENDENT.md and INDEPENDENT_PROPOSAL_RESPONSE.md. Read peer skeptic/INDEPENDENT.md and skeptic/CROSS.md, root PROTOCOL.md, experiment.py and test_kernel.py. Peer's prior CROSS was root-proposal review, not reciprocal exchange; this document records the subsequent actual exchange. No numerical dataset, protected values, HTTP or fit/run accessed.

## Independent source-code assessment

No fold leakage found: select(train,validation) calls baseline(train), candidate residuals train only on train, and validation y is used only for candidate scoring. Nuclear inner selection similarly fits its own baseline on union training rows. q_E is fitted once on all E and copied into both later-only estimators. Union baseline is refitted on union, as required. The normalized symmetric tensor kernel is PSD mathematically; implementation matches its equation and pair orientation invariance. The supplied synthetic test checks PSD, unit diagonal and orientation, but was inspected rather than run by this reviewer.

The strongest interpretive limitation remains later-only residual updates discarding E residuals. This intentionally tests a restricted operator from a common quadratic predictor. Ordinary union controls fairly recover E information. No full-learning-superiority claim follows from a fixed-geometry win. Nine mixture candidates versus three fixed candidates bundles geometry and selection opportunity; identical penalty support and the paired grid expose the narrower fixed-penalty comparison, not equal search or compute. Root explicitly discloses both limitations.

## Actual exchange

Reviewer sent skeptic: common-start restriction is coherent; union controls address forgotten E residual evidence; no fold-baseline leakage found; main 9-versus-3 bundles geometry/search; requested peer's strongest actual blocker. Reviewer proposed finite, duplicate, diagonal and overlap assertions as minimal boundary enforcement.

Skeptic replied: 'Agree narrow qE operator valid, baseline fold separation correct, union controls adequate finite GO.' Peer identified the same concrete correction: canonical unordered pair uniqueness, a!=b, source/development disjointness, finite outcomes/priors/features/correlation, sufficient source and later sizes, and unique/nonmissing source_order. Peer noted duplicate selected/grid fits inflate reported runtime honestly and do not create equal-compute evidence.

Reviewer replied: agrees these checks are the sole concrete implementation blocker found, with no evidence that existing qualified inputs violate them. Also agrees with peer's earlier mathematical distinction: forming the pair kernel from mixed gene L_w includes cross terms and is not a convex mixture of the RNA and identity pair kernels. Root's actual equation/code preserve the correct version.

## Final bounded verdict

GO for the finite ordinary exploratory run after minimal prefit boundary assertions are installed. Assertions should reject nonfinite arrays and priors, unmapped genes, duplicate canonical unordered pairs (including across splits), diagonals, ambiguous source ordering and undersized batches. They should not inspect protected inputs. No new algorithm GO; no independent-task, inherited updater, RSI or confirmatory protected-performance claim. Stop this instantiated advantage if primary later512 calibrated U fails against fixed RNA. If union refit matches/beats it, stop distinct updater-superiority claims. Preserve all costs and selection records. No further search or split change is requested.
