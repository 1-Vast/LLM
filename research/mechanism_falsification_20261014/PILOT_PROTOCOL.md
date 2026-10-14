# Pilot protocol (conditional, not executed)

**Status: NOT RUN and NOT FROZEN.** A0 returned INSUFFICIENT_MECHANISM_TRUTH, so the brief's rule is to stop
mechanistic method development. This file records the pilot that *would* be registered if the blockers in
[DATA_FEASIBILITY.md](DATA_FEASIBILITY.md) were removed, so that the gap is concrete and the first step is a data
decision rather than a modelling one. Nothing here may be run on the exposed L1000 or PRISM data as a
confirmation.

## Estimand

For a candidate mechanism "compound C acts through gene T in context X", a falsification rule R either **rejects**
the mechanism or **retains** it using only evidence that is admitted under `strict-review-1`.

* False-rejection rate (FRR): `P(R rejects | mechanism independently supported true)`.
* False-retention rate (FRetR): `P(R retains | mechanism independently excluded)`.
* Report both with exact (Clopper-Pearson) intervals, with the unit of analysis the **mechanism family**, not the
  compound.

## Required truth, all independent of the rule's inputs

| Role | Acceptable evidence | Minimum |
|---|---|---|
| Positive reference | measured engagement in cells or lysate (PISA, TPP, kinobeads, CETSA), or genetic rescue / epistasis tied to the compound | 30 independent families (a zero-failure bound of 10 percent at 95 percent needs 29) |
| Negative reference | measured absence of engagement at relevant concentration with a positive control in the same run, or loss-of-target leaving sensitivity unchanged (Lin et al. 2019 pattern) | 30 independent families |
| Context | same cell line, exposure time within a declared tolerance, same assay | per pair |

Annotation sources (Hub, MAP-KG, ChEMBL) may be *inputs* to R, never truth, never both.

## Arms (all provider-free unless separately authorised)

1. **Zero arm**: retain everything. FRR 0 by construction, FRetR 1. Any rule must beat it on FRetR without paying
   more than a stated FRR.
2. **Annotation-only**: retain if a curated source lists the pair.
3. **Class-membership baseline**: retain if the compound's mechanism class matches (the earlier blocks found this
   explains the knowledge-graph gain).
4. **Signature agreement**: connectivity between compound and genetic signature, with a structure-preserving
   relabelling null (permute gene labels within family sizes).
5. **Candidate rule R**: only after arms 1-4 are fixed, and only a rule whose inputs are admitted evidence.

## Decision rule, fixed before any outcome

R is `METHOD_SUPPORTED` only if, on the registered truth set, (i) FRR upper bound at 95 percent is at most 0.10,
(ii) FRetR is lower than every baseline's by a margin whose interval excludes zero, (iii) the gain over the class
baseline survives the relabelling null, and (iv) it holds in at least two families not used to choose R.
Otherwise the verdict is `INCREMENTAL_SIGNAL_ONLY` or `INSUFFICIENT_EVIDENCE` and is reported as such.

## Refusals that stay in force

No OCEA-style query gating. No NES sensitivity weighting. No on-target / modality / noise decomposition unless it
is identifiable from the registered data and the identification argument is written first. No LLM arm without a
cost ledger and an exact-id schema (the earlier exact-k failure was four-digit ids). No claim of a no-harm
guarantee for any heuristic gate.

## First step that would change the verdict

Obtain authorisation for one measured-engagement or CRISPR-dependency asset covering at least 30 compounds across
families, register it with a source digest, and rerun [census.py](census.py). Only if A0 becomes FEASIBLE_* does
this protocol move to a freeze.
