# Qualification: is there a measured self-repair research unit for drug-discovery functional decisions?

Status: QUALIFICATION, 2026-10-20. No experiment is proposed. No API, purchase, author contact or wet work. Nothing committed or pushed.
Closed studies (`functional_rule_revision`, `self_improving_virtual_cell`, `innovation_validation[_repair1]`, `procedure_inheritance[_audit1]`) and their
negative decisions are untouched (digests in `EVIDENCE_MANIFEST.json`).

## Verdict

**`NO_UNIT_QUALIFIES_FOR_SELF_REPAIR_BEYOND_REFITTING`.** The observation unit exists and the failure is real and decision-relevant, but the revision that would
make it *self-repair* rather than ordinary refitting has no supported content: every structured explanation tested for the failure explains none of its
decision-relevant part, and the failure is repaired by a plain per-drug offset estimated from earlier-run later samples. The missing link is a measured
**cause** of the shift (an assay-condition variable such as reagent lot, plate layout or protocol change, or a second hypothesis class with a transferable
prediction). A smaller functional claim remains (drift-aware refitting, below); it is not novel and needs no agent.

## Evidence for the eight items (selected candidate: Beat AML 2.0; others summarised after)

All numbers: **exposed released development data** (Beat AML was used by `context_transfer_20261017` and `feedback_attribution_20261017`), feasibility only, never
confirmation. Scripts: `feasibility.py` (headroom), `feasibility2.py` (explanations, chronology), `feasibility3.py` (structure), `feasibility4.py` (continuation).
Outputs: `FEASIBILITY*.json`. Pool, endpoint, models and decision rule were declared in each script header before its first numeric output.

1. **Identities.** Rows: 555,583 raw wells; 63,395 probit fits (subject x rnaseq/dna sample x inhibitor, `auc`, `ic50`, dose range). 166 inhibitors, 569 subjects,
   631 sample ids, 7 concentrations, replicate wells in about 15 percent of (sample, drug, concentration). Action meaning across contexts: 116 drugs have >= 100
   fits in both cohorts and **identical fitted dose ranges** (none dropped), so AUC is comparable across waves; cohorts differ in drug coverage (13 drugs one
   cohort only). Gap: `time_of_read` takes 30+ values per drug, so it is **not an assay duration**; endpoint time is not identified by the release.
2. **Menu / exposure / missingness.** One query = one drug AUC on one sample (about 7 wells; plates carry the cost). Later-cohort missing fraction 19 percent in the
   pool. Releases are fully exposed; no hidden outcome exists. Subjects repeat (569 subjects, 631 sample ids), so every interval clusters by subject.
3. **Existing-model error and headroom.** Waves1+2 (401 samples) model applied to Waves3+4 (210 samples): mean |shift| 0.216 SD, 28 percent of drugs |t| > 3,
   34 percent > 0.25 SD. Decision (nominate top 5 drugs, utility = minus mean true z): stationary covariate model 0.375, chronological online per-drug offset
   0.745; paired difference **+0.370 [0.257, 0.497]** (cluster bootstrap, 154 decisions, 146 subjects); random 0.197, oracle 2.57 (noise-inflated: median technical
   noise 0.34, RMS 0.63 between-sample SD units, so the oracle is not an attainable ceiling). With a fixed 8-drug ridge battery: 0.693 -> 0.803 with offsets
   (+0.109 [0.038, 0.184]); k = 16: +0.064 [0.005, 0.134]. Headroom of repair over the strong fixed predictor: real. Headroom of an agent over the offset: untested
   because no strong comparator is exceeded by anything except the offset.
4. **Two competing explanations, same observation.** Composition shift (covariates) vs assay/step shift vs run-time trend. Composition explains **0.03 percent** of
   the shift (corr -0.001); time slopes learned in Waves1+2 extrapolate with R2 -0.72 (corr 0.34 but over-scaled); the within-Waves1+2 late-minus-early drift is
   not a continuation of the later shift (centred corr 0.04, sign agreement 51 percent); family structure (leave-one-drug-out, centred) -0.13, potency -0.04.
   The shift is **reproducible** (split-half corr of the centred Waves3+4 shift 0.78), so it is not noise. Separability by a single observation: per-drug
   |shift| / residual SD median **0.16** (p90 0.37); about 308 later samples per drug for 80 percent power at alpha 0.05; 12 percent of drugs detectable with
   <= 60 samples; none with one. A global part (-0.18 SD, 38 percent of squared shift) exists but cannot change a ranking. **The two hypotheses are therefore
   not distinguishable by one diagnostic observation, and no structured hypothesis has non-zero decision-relevant explanatory power.** Marked: unestablished.
5. **Downstream target.** Later-wave AUC of the same drug in other subjects is a legal target; pairing is traceable by subject and sample id. Shared reference
   terms (drug standardisation uses Waves1+2 only) and dependence (subject clusters, plate and run) are recorded, but run-block and panel effects were not
   modelled (unestablished whether plate/panel explains the offset; no labelled lot variable exists).
6. **Chronological sequence.** Partly real: later-cohort median run_index 417 vs 188.5, 92 percent of later runs after the Waves1+2 median, but only 34 percent
   after its maximum (run ranges 1-448 vs 17-512, 20 'Both' samples excluded). The prequential check (offset from earlier-run later samples only) respects this order.
   It is a replay of released data, not a prospective sequence; revision-before-evaluation holds inside the replay.
7. **Comparators and mechanism.** Fixed model (0.375), covariate-composition (adds +0.007 [-0.081, 0.093] to the offset), ordinary online per-drug offset
   (0.745), 8/16-drug battery refit (above). Not run: KG/lookahead, caching/distillation, conventional model selection (no second mechanism exists to
   distinguish them from). Released history is a shared prior in every arm. What would distinguish a self-repair mechanism from the offset: a revision that
   predicts an offset for drugs *not* queried later. Tested here and absent (family/potency/time/composition all <= 0 centred).
8. **Claim table.**

| Claim | Status here | What exists |
|---|---|---|
| Software correctness | partial | scripts run; part-1 M3/M4 and its separability block are invalid by construction (documented, unused) |
| Exposed measured development | **yes** | wave shift reproducible; offset refit +0.37 U [0.26, 0.50] over stationary |
| Independent functional validation | no | none; all data exposed; changing the split cannot create it |
| Mechanism evidence | no | composition, time, family, potency all fail to explain the decision-relevant shift |
| Real economic value | no | no cost data; query-count unit only |
| Pharmacological efficacy | no | ex vivo AUC only; no patient benefit |

No sample size is computed: no estimand with a non-zero effect beyond the ordinary comparator exists to power.

## Other candidates (metadata and local records only)

- **Jaaks 2022 combinations** (pair identity: anchor + library, concentrations, COSMIC line, plate barcode; fitted schema read). Strong unit, but opened and
  closed repeatedly by the Jaaks studies (action substitution NARROW/STOP, biological residual gate UNDERPOWERED/STOP, feedback propagation STOP); failure not
  separable from noise; no new unit.
- **O'Neil, PRISM 19Q4/24Q2, GCP2020, Tahoe, ALMANAC:** consumed, no chronology, no pair identity or too few backgrounds, or access-restricted; none opened.

## Smaller functional claim that remains (not proposed as an experiment)

"Per-drug offsets estimated chronologically from the first n later samples improve top-5 nomination over a frozen earlier-cohort model, and covariate composition
adds nothing" is supported on exposed data only, is ordinary drift repair, and would need a new unexposed cohort with a recorded assay-condition variable to become
independent. A query-budget version (how many per-drug queries find the offsets) is the relevant efficiency question; its effect size is unknown here and no N is committed.

## Literature (verified, not used for any novelty claim)

Bottomly et al., Cancer Cell 40(8):850-864 (2022), doi 10.1016/j.ccell.2022.07.002 (Beat AML 2.0; 805 patients, 942 specimens). Tyner et al., Nature 562:526-531
(2018), doi 10.1038/s41586-018-0623-z. No novelty claim is made; related ideas were not searched beyond these two data sources.

## Reproduction

`python feasibility.py` -> `feasibility2.py` -> `feasibility3.py` -> `feasibility4.py` -> `manifest.py` (each about one minute; clock resolution not a factor: no CPU timing is claimed).
