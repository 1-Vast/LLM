# Deviations and post-freeze disclosures

The frozen protocol stays authoritative for the verdict. No frozen file changed after the freeze: the
independent verifier re-hashed all 6 study files, 13 built inputs and 22 sources at the end of its run.
Times are UTC on 2026-10-31.

## 1. Undescribed de-duplication of 24Q2 queries (pre-freeze; found at verification)

`keys_24q2.tsv` and `l1000_24q2.npz` (built 04:20Z, hashed in `FREEZE.json`) keep one Broad ID per InChIKey
connectivity block. Section 4 of the protocol does not describe this, although its census count of 101 queries
reflects it. One eligible compound was therefore left out: BRD-K57796080 (3,5-DHPG-(S)), whose block and
L1000 signatures it shares with the query BRD-A20589515.

At 05:51Z, after the verdict, the principal read that compound's single REP.1M row
(`POSTHOC/dhpg_sensitivity.py`, `POSTHOC/dhpg_sensitivity.json`). It is inactive: 13 of 568 lines killed, where
29 are needed. The primary population (32 actives) and every verdict are unchanged. Across all 102 compounds
(reported, not tested): C1 − B0 +0.0097 (one-sided p 0.068), C1 − B1 +0.0123 (p 0.022).

## 2. Contrasts listed by the protocol but missing from `RUN/RESULTS.json`

The run did not write the context contrasts "every arm vs Z", nor the secondary-endpoint versions of C1 − B2
and B1 − B0. The verifier computed them (`VERIFY/check1_stats.json`, `unreported_contrasts`). Every arm except
L is above Z on both sets. On PRISM 24Q2, C1 vs Z is +0.113 [+0.075, +0.154] (p 2.6e-6), and B0 vs Z is +0.099
[+0.058, +0.143]. No decision depends on these.

## 3. Details the protocol leaves unstated

The verifier resolved each from the data and reported what each alternative would change (`VERIFY/REPORT.md`,
"Ambiguities"):
- hit count: nearest integer to 10%, ties to even;
- activity denominator: missing values count as not killed;
- line matching: exact DepMap IDs;
- dose: the nominal LINCS 10 µM label;
- 24Q2 L1000 identity: the connectivity block, as for NCI-60;
- B2 fingerprints for keys with several NSC numbers: the first NSC's SMILES;
- the leakage-arm permutation sequence.

None changes a verdict. The verifier disclosed that it chose the hit-count reading after a floor reading failed
16 checks.

## 4. Chance level of the secondary endpoint

The protocol gives the zero arm a hit precision of 0.10. The permuted-reference arm L reaches 0.121 on NCI-60
and 0.120 on 24Q2 (one-sided p 0.003 and 0.004 against 0.10), so 0.10 understates chance. The report reads hit
precision against L.

## 5. Analyses added after the run

All are exploratory and outside the verdict:
- sensitivity to the number of removed directions;
- the neighbour-mechanism analysis and the tertile analysis (`POSTHOC/posthoc.py`, finished 05:39Z);
- the check that the promoted module reproduces the confirmed predictions (`POSTHOC/promotion_check.py`);
- a literature link to Systema (Nature Biotechnology 2025), cited in the report but not in the frozen
  protocol.
