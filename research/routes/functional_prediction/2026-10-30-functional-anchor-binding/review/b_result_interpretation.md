# Independent B result interpretation

2026-10-30. Author: independent B aggregate/prediction arithmetic checker,
previously exposed to the separate A result. This interpretation was formed
after authorized access to B saved artifacts and before the coordinator read
the B outcome summary. No desired B result was supplied. Overall objective
remains ACTIVE / NOT_ACHIEVED.

## Conclusion

The fixed conditional Ridge100 candidate has a small positive point estimate
against its strongest ordinary rival, but fails the frozen exploratory
continuation gate. Mean action utility is 0.07968587 versus 0.07886773 for
pooled target-gene shrinkage, a paired gain of only 0.0008181332. The
2,000-draw identity-group bootstrap interval is
[-0.0241938787, 0.0249875827], crossing zero by a wide margin relative to the
point estimate. This is an inconclusive small gain, not established predictive
or biological benefit.

Both chemical-plate repeat gains against that same selected comparator are
positive (0.0009694645 and 0.0006668018). The interval-lower-bound condition
still fails, so `information_gate_pass=false` is correct. Status remains
`EXPLORATORY_ONLY`, with robust benefit, core promotion and Agent gates false.
No randomization p-value is used or implied.

## Simple rivals, context and nuisance

All 260 source compound IDs and both known cell contexts contribute equally:
520 ID/cell queries in 255 uncertainty groups. These are grouped whole-compound
out-of-fold predictions, not unseen-target, unseen-cell, scaffold-disjoint or
external validation. There are 198 source-target-supported IDs and 62 without
another source-fold compound for their nominal target.

| Method | Mean action utility |
|---|---:|
| Fixed same | 0.07227142 |
| Fixed opposite | -0.07227142 |
| Global mean | 0.07227142 |
| Gene shrink10 | 0.07886773 |
| Pooled Ridge100 | 0.06853219 |
| Pooled RBF1 | 0.07227142 |
| Conditional Ridge100 (fixed candidate) | 0.07968587 |
| Conditional RBF1 | 0.07641498 |
| Cell mean | 0.07227142 |
| Gene-cell shrink10 | 0.07677685 |
| Spatial Ridge100 | 0.06906647 |
| Conditional spatial Ridge100 | 0.07400074 |

The strongest of the eleven noncandidate methods is the simple pooled
target-gene mean shrunk toward the global mean. The conditional candidate
exceeds its pooled Ridge counterpart by 0.01115368, but comparison with the
strongest ordinary rival reduces the apparent gain to 0.00081813. A comparison
only against pooled Ridge would overstate the evidence for this design.
Global mean, cell mean and pooled RBF all choose the same orientation on every
query and have exactly the fixed-same utility. Gene shrink10 chooses opposite
on only 4/520 queries; the candidate does so on 147/520. Substantially more
conditional opposite choices produce very little net gain over that simple
target-based policy.

The candidate-versus-selected-comparator contrast differs sharply by known
cell: +0.03676524 in A549 and -0.03512897 in U2OS. Candidate utilities are
0.08061909 and 0.07875264, while gene-shrink utilities are 0.04385385 and
0.11388162. These descriptive contrasts nearly cancel in the primary average;
they do not support a general benefit across the two contexts.

Spatial-only and combined conditional/spatial rivals are both below the
candidate in this frozen panel. That result does not remove position/target
confounding or establish a biological conditional mechanism: layouts are
fixed, references/controls are shared, and regularization can alter the effect
of adding position columns. Neither the candidate nor its rivals establish
the outcome of independently randomized layouts or assays.

The primary task concerns orientation utility. As a separate regression
description, candidate MSE is 0.06025282 versus 0.05342996 for gene shrink10
and 0.05298969 for gene-cell shrinkage. There is no uniform improvement across
action utility and prediction error.

## Same/opposite and repeat usefulness

Measured mean relations have 317 positive and 203 negative values, with no
exact zeros across the 520 queries. Always choosing same has positive utility
0.07227142; always choosing opposite has its negative. This supports a useful
geometric direction bias in this assay summary, not a rule that drugs
biologically mimic nominal-target ORF overexpression.

Oracle utility, equal to mean absolute measured relation, is 0.19259924;
candidate regret is 0.11291338. There is substantial oracle headroom under
this particular geometry metric, but no physical-effect, dose-response,
target-engagement or practical-cost calibration.

The two chemical-plate summaries agree in sign on 417/520 queries (80.1923%).
This is descriptive consistency of assay geometry; the remaining 103 disagree.
The two summaries share measured ORF references and arise from fixed layouts,
with independent culture/batch identities unverified. They are not independent
biological replications or additional query samples.

Diagonal pairing sensitivity gives candidate-minus-gene-shrink gain
-0.0000454389, while off-diagonal sensitivity gives +0.0016817052. Neither
pairing is experimentally privileged. The primary four-pair mean and the
prespecified chemical-repeat gate remain controlling; these sensitivities show
how small the net contrast is and do not establish robust orientation benefit.

## Arithmetic status and two preserved exceptions

The unchanged preaccess verifier SHA-256 is
`82fd45c61ceae21162c3f65227dd1a4b3e8f1e490198eeb5159a18cea0aceec1`.
Its synthetic and metadata-only checks preceded all B numerical access.
**The unchanged frozen verifier did not PASS, and the original full freeze
integrity did not PASS.** Those facts are retained alongside the numerical
findings rather than replaced by a success claim.

1. The first original-artifact run stopped before arithmetic because
   `review/b_code_access_review.md` differed from its preexecution pin:
   expected `5f77f46e570fac1b28d6a5dfee747cea37107c01b4e49b717630ef43ce06ef7b`,
   current `57bb5aa6f8f5b919855210f1fd9b876bf4079ba5e2781209dc7bbf60460ec976`.
   All other nonraw scientific-input, code, protocol, split and checker pins
   match. The eight raw SHA declarations match the unchanged source manifest;
   the loader declares all original hashes checked. This verifier did not open
   raw files to recertify their bytes. The coordinator authorized an isolated
   administrative-review snapshot view, with the original run/pins and first
   FAIL preserved. This does not retrospectively repair the original freeze.
2. The frozen verifier then stopped on an exact bit-identity check for pooled
   predictions across cells. Ridge differs at 4/260 IDs by at most
   4.4408920985e-16; RBF differs at 3/260 IDs by at most 1.3877787808e-17.
   All pooled action signs are exactly identical across cells. The coordinator
   authorized a separate postaccess supplement replacing only this assertion
   with absolute difference<=1e-12 AND exact identical action signs.

The supplement executes every other frozen check without alteration in a
separate namespace. It does not modify the frozen source, original numerical
arrays, winner/tie selection, sign actions, utility comparisons, bootstrap,
or gate conditions. It returned `SUPPLEMENTAL_ARITHMETIC_PASS`, recorded in
`b_arithmetic_verification_supplemental.json`. The two FAIL reports remain
`b_arithmetic_verification.json` and
`b_arithmetic_verification_review_adapter.json`.

The completed numerical checks independently reconstruct all four cosines
from normalized chemical/ORF aggregates, verify the 5,673 retained features
and recorded scale/center/count constraints, match output IDs/folds/groups to
the pinned metadata, reproduce all six simple fixed/mean/shrinkage profiles,
and check saved utility/regret/MSE, the exact floating comparator, paired
gain, fixed identity bootstrap, repeat/pair sensitivities and decisions.
The 2,576 decoded rows and 14,920,192 numeric cells, 496 skipped rows, allowed
well identities and protected-CGI-false receipt all match the metadata contract.

The child reports approximately 15.667 seconds wall, 15.109 seconds CPU,
four threads and five complete folds, with bounded-launch exit0. No fit,
real-data replay, array repair, reserve-matrix use, raw profile read, HTTP
request or protected-outcome access occurred in this audit. The supplement
was written after access and is explicitly not a second preaccess frozen
verifier. All original outputs are retained byte-for-byte, with hashes in the
reports/adapter receipt.

## Interpretation boundary and disposition

Cosines from normalized Cell Painting features measure feature-dependent
assay geometry. They do not establish drug efficacy, sensitization, target
engagement, chemical/ORF mechanistic equivalence or knockout response. The
nominal target is supplied as an input hypothesis, not discovered. Measured
ORF catalogs in both cells and negative controls are additional assay-assisted
information with measurement costs, not free transfer.

The arithmetic audit starts from saved normalized aggregates. It does not
independently certify raw control normalization, treatment aggregation,
unretained-column raw finiteness, source-fold operator fitting or nuisance
removal. Source/code admission and loader receipts are separate evidence.
The bootstrap is conditional on fixed predictions, this dataset and the
selected comparator, excluding refitting, selection and shared-reference/
control uncertainty. The administrative review drift and postaccess numerical
check change remain material provenance limits.

Retain the small positive point estimate and failed continuation gate. Park
this fixed conditional Ridge design for purposes of escalating complexity;
do not tune another model or select a favorable cell/pairing after this result.
The result does not show conditional biology is impossible, and it does not
establish enough gain to justify a larger architecture on this evidence.
Ordinary target-based shrinkage attains nearly the same primary utility.
No novelty, independent external validation, secure holdout, Agent/core or
robust practical benefit claim follows.
