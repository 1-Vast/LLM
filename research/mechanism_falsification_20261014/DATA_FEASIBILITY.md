# A0: data feasibility for evidence-qualified mechanism falsification

Decision (`CENSUS.json: a0_decision`): **INSUFFICIENT_MECHANISM_TRUTH.** Secondary blocker:
**INSUFFICIENT_CONTEXT_MATCHING.** Method development (A1, Phase 5) is stopped, as the brief requires.

Metadata only. The census ([census.py](census.py)) opened sample and perturbation annotation tables, never an
expression matrix, never a PRISM 24Q2 response. Zero downloads. Every L1000 signature was exposed to earlier
studies, so anything computed here is exploratory.

## What can be paired

A *pair* is a compound with a Repurposing Hub target T, in a cell line where a genetic signature of T exists.
Counts use the CMap reproducibility rule (`distil_cc_q75 >= 0.2` and `pct_self_rank_q25 <= 5`).

| | Count |
|---|---|
| Compound signatures (GSE92742 trt_cp) | 205,034; 20,413 unique perturbagens |
| Hub target-annotated compounds | 2,215 |
| Annotation-only pairs (compound, gene, line, modality) | 61,413 in 13 lines; 1,548 compounds, 601 genes, 346 mechanism families |
| Of these, with a gold-reproducible genetic signature | 22,948 (1,417 compounds) |
| Phase 2 CRISPR knockout, mapped to the parent line (assumption) | 1,199 triples; 133 compounds, 23 genes |
| Of these with the identical cell id | 0 |

## What blocks the estimand

1. **No independent mechanism truth.** The question needs compounds with an independently supported positive
   mechanism (measured engagement, genetic rescue, epistasis, dependency) and compounds with an independently
   excluded one. Local count: **0 measured positive and 0 measured negative references.** The assets that would hold
   them (PISA, Hill 2017, kinobeads, Nyman 2020 preparation, JUMP-target, the engagement case packages) exist as
   directories but hold no files. Hub target annotations are `annotation_only_candidate` (3,184 compound-gene pairs
   in the local scan). Annotation recovery is not mechanism validation.
2. **Hub and MAP-KG are not independent.** Both draw on overlapping curated databases; of 1,472 qualifying pairs
   present in both, MAP-KG agrees on 1,016. Agreement between two sources with a common ancestor is one source.
3. **Context mismatch.** Compound signatures are 6 or 24 h; shRNA and overexpression signatures are 96 h or
   later (shRNA 96 h: 120,654; overexpression 96 h: 19,235). Exact exposure-time matches: 359 of 61,413 pairs, all
   overexpression, none a designed pair. No consensus knockdown or overexpression signature shares a plate with a
   chemical well; 85 single-hairpin signatures that do are control wells on compound plates. In Phase 2, knockouts are
   96 h in Cas9 sublines (`.311`, `.101`): 0 triples with the identical cell id, 0 with an exactly matching time.
4. **Decoys are not negatives.** A constructed decoy is a gene measured in the same line that the Hub does not list
   for the compound (mean pool 2,538 per line; 22,932 qualifying pairs have a pool of 100 or more). That is a bias
   probe. A target missing from a curated database is not evidence that the compound does not act on it.

## Power, if truth existed

At an observed false-rejection rate of 0.05, a 95 percent interval half-width of 0.07 needs about 37 independent
positive references; proving a rate no higher than 0.10 with zero observed failures needs 29 (`0.9^n <= 0.05`).
Compounds inside one mechanism family count once. Available now: **0**. Annotation-only units, usable for
replication but not validation: 1,417 compounds in 331 families.

## What would change the verdict

Any one of: (a) a measured engagement set (PISA, TPP or kinobeads) for at least 30 compounds spanning families,
read after registration; (b) CRISPR dependency or rescue data tied to the same compounds and lines; (c) designed
chemical-genetic pairs measured on one plate at one time. Authorisation to download is required for each (the
DepMap Achilles file noted in the memory index is 218 MB and still unauthorised). None was fetched.

## Asset authentication

All GEO files used were checked against GEO's own SHA-512 sum files: status `VERIFIED` for the small metadata set
([ASSET_AUTH.json](ASSET_AUTH.json)) and for the 21 GB and 5 GB level-5 archives
([ASSET_AUTH_LARGE.json](ASSET_AUTH_LARGE.json)). The Hub and MAP-KG tables have no upstream digest here and are
recorded `LOCAL_DIGEST_ONLY`: the sha256 pins the bytes used, nothing more. A replay requiring any other status is
`BLOCKED/ASSET_MISSING`.
