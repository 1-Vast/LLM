# Real predecision-state audit

The [October 1 evidence addendum](../../log/20261001/README.md#16-independent-review-of-the-supplied-state-evidence-report)
restores Cycloop original controller-log replay and corrects the Gross control
wells. The older `two_measured_actions_per_question` contract applies to a
matched sister-sample panel only. Randomized policy arms and randomized action
logs have separate identification contracts in `state_evidence_followup.assess`.
They require authenticated assignment/support, real endpoints and complete
attempt denominators; an alternative action need not be observed on the same
physical cell. This correction qualifies no current task for STATE efficacy.

The 2026-10-01 audit stops at stage 1: **zero qualified state-gain tasks**.
Twelve local task families and three new public candidates fail temporal
availability and/or state-to-response matching. Reconstructed historical
metadata joins cover 4,926 episodes and 44,520 episode/action records; these
remain replay evidence. No new model, planner, threshold or synthetic-card
experiment is run.

The full dated report is [log/20261001/README.md](../../log/20261001/README.md).
The [data acquisition and collection plan](STATE_DATA_PLAN.md) names the missing
fields and the steps required before an efficacy preregistration.
The [published receipts](audit_results/20261001_state/manifest.json) preserve
raw source metadata, public response bytes, action joins, failures, versions,
hashes, environments and reproduction commands. Large uncompressed metadata
copies are published as reversible gzip; the manifest distinguishes raw source
hashes from derived join hashes.

## Reproduce into fresh output directories

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -m tools.datasets.state_raw_review --review-notes outputs/state_identifiability_20261001/raw_review/raw_source_review.json --out outputs/state_identifiability_20261001/raw_review_new
& 'D:\anaconda\envs\maestro\python.exe' -m tools.datasets.state_public_review --out outputs/state_identifiability_20261001/public_review_new --fixtures outputs/state_identifiability_20261001/public_review
& 'D:\anaconda\envs\maestro\python.exe' -m tools.datasets.state_identifiability --out outputs/state_identifiability_20261001/stage1_audit_new --review outputs/state_identifiability_20261001
```

The first command freshly hashes local assets by default. Its explicit
`--reuse-recorded-hashes` option records reuse rather than a fresh verification.
The public command above parses frozen local bytes and makes no network calls;
omit `--fixtures` to collect the 13 pinned metadata sources from HTTPS. Changed
bytes, invalid registry identities, challenge pages, malformed metadata and
request failures remain negative receipts. Successful download never qualifies
a causal comparison. The original public inspection also includes contextual
sources and failures beyond the 13 minimal reproducible pins.

The stage-1 entry point consumes completed independent review notes. Its
classification is a source-backed scientific review plus strict software
contracts, not automated certification of a dataset. It does not silently
execute stage 2 or stage 3 when a future candidate passes. Raw `time=0`, a DMSO
label, cell-line identity, a design menu and a deposited result do not by
themselves certify decision-time availability, legal pairing or all attempts.

Current STATE remains the registered Tahoe c39/NCI-H596 backend; its exact
weights are audited separately from the data. WorldV2 has historical fitted
results but no verified restorable transition artifact for this comparison.
ReferenceWorld is not a substitute for either backend.
