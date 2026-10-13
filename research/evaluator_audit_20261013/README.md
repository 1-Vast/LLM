# Evaluator audit: knowledge-reality confirmatory stage

Study folder: `research/evaluator_audit_20261013/`.

* **Status.** Exploratory integrity audit, done on 2026-10-13. The method is in
  [PROTOCOL.md](PROTOCOL.md).
* **What was audited.** The frozen, never-run evaluator in
  `research/knowledge_reality_20261013/confirm.py`, together with `develop.py`, which supplies its
  scoring functions.
* **Cost.** 0 wells, 0 provider calls and 0 downloads. No PRISM 24Q2 response value was read.
* **Effect on past results: none.** The knowledge-reality development gate failed, so
  `confirm.py evaluate` never ran.
* **Why it still matters.** The findings bind any future confirmatory protocol on the sealed 24Q2
  tier. The frozen files are untouched, and `verify.py` checks that their freeze still
  authenticates.

## Findings

Line numbers refer to the frozen `confirm.py`.

| Id | Finding | Severity |
|---|---|---|
| E3 | **Test-batch normaliser** (details below). | major |
| E4 | **Labels depend on the test batch.** Hits and the active set read `S`, which is residualised on the test-batch `G`, so the scored population depends on which other compounds are in the sealed batch. | major |
| E1 | **Eligibility read from outcomes.** `measured = np.isfinite(Y).sum(1) >= MIN_LINES` (L391) defines the scored population from the sealed matrix's missingness. `active` (L392) and the calibration mask (L432) inherit it. | moderate |
| E2 | **A policy reads outcome missingness.** The H2 nomination score is masked by `measured[c][:, None] & np.isfinite(Y[c])` (L451), so every arm skips wells that turned out unmeasured. The mask is the same for every arm. Still, a decision rule sees outcome-derived information, and hit rates are inflated against a real campaign, where a failed well is consumed. | moderate |
| E6 | **Unfrozen inputs.** `read_outcomes` (L308) and `replication_ceiling` read the 24Q2 compound list from `tmp/knowledge_reality_20261013/sealed_metadata/`. That path is not among the FREEZE.json digests, so the ID-to-core map that defines identity is not authenticated. `MIN_ID_MATCH = 0.9` (L58) lets up to 10% of requested compounds drop out of scoring without a recorded deviation. | moderate |
| E5 | **Identity matching** (details below). Currently harmless; latent risk only. | minor |
| E7 | **Secondary readouts repeat E3/E4.** The replication ceiling normalises with `G24` from the sealed compounds (L349). The context-shift readout uses `Gc` and `act_c` from the sealed context lines (L463–L465). | as E3/E4 |

**E3 in detail.** `G = np.nanmedian(Y, axis=0)` (L388) is the median profile of the sealed batch.

* It residualises the truth: `S = M.residualise(Y, G)` (L389).
* It also residualises every prediction inside `drug_r(P, S, G)` (L397, `develop.py` L294–L307).
* Development used the training median: `G = np.nanmedian(Y[train], axis=0)` (`develop.py` L404).
* So the confirmatory estimand differs from the development estimand, and the score uses all
  test outcomes through `G`.
* The training profile `G19` is already locked into the prediction file (L292), but only the H2
  zero arm uses it.

**E5 in detail.** Identity is the 13-character Broad core of REP.1M rows; rows sharing a core are
averaged.

* In the metadata, the 1,278 REP.1M IDs map to 1,278 distinct cores. One ID is also listed under
  REP.300: AZ-628, `BRD-K05804044-001-18-5`. It is not in the 1,229-core sealed set.
* The cell-line metadata spells the screen `REP1M`, while the compound list spells it `REP.1M`.
  The evaluator never joins the two, but any metadata-based eligibility rule must normalise the
  spelling.
* Averaging duplicate rows would silently merge measurements from different screens.

## Proposed corrections, for a new frozen protocol only

1. **C1: eligibility from metadata (fixes E1).**
   * Define the population before unsealing:
     * compounds: the sealed cores that have REP1M `trt_cp` rows in
       `Repurposing_Public_24Q2_Treatment_Meta_Data.csv`;
     * lines: the REP1M lines in `Repurposing_Public_24Q2_Cell_Line_Meta_Data.csv`, intersected
       with the panel.
   * Lock the expected counts with the predictions.
   * Report outcome missingness as QC loss, applied identically to every arm.
   * Refuse with `QC_LOSS_EXCEEDS_DECLARED` if more eligible compounds lose too many lines than the
     protocol declares.
2. **C2: nominations from predictions only (fixes E2).**
   * Policies nominate on predicted scores.
   * A nominated well without a value counts as consumed, with no hit.
   * The masked version is reported only as a sensitivity analysis.
3. **C3: training-side normaliser (fixes E3).**
   * Primary: residualise both truth and predictions with the locked training profile `G19`.
   * Sensitivity 1: a bridge normaliser. Take the median of the 24Q2 compounds also screened in
     19Q4 (`sealed_overlap.csv`), and exclude those compounds from scoring. This removes a
     batch-level shift without using any scored compound's outcome.
   * Sensitivity 2: the current test-batch median.
4. **C4: labels fixed by the primary normaliser (fixes E4).**
   * Hits use `S` residualised with `G19`. The robust z is row-local, so it is unaffected.
   * The active set is fixed the same way.
   * Report the agreement with labels computed on the test-batch `G`.
5. **C5: unambiguous identity (fixes E5).**
   * Refuse when an evaluation core maps to IDs from more than one screen.
   * Refuse duplicate index rows in the outcome matrix instead of averaging them.
   * Normalise `REP.1M` and `REP1M` explicitly.
   * List every requested core that is not found; any loss is a recorded deviation.
6. **C6: pin every evaluator input (fixes E6).**
   * Copy the three metadata files into the study (or a data manifest) and freeze their SHA-256:

   | File | SHA-256 |
   |---|---|
   | `Repurposing_Public_24Q2_Cell_Line_Meta_Data.csv` | `13a85da9e45656c455d3911a4491f3636d7d0975a9d2333dc3d0a3e2cd3b0526` |
   | `Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv` | `7e78f5901c1a97d2baab0789ab89832e716388da4eacaa9f094e7d2f2f5a3463` |
   | `Repurposing_Public_24Q2_Treatment_Meta_Data.csv` | `6be6422ba804ad0775e78b457677bdf088707b9354746a03e110ae63f5eb2061` |
7. **C7: same rules for secondary readouts (fixes E7).** Apply C1–C4 to the replication ceiling and
   the context-shift readout.

These corrections are not applied to `knowledge_reality_20261013`. Its protocol and freeze stay as
frozen, and its NO-GO recommendation stands. The sealed 24Q2 outcomes stay sealed. They should be
unsealed only under a new, independently justified, powered protocol that adopts C1–C7.

## Verification

Run from the repository root:

```bash
python research/evaluator_audit_20261013/verify.py
```

Each check replays one mechanical fact:

* E1–E4, E6 and E7: the cited source lines are present in the frozen files.
* E6: no `tmp/` path is among the freeze digests.
* E5 and C6: if the metadata files are present, the screen counts, the AZ-628 overlap and the three
  digests are re-derived.
* Freeze: the knowledge-reality freeze still authenticates, with CRLF normalised to LF.
