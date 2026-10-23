# Implementation identifiability v1: audit 1 protocol

Status: post hoc, not preregistered, no independent confirmation. Both source papers were already exposed to the v1 package, and the supplementary files were read during this audit, so nothing here is a blind test.

## Question

Do the public AURORA-A (S1, 2020) and CCT400028 (S2, 2026) records contain a condition-matched, quantitatively interpretable, lineage-qualified unit that can support a biological G1 claim? If not, ASSET_BLOCKED is retained and the audit stops. Model predictions, figure interpretation and narrative inference are not used to make up the difference.

## What this audit does not do

- It does not run G2, G3, G4 or G5, and it makes no Agent-gain, Virtual-Cell-gain or autonomous-discovery claim.
- It does not alter any v1 file. Corrections are new versioned records (`records_v2.jsonl`, each pointing at the digest of the record it supersedes).
- It does not define, map or give probabilities to the labels H_E, H_M, H_C or H_O. Explanations keep the v1 study-local ids plus `OPEN_OR_UNMODELED_EXPLANATION`. They are diagnostic fixtures, not an ontology and not a distribution. `NONE_...` means model inadequacy.
- It makes no paid call, buys no data and does no wet-lab work. The only downloads were two open-access full texts and their supplementary bundles (kept outside the repository).

## Evidence grades

`not_read`, `not_reported`, `reported_qualitatively`, `numeric_without_uncertainty`, `numeric_with_uncertainty`. A qualitative "no significant" is not evidence of no effect without an equivalence margin, a detection limit or an interval.

## Rules added (audit1-rules-1)

These can only lower a level. None relaxes a v1 rule.

- Grade-gated updates: only `numeric_with_uncertainty` observations update the compatible set, and a negative reading also needs an equivalence margin, interval or detection limit.
- JB211 is held as separate variables: CRBN recruitment, AURKA occupancy, intracellular exposure, catalytic activity, protein abundance, terminal phenotype. The premise "JB211 inhibits AURKA catalytically" is resolved only by an activity assay. It is never inferred from structure, from a rise in AURKA abundance or from a binary "engaged".
- `OPEN_OR_UNMODELED_EXPLANATION` stays in the compatible set in every state.
- An assay is discriminative only if its predictions differ across surviving explanations, it is legal, it declares an uncertainty model or measurement limit, and it can change a terminal decision. If no action is discriminative the state is `unknown`, `still_indistinguishable` or `NONE_OF_THE_CURRENT_EXPLANATIONS_IS_SUFFICIENT`.
- Requalification adds E1 to E6 on top of v1 L3a to L3f: a terminal endpoint exists; proximal and terminal context is shared by every implementation; exposure or pharmacodynamic evidence backs nominal dose comparisons; negative terminal readings carry an equivalence margin or limit; no unresolved premise sits under a mechanism contrast; an inhibitor or genetic terminal comparator exists when a contrast is claimed. Nominal dose equality is not pharmacological equivalence.

## Candidate units

U1, U2 and U3 from v1, plus C4 (Kelly proteomics for CCT400028, JB170 and compound 50), which has a proximal readout and no terminal endpoint. Each is recorded with target and family, background and genotype, intervention method, compound, modality, dose, exposure, proximal and terminal readouts, controls, replicate structure, lineage, source locator and hash, exposure status, costs and turnaround.

## Mutation checks

Ten, in `mutation.py`: hidden outcomes changed; cell, dose, time or readout changed; JB211 relabelled fully inactive; JB211 catalytic-engagement evidence removed; wells duplicated; proximal evidence removed; all assay predictions made identical; decision consequences removed; source hash or condition identity changed; published-case flag flipped to discovery eligible. Each must be refused, flagged or leave the decision unchanged as stated in the script. They test the software, not biology.

## Stop conditions (all met)

No Level 3 unit; supplementary Table 1 and Data Sets 1 and 4 of S1 not legally reachable in this audit; JB211 catalytic inhibition unresolved; CCT400028 lacks a matched inhibitor or genetic terminal comparison; compound 57 has no terminal result; terminal effect sizes and uncertainty not recoverable; lineage unknown; one target family.

## Reproduction

```
python research/implementation_identifiability_v1_audit1/mutation.py
python research/implementation_identifiability_v1_audit1/build_audit.py
python research/implementation_identifiability_v1_audit1/verify.py
```

`extract_supplements.py` needs the downloaded supplementary files and is not re-run by `verify.py`; its output `supplement_extracts.json` carries the file digests.
