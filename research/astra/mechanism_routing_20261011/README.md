# Block N: where does an LLM add value to a virtual cell?

**Question.** Can the dual core predict *which* cancer lines a compound kills (PRISM Repurposing
19Q4, 578 lines, 2.5 uM)? Does the LLM add anything that the virtual cell (VC) and strong non-LLM
methods do not?

**Answer (confirmatory, 421 sealed drugs, 101 killers):**
* **The VC carries real, irreplaceable information for unseen mechanisms.**
  * It transfers the profiles of screened drugs whose L1000 responses look alike.
  * It beats target and chemical knowledge.
  * It adds to a 160-line partial screen of the compound itself.
  * Its own neighbour similarity says when to trust it.
* **No LLM role added value, and two roles harmed the VC:**
  * forecaster;
  * critic of the VC's evidence;
  * post-screen biomarker explainer;
  * trust judge.

Registered 2026-10-11. Frozen `2026-10-10T18:02:47Z` (755 files, 1,408 development agent
outputs). Run once on the sealed tier, then verified. One frozen check failed on a CSV-precision
artefact with no effect on any verdict (D1 below). Data are local and public:
* GSE92742 L1000 (already extracted by block M);
* PRISM 19Q4 primary and secondary screens;
* CCLE 19Q4 expression and mutations.

## Design

* **Units.**
  * 1,403 drugs with an L1000 profile and a PRISM primary profile, split within mechanism class:
    701 reference, 281 development, 421 confirmation.
  * Confirmation profiles were sealed (`TIERS_RECEIPT.json`) until the freeze.
  * At confirmation the reference pool was the 982 reference + development drugs.
* **Endpoint.** Selective r: Pearson r over lines after removing the generic killing profile G
  from prediction and observation.
* **Population.** *Killers* kill at least 5% of lines (log fold change < -1). The trust contrasts
  use all 421 drugs.
* **Regimes.** In the *unseen class* regime, same-class drugs are removed from every pool and from
  the agent's vocabulary.
* **Virtual cell `L`.** The similarity-weighted mean profile of the 5 reference drugs with the most
  similar GSE92742 responses (mean cosine over shared 9 lines x 6/24 h conditions, 10 uM).
* **Non-LLM comparators:**
  * Hub target kNN `T`;
  * Morgan chemical kNN `C`;
  * their z-mean with L, `E`;
  * the annotated class mean `A`;
  * ridge and top-5 mining on 40 or 160 discovery lines of the compound's own screen, scored on
    281 test lines.
* **Agent: deepseek-flash, thinking off, frozen prompts.** One call per drug and arm:
  * *forecaster*: `route_lit` / `route_nolit` route to screened mechanism classes;
  * *critic*: `adjudicate_lit` keeps or drops the VC's 10 nearest neighbours;
  * *explainer*: `explain_full` sees the top and bottom 20 of 40 discovery lines and names
    genomic features;
  * *trust*: keep count and expected killing, rank-averaged with the VC's similarity.
* **Statistics.** Mechanism-class cluster bootstrap, 4,000 draws. Bonferroni within the 8 VC and
  7 agent contrasts.
  * PASS: the lower bound is > 0.
  * HARM: the upper bound is < 0.
* **Controls.**
  * Zero arm: G scores 0 by construction; random trust scores the mean utility.
  * Outcome poisoning: profiles permuted across lines, on development drugs and again on the
    sealed tier.
  * Literature leak filter, rescanned at verification.
  * Name masking (development).

See `PROBLEM.md`, `PROTOCOL.md` and `PROTOCOL_CONFIG.json`. The development trail is in
`feasibility/README.md`, `development/` and `rehearsal/`.

## Results (`RESULTS.json`)

The family-wise interval decides each verdict.

| id | claim | estimate | family-wise interval | verdict | predicted |
|---|---|---|---|---|---|
| **V1** | VC beats target transfer, unseen class | **+0.116** | [+0.053, +0.181] | **PASS** | PASS |
| V2 | VC beats chemical transfer, unseen class | +0.100 | [+0.030, +0.177] | PASS | PASS |
| V3 | VC alone beats the L+T+C ensemble, unseen class | +0.039 | [+0.002, +0.078] | PASS | PASS |
| V4 | VC adds to the class mean, known class | +0.038 | [+0.007, +0.076] | PASS | NOT_SUPPORTED |
| V5 | unseen-class VC beats ridge on a 40-line partial screen | +0.059 | [−0.023, +0.148] | NOT_SUPPORTED | NOT_SUPPORTED |
| **V6** | unseen-class VC adds to ridge on a 160-line partial screen | **+0.049** | [+0.004, +0.097] | **PASS** | PASS |
| V7 | VC beats targets on the independent secondary screen (n 89) | +0.103 | [+0.049, +0.160] | PASS | PASS |
| V8 | VC's top similarity selects better predictions (top 25% minus mean) | +0.097 | [+0.042, +0.150] | PASS | PASS |
| A1 | forecaster beats target transfer, unseen class | +0.011 | [−0.032, +0.055] | NOT_SUPPORTED | NOT_SUPPORTED |
| A2 | forecaster added to the VC | −0.025 | [−0.051, −0.003] | **HARM** | NOT_SUPPORTED |
| A3 | literature improves the forecaster | −0.009 | [−0.023, +0.006] | NOT_SUPPORTED | NOT_SUPPORTED |
| A4 | critic of the VC's neighbours beats the VC | −0.052 | [−0.091, −0.017] | **HARM** | HARM |
| A5 | explainer beats top-5 mining on the same 40 lines | −0.012 | [−0.044, +0.018] | NOT_SUPPORTED | NOT_SUPPORTED |
| A6 | explainer added to the unseen-class VC | −0.020 | [−0.048, +0.012] | NOT_SUPPORTED | NOT_SUPPORTED |
| A7 | agent judgement improves the VC's trust ranking (AUCC) | +0.007 | [−0.007, +0.027] | NOT_SUPPORTED | NOT_SUPPORTED |

**Headline (rules fixed before the run):**
* VC value **confirmed**: V1 and V6 both pass.
* Agent value **not shown**: no A contrast passes; A2 and A4 are harms.
* 13 of 15 predictions held.

Mean selective r on the 101 killers:

| Predictor | Unseen class | Known class |
|---|---|---|
| VC L | 0.153 | 0.205 |
| target kNN | 0.038 | 0.169 |
| chemistry kNN | 0.053 | 0.150 |
| L+T+C ensemble | 0.115 | 0.221 |
| class mean A | — | 0.186 |
| A + L | — | 0.224 |
| agent forecaster | 0.049 | — |
| agent critic | 0.101 | — |

Own-screen test-line r:
* ridge: 0.084 on 40 lines, 0.145 on 160 lines;
* unseen-class L alone: 0.144;
* L + ridge@160: 0.194;
* explainer@40: 0.034;
* top-5@40: 0.046.

Against the secondary screen:
* L 0.148;
* T 0.045;
* C 0.051;
* the primary screen's own agreement with the secondary (ceiling) 0.320.

**Trust (all 421 drugs).** Mean utility 0.074; oracle top 25% 0.256.

| Trust score | Spearman with utility | top 25% | AUCC |
|---|---|---|---|
| top_sim | 0.273 | 0.172 | 0.125 |
| agent keep count | 0.362 | 0.160 | 0.123 |
| vc+agent | 0.277 | 0.178 | 0.130 |

The agent's keep count again correlates more with VC accuracy than the VC's similarity does, but
does not select better predictions (A7).

## Post hoc (`posthoc/`, not registered)

* **The critic over-rejects** (`agent_failure_modes.json`).
  * It kept 1.1 of 10 transcriptional neighbours on average, and none for 64% of killers.
  * Where it kept none, critic − VC = −0.072. Where it kept 4-10 (n 14), the gap was +0.01 to
    +0.03, but n is too small to read.

  The agent judges neighbours by annotated mechanism. The VC's value lies in cross-mechanism
  phenotypic similarity (V1-V3), which that judgement discards.
* **The forecaster abstains often.**
  * No routable class for 42% of killers.
  * Among the 59 it routed, it beat target kNN by +0.036 [−0.013, +0.085] but trailed the VC by
    −0.130 [−0.185, −0.075].
* **Missing-value rule.** Skipping missing reference values (the promoted rule), instead of the
  frozen nansum over total weight, changes mean selective r by ≤ 0.001
  (`missing_value_rule.json`).

## Verification

`VERIFIED.json`: eight of nine frozen checks pass:
* freeze hashes;
* pre-freeze outputs unchanged;
* tier digests;
* run identity;
* all 1,044 confirmation agent outputs present, created after the freeze, all `ok`;
* literature leak rescan clean;
* ledger within ceiling;
* sealed outcome poisoning: all eight VC contrasts NOT_SUPPORTED, |estimate| ≤ 0.016.

**D1.** `recomputed_contrasts_match` failed. Recomputing from the CSVs moved one tied drug in A3's
descriptive `share_negative`: 16-digit CSV floats turn a last-bit difference between identical
routes into a tie. `VERIFIED_SUPPLEMENT.json` (post freeze) shows:
* every estimate and interval matches within 8.3e-17;
* every verdict and the headline match.

See `DEVIATIONS.json`.

## Interpretation and limits

* **What the VC adds.** Transcriptional similarity carries killing-pattern information that
  curated targets and chemistry do not, for mechanisms with no screened member. It held on an
  independent re-screen, and it complements a partial screen of the compound itself.
  * It does **not** replace a 40-line partial screen at the family level (V5).
  * When the class is known, L alone is comparable to the class mean (0.205 vs 0.186, not
    tested) and adds to it (V4).
* **What the LLM does not add.** In this task the agent's knowledge was confirmed not to help:
  * as a forecaster from literature;
  * as a critic of the VC's evidence;
  * as a post-screen explainer;
  * as a trust judge.

  Literature did not change the forecaster, and name masking did not either (development).
  Development capability ablations do not suggest the null is a model-size artefact:
  * thinking mode and the pro model changed no forecaster or explainer result (69 drugs);
  * pro's critic beat flash's on 14 drugs but did not beat the VC. A pro critic on the
    confirmation tier would have exceeded the budget, so the lead is **unresolved**.
* **Limits:**
  * one assay, one dose (2.5 uM), one L1000 dose (10 uM) and 9 lines;
  * class-level labels define the unseen-class regime;
  * 101 confirmation killers (89 with a secondary profile);
  * the agent's memorised knowledge of PRISM cannot be excluded, but it could only have inflated
    agent scores;
  * L1000 phase 1 was used by earlier blocks for other estimands.

## Promotion

* Promoted: `src/virtual_cell/transcriptional_transfer.py`.
  * `transfer_profile` and `signature_similarity`;
  * the top-similarity trust score;
  * `selective_r`;
  * named refusals: `NO_REFERENCE_DRUGS`, `SIGNATURE_AXIS_MISMATCH`, `NO_QUERY_SIGNATURE`,
    `NO_SHARED_CONDITION`.
* Validated scope is stated in the module.
* Tests:
  * contract tests: `tests/test_transcriptional_transfer.py`, in the core testpaths;
  * parity with the frozen predictors on complete profiles: `test_promotion_parity.py`.
* No agent arm was promoted.

## Costs

* **Lab units.** None purchased. The analogy is one PRISM screen (one compound x ~578 lines)
  against nine L1000 profiles.
* **Provider spend.** $7.46 of the $10 block ceiling (`tmp/mechanism_routing_spend.json`):
  * $6.22 before the freeze: feasibility, development and capability ablations. Pro calls were
    booked at reservation.
  * $1.24 for the 1,044 confirmation calls.

## Reproduction

```
python research/astra/mechanism_routing_20261011/evaluate.py --tier dev --out <dir>    # rehearsal, no sealed value
python -W ignore research/astra/mechanism_routing_20261011/evaluate.py --tier sealed     # reuses cached agent outputs
python -W ignore research/astra/mechanism_routing_20261011/verify.py
python -W ignore research/astra/mechanism_routing_20261011/verify_supplement.py
python -m pytest research/astra/mechanism_routing_20261011 tests/test_transcriptional_transfer.py
```

Repurposing Hub annotations are licensed for non-commercial use.
