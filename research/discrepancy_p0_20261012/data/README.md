# P0a source and repeat-design qualification

This packet audits conditions, identifiers and repeat designs. It fits no model,
scores no response, and makes no LLM call. New downloads are limited to the
officially linked PRISM primary replicate-treatment metadata (5,171,151 bytes)
and pooling metadata (151,201 bytes). The original download receipt is preserved
in `NETWORK_SOURCES.json`; reruns verify and reuse its exact bytes.

From the repository root, reproduce with the existing environment:

```powershell
& D:/anaconda/envs/maestro/python.exe research/discrepancy_p0_20261012/audit_sources.py
```

`SOURCE_AUDIT.json` holds qualifications and limitations. `SOURCES.json` hashes
the local inputs, including original assay descriptions. Group tables retain
recorded treatment/sample identifiers without response values. No old study,
derived response matrix, receipt, or production file is changed.

## PRISM

The original paper supports five-day incubation and up to three independently
treated assay plates per screen, with one to three retained after QC. This is
stronger evidence than plate identifiers alone. Distinct thaw/culture-start
identifiers and a fully reconstructed independent normalization hierarchy are
still unavailable. Their absence limits inference about culture variance and
biological versus technical causes; it does not invalidate assay repeats.

Strict 2.5 uM HTS metadata contain 11,841 experimental replicate records in
3,947 drug-dose-screen-compound-plate groups, each with three detection plates,
and 3,939 distinct full Broad IDs. The primary replicate outcomes and raw MFI
are not local, so primary repeat-response verification is not yet evaluable.

Secondary strict 2.5 uM metadata contain 4,466 experimental replicate records
in 1,489 treatment groups: 1,488 have three detection plates and one has two.
The shared group key excludes `well`: MTS010 technical-redo replicates can have
different well positions. These positions remain in the source metadata and
their multiplicity is recorded. Secondary replicate outcomes are already local
but were not opened by this audit. Existing ComBat processing is not an isolated
raw-assay replay.

The 1,281 full-Broad-ID matches between primary HTS and secondary at 2.5 uM,
and 102 drug-dose groups across multiple secondary screens, are identifier/dose
matches. They are not counts of complete cell-drug observations, independently
started cultures, matched elapsed times, or verified pharmaceutical equivalence.
Function agreement is conditionally testable after admitting a common endpoint,
QC and observation contract. Mechanism-cause attribution remains non-identifiable.

## Small alternative: CXCL9

The original paper measures **secreted CXCL9 in 24-hour culture supernatant**
with a LEGENDplex capture-bead sandwich assay and FACS PE. The old dataset card's
"intracellular" and "single-cell" terms are corrected here; its receipt remains
unchanged. Raw rows are nested bead events, not independent cultured cells.

The cached BxPC3 E3CA/P12 and E3CB/P14 files each contain the full 24-condition
factorial menu in `Condition=Sample1` and `Sample2`. The paper states two
independent biological screenings with technical duplicates. File/passage and
Condition are therefore supported screening/technical-repeat candidates, with
96 condition/sample records and 99,528 bead-event rows. `Sample` encodes the
treatment, not a repeat. Explicit seeding/well/day keys are absent.

This supports a small BxPC3 retrospective secretion replay: release declared
condition-level observations from one screening, preserve technical nesting,
and score frozen commitments on the other. Its two screenings do not establish
broad context generalization. The cytokine concentration in this raw background
is 1 ng/mL; the paper uses 10 ng/mL for AsPC1, so the two backgrounds are not
an automatically matched-dose context comparison.

The paper describes an orthogonal Caspase-3 assay, but these cached raw tables
have no matched Cas3 or viability channel. Distinguishing pathway-specific
secretion regulation from cell loss is `NOT_EVALUABLE` until a paired channel is
qualified. Network edges and inhibitor annotations cannot supply the missing
mechanism truth. Full-condition min-max normalization and constructed MIDAS
time grids are excluded from a legal observation stream.
