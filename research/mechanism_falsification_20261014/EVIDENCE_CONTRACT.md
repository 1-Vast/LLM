# Evidence contract (version `strict-review-1`)

Implemented in [evidence_registry.py](../../src/maestro/evidence_registry.py),
[strict_decision_review.py](../../src/maestro/strict_decision_review.py) and
[evaluation_contract.py](../../src/maestro/evaluation_contract.py). Opt-in: the historical
`decision_review` keeps its behaviour because a frozen study hashes it.

## 1. What a receipt is

A `RegisteredSource` binds an identifier to a relative path and a sha256 (raw bytes, or LF-normalised for text
tracked under `eol=lf`). It may name the upstream `experiment_id` and `publication_id`. An `EvidenceReceipt` is a
claim about one source: observable, value, unit, normalisation, context, QC status and QC reference, rule id,
protocol version, kind, and `derived_from` (parent receipt ids).

## 2. What authenticates, what admits, what decides

| Step | Question | Refusal codes |
|---|---|---|
| Authenticate | Do the bytes on disk, re-read now, equal the registered digest and the receipt's digest; is the receipt un-withdrawn; do all parents authenticate; is the chain acyclic? | `SOURCE_UNREGISTERED`, `SOURCE_MISSING`, `SOURCE_DIGEST_MISMATCH`, `RECEIPT_UNKNOWN`, `RECEIPT_WITHDRAWN`, `LINEAGE_CYCLE`, `NO_LINEAGE`, `PARENT_REFUSED:<id>:<why>` |
| Admit | Is it a measured kind, with a measured root and no model prediction anywhere upstream, qualified (or undetected only for a registered no-signal rule), finite, in the asked context and protocol version, in a known unit? | `KIND_NOT_MEASURED`, `PREDICTION_IN_LINEAGE`, `NO_MEASURED_ROOT`, `STATUS_NOT_ADMITTED`, `NON_FINITE_VALUE`, `CONTEXT_MISMATCH`, `PROTOCOL_MISMATCH`, `UNIT_UNKNOWN` |
| Decide | Does the canonical value satisfy the prediction's relation, and is the receipt's `rule_id` the prediction's own key? | outcome `supported`, `contradicted`, `conflicted`, `untested` |

A string digest of the right length authenticates nothing; a file named in a receipt but missing authenticates
nothing; a changed byte invalidates every receipt and every certificate resting on it.

## 3. Independence

Independence is **computed, never declared.** The group of a measured receipt is its source's `experiment_id`, else
`publication_id`, else the single shared group `UNATTRIBUTED`. A derived receipt inherits the groups of its measured
ancestors. Three files copied from one run are one group; two unattributed sources are one group, because unknown
provenance is treated as dependent. The policy sets `min_independent_groups` (default 1) for every required prediction.

## 4. Required and supportive predictions

A prediction is `required` or `supportive`. GO needs every required prediction of at least one progression
explanation supported by an admitted measurement. A supportive prediction may stay untested and is listed as
`supportive_untested:<key>`. A progression explanation with no required prediction is refused by the policy.
A measured contradiction of a required prediction removes the explanation; two independent measurements that
disagree produce `CONFLICTED:<key>`, which is neither GO nor NO_GO.

## 5. Competing explanations

With `exclude_alternatives` on (default), a progression explanation is not enough while a competing explanation
(for example an off-target one) has not been excluded by a qualified measurement. The state is
`ALTERNATIVE_NOT_EXCLUDED:<id>`. `exclude_alternatives=False` waives it explicitly; the policy is part of the basis digest the human approval binds to, so a waiver cannot be introduced after approval.

## 6. NO_GO

NO_GO has two routes, both named. (a) A measured contradiction of a required prediction, with the receipt ids.
(b) A registered `NoSignalRule`: an authenticated receipt, admitted for `UNDETECTED` only under that rule, in the
right context, for the prediction the rule names, whose value actually satisfies the rule. An unknown receipt, an
unregistered rule, wrong context, tampered bytes or a value that shows signal is refused with
`NO_SIGNAL_REFUSED:<reason>` and the review continues. A boolean cannot produce NO_GO.

## 7. GO and approval

GO needs: required predictions supported; independent-group minimum met; alternatives excluded or waived; no
unresolved critical limitation; the experiment funded; and a **human approval** by a named person bound to the
SHA-256 of the basis (candidate, policy, status, reasons, and the receipt-to-digest binding). Approvals naming an
automated actor are refused even if constructed by hand. A changed receipt changes the basis; the approval no
longer applies. `certificate_problems` re-checks a stored GO against the ledger and lists withdrawn, altered or
missing receipts.

## 8. Predictions never certify

A model prediction can rank, propose and choose a discriminating experiment. It cannot be the measured support or
contradiction of a required prediction, cannot supply a missing assay, and cannot be the root of a derived
analysis that decides.

## 9. Units

Declared unit per receipt; conversion by division to one canonical unit per dimension (`percent / 100`, never
`fraction * 100`); a threshold at a boundary (inclusive or exclusive, with 1e-12 tolerance) classifies 50 percent
and 0.5 fraction alike; the wrong dimension is refused `UNIT_DIMENSION_MISMATCH`. A reader that guesses the unit
from the data range, as the frozen CTRP reader did, is the failure this prevents.

## 10. Evaluator contract C1-C7 ([evaluation_contract.py](../../src/maestro/evaluation_contract.py))

| Id | Rule | Function |
|---|---|---|
| C1 | eligibility from metadata only; no outcome argument exists | `eligible_units` |
| C2 | nominations independent of outcomes and missingness; failed wells consumed, never replaced | `nominate_wells`, `settle` |
| C3 | normaliser fitted on authorised training rows; a test row is refused | `TrainNormaliser` |
| C4 | hit labels row-local; they do not depend on other test compounds | `hit_labels` |
| C5 | identity collisions, duplicates and losses refused or listed; no averaging across screens | `resolve_identity` |
| C6 | only pinned, unchanged inputs can be read | `PinnedInputs` |
| C7 | secondary readouts follow the same QC and unit rules | `settle` with `Readout` |

## 11. Limits, stated plainly

The contract proves **which bytes** a claim rests on and **how independent** they are by the registrant's own
attributions. It does not prove the bytes measure what the receipt says, that the QC reference is a real
document, or that two experiments the registrant names as different are not confounded in the lab. It is
therefore a gate on admissible evidence, not a guarantee of correct decisions, and nothing in this repository
calls it a no-harm guarantee.
