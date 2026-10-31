# C1 amendment check

Date: 2026-10-30. Decision: **PASS for the narrowly descriptive C1 execution.**

Reviewed only `protocol_c_census_v1_1.md` and the amended `census_c.py`, against the initial review already saved before rebuttal. No source counts or generated results were read, and no census was executed. No source/core files were edited. This is a static protocol/implementation check, not numerical verification.

## Resolution of initial blockers

1. **Incomplete technical conditions and denominators: resolved.** A condition retaining only one well is recorded and omitted from pair analysis rather than aborting or contributing a one-well mean (`census_c.py:61-67`). Conditions losing both wells remain traceable through well exclusions. Input exact-dose pair counts are derived from the original metadata, and the final background table iterates those original backgrounds (`69-72`, `112-119`), so MGH is retained with zero eligible pairs. The amendment explicitly states its metadata-determined inability to bracket 60 h before 72 h and preserves the endpoint. Input-pair counts here mean exact-dose-eligible pairs before endpoint quality filtering; they do not mean all C(14,2) possible drug pairs.
2. **Cross-background reproduction estimand: resolved.** The protocol freezes one technically concordant source-background/drug-pair unit and chooses its primary witness by the minimum positive and minimum negative numeric dose. The implementation does this at line 89, labels that sole witness, and uses only available primary units for the arithmetic mean of unit-level fractions and the separately pooled fraction (`111`, `129-131`). Sign reproduction strictly excludes zero; margin reproduction is separately counted (`98-107`). This removes the previous ambiguity between witness weighting, pair weighting, and sign versus margin reproduction. The number of technically concordant units with no available comparison can be recovered as `technical_concordant_flips - primary_reproduction_pair_units`; printing that explicitly would improve convenience but is not a blocker.
3. **All mean-flip witnesses: resolved.** The witness loop now uses all mean-positive and mean-negative dose combinations and saves technical-concordance and primary-witness flags (`90-107`), so failed technical concordance no longer hides mean-flip witness identities.

## Remaining limits and execution interpretation

No remaining material scientific or implementation issue blocks this descriptive execution on the frozen source. The endpoint, exact-dose restriction, 0.25 margin, and technical-concordance criteria are unchanged. Existing claims remain limited to within-assay descriptions in previously exposed data.

Two fail-closed implementation cases remain: absence of any valid vehicle endpoint on a plate containing surviving treatment endpoints causes the assertion at line 57; absence of every eligible pair leaves an empty untyped pair table and will fail at later column access. Neither case silently produces a favorable result. If encountered, record the execution failure and make only a documented reporting/exclusion implementation correction under the existing rerun rule; do not reinterpret failure as zero flips or change the endpoint, dose criteria, or margin. These cases do not justify exploratory criterion changes.

The stricter margin-reproduction counts are available at witness level; the two headline reproduction fractions are explicitly sign fractions. Any later report should keep those names and denominators. The pair/background and pooled opportunities remain dependent descriptive units, including reverse reuse of backgrounds as anchors and comparisons.

PASS grants no biological replication, independent preparation, molecular mechanism, novelty, clinical exposure, held-out transfer, predictive-model benefit, Virtual Cell Capability, or Agent claim. The required independent numerical check remains outstanding after execution.
