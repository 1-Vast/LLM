> **File summary**
> - **Path**: `research/astra/feedback_validation_20261003/ADDENDUM_certified_discovery.md`
> - **Purpose**: corrections and boundaries for the claims in
>   `research/certified_discovery/README.md` (2026-10-03). That report, its frozen code and its
>   receipts are left unchanged; this addendum states what the audit found.
> - **Core points**:
>   - The "discovery gain" is a screen-label gain. On an untouched screen with plate-disjoint
>     validation, feedback did not increase validated discoveries (`REPORT.md`).
>   - The FDR guarantee is mostly met through empty lists. The summed yield bound is not a
>     simultaneous certificate.
>   - Costs were partly unrecorded, and elapsed time was not matched.
> - **Evidence**: `workstreams/ws1_*` to `ws4_*`, `results/jaaks_primary`.

# Addendum to the certified-discovery report

Every number below was recomputed from receipts or new runs in this directory. The original
receipts reproduce exactly: WS1 matched all arm totals, and WS3's rerun matched 1,911/1,911
O'Neil and 2,940/2,940 ALMANAC certificate records.

## 1. Discovery claims

| Original claim | Correction | Evidence |
|---|---|---|
| H1: the certified loop "finds more measured synergies than static retrieval" (+2.58 per line) | True for the primary-screen label only. On ALMANAC it decomposes into +2.45 from a better static prior, +2.15 from feedback and −2.02 for the audit. On an untouched screen (Jaaks 2022), with validation on disjoint plates, feedback gave −1.1% [−4.0, +1.4] validated discoveries against the best static arm: NO_MEANINGFUL_GAIN | WS1 step1; `results/jaaks_primary/verdict.json` |
| Feedback is "the active ingredient" | All of the gain comes from drug-in-line effects. Updating only the line offset makes exactly the static purchases (39/39, 60/60, 250/250). On O'Neil, re-scoring with single-agent replicates the model never saw cut wm_full − history from +2.05 to +0.17 [−0.53, 0.85] per line | WS1 step2; WS2 `split_replicate_*.json` |
| Equal wells and days | Experiment counts were matched. Elapsed time was matched only by forcing static arms through 4 rounds; a static policy needs 1 round (3 days on ALMANAC, not 12) | WS1, WS3 |
| S2b: "permuted context hurts" (+3.92) | This measures a wrong drug kernel spreading feedback across unrelated drugs (−0.78 per line from permuting the kernel alone). It is not value from cell state | WS2 shuffle decomposition |

## 2. Certification claims

| Original claim | Correction | Evidence |
|---|---|---|
| H2 FDR 0.043 | Valid as a marginal per-list guarantee under the design. Only 5.6% of lists are non-empty; a non-empty list has FDP 0.77 [0.68, 0.87] and pooled precision 0.27. Nominations are not reliable one at a time | WS3 `receipts_metrics.json` |
| "Certifies 224.5 of the 469 remainder hits" | A sum of per-line 90% bounds is not a simultaneous claim: all 60 lines were covered in 1 of 20 draws, about 0.04 if independent. Valid aggregates on the same receipts are 82.2 (Bonferroni) and 371.5 (pooled Poisson–Chernoff bound for sampling without replacement) | WS3 |
| Certificates valid "under every planner" | The theorem holds (finite-population exchangeability of the random audit inside a fixed shortlist; clipped conformal p-values; BH). In every LLM arm, though, the shortlist and scores were the world model's, so the LLM never set what was certified. llm_named's validity result duplicates wm_full's | WS3 |
| — | The random and menu-random arms reuse the same audit positions in every line, so line-bootstrap intervals for those arms are not over independent audits. Peeking at the bound and stopping early lowers coverage to as little as 0.83 | WS3 `design_checks.json`, `optional_stopping.json` |

## 3. Costs

- The recorded `dose_points` and `wells` belong to the exploit branch; the certify branch's own
  purchases were never recorded. On ALMANAC they differ by −3.4 points per campaign on average
  (range −120 to +69).
- O'Neil "wells" in the receipts are dose points. Under 4 replicate wells per point, the true
  figure is 4× larger.
- Target-line single-agent context was uncharged:
  - ALMANAC: about 12,800–13,200 records per line, 2.6–2.9× a campaign. Most come from plates of
    combinations the campaign never bought, so as built this input is not available before the
    decision.
  - O'Neil: about 0.32–0.48× a campaign.
- Provider spend recorded in the ledgers is USD 1.869 at the provider's peak rates:
  - 1.530 confirmatory;
  - 0.149 dev v2;
  - 0.182 invalid dev v1;
  - 0.008 scratch smoke test.
  - 12 unparseable confirmatory calls were never priced (at most about USD 0.066–0.079 more).
  - The billed amount is unknown.

## 4. Chronology and integrity

- **Invalid dev LLM run.** The "about 18:05" in its `INVALID.md` is a wrong clock estimate made
  when the note was written at 17:50:00. Spend timestamps, the manifest's code digest and the
  freeze contents place the run at 17:47:49–17:48:49, before the 17:58:20 freeze.
- **Freeze integrity.** All 18 frozen digests still match, and the vault was opened once
  (17:58:48).
- **screens.py after dev v2.** The dev v2 manifest records a different `screens.py` digest from
  the frozen one: the ALMANAC builder was added after the development run. The frozen code still
  reproduces the O'Neil receipts exactly.

## 5. LLM planner

The confirmatory failure to return exactly k ids is reproduced by 4-digit candidate ids:
- 4-digit ids: 0 of 21 replies valid on O'Neil;
- 3-digit ids at the same k = 128: 20 of 21 valid;
- chunks of at most 16 ids: 36 of 36 valid.

The model's picks follow the presented order and the displayed scores. Blind mode copies a random
presented order (overlap 0.92). WS4 spent USD 0.2171 over 117 calls on this diagnosis.
