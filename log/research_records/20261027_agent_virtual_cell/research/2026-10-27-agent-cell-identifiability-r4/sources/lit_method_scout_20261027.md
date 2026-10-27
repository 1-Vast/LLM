# Four methodological facts — source check (2026-10-27)

Pages fetched over HTTP and searched locally; PubMed/Europe PMC/arXiv APIs for discovery. Quotes verbatim. Zero-hit searches reported as such, not as proof of absence.

## FACT 1 — "power-aware" acquisition functions

**Claim:** acquisition functions that ignore statistical detectability waste budget, so a power-constrained acquisition is needed.

**No primary source stating this was found**, and no paper framed as "information gain is not enough". Europe PMC title/abstract: `"detectability" AND "Bayesian experimental design"` → 0 hits; `"acquisition function" AND (power OR detectability)` → 5 hits, none on experiment selection. What exists is adjacent:

- **Standard, documented incumbent:** BATCHIE's benchmark baselines are "random sampling (Random), expected information gain (EIG), and variance sampling (Var)" — EIG is the default acquisition, not power (Tosh et al., Nat Commun 2025, DOI 10.1038/s41467-024-55287-7, supplement).
- **Closest published noise-aware acquisition (biology, 2025):** the same paper's probabilistic DBAL criterion carries an entropy factor: "Without this term, a query with a noisy likelihood will be given higher saliency simply because it produces a wide range of possible outcomes. The entropy term balances out this bias by penalizing queries with a low signal-to-noise ratio." This weights likelihood noise inside the utility; it does not constrain whether the effect is resolvable. "Power" appears in the main text only as "computational power".
- **Textbook, not measurement:** low power is wasteful — Button et al., Nat Rev Neurosci 2013 (PMID 23571845): "unreliable research is inefficient and wasteful."
- **Field review:** Rainforth et al., Statistical Science 2024 (arXiv:2302.14545; abstract) frames design as utility optimisation; no power criterion appears.

**What this does and does not settle for us.** Settles that an SNR penalty inside an acquisition is published and operating in a real combination screen, and that EIG is the incumbent. Does not settle that the gap has been framed as detectability/power-constrained design or that wasted budget has been quantified anywhere. The framing looks unpublished, but a zero hit is a search result, not a proof.

## FACT 2 — replicate noise in viability screens

Published numbers are **plate-level correlations and QC cut-offs**, not SD of normalised viability.

- **1536-well, >5,000 combinations across 81 lines** (Nair et al., Nat Commun 2023, DOI 10.1038/s41467-023-39528-9): "Screening was performed in replicate (two separate 1536 well plates)."; replicate agreement "Pearson's R value across DMSO plates … of 0.80 and for technical replicates across combinations plates … of 0.76"; acceptance "CV of less than 25%" in control wells; 4,223 of 5,766 plates passed (~73%).
- **1536-well Z′** (Madoux et al., SLAS Discov 2017, DOI 10.1177/2472555216686308): "an average Z′ factor greater than 0.5" over a ~3,300-drug spheroid pilot — a threshold, not a distribution.
- **PRISM** (Corsello et al., Nat Cancer 2020, DOI 10.1038/s43018-019-0018-6; PMC7328899): 384-well, "1,250 cells/well in triplicate"; 3 replicate plates per screen ("Three replicate plates are combined for visualization"; compounds with "average Pearson correlation below 0.25 across 3 independent plates in one PRISM screen are not shown"). Wells >5 MAD from plate median removed; "cell lines with Strictly Standardized Mean Difference (SSMD) values less than 2 were excluded"; well pass rate "median 99.1%, mean 94.3%"; "5.7% of the pools are filtered out as outliers."
- **DepMap docs** (figshare readmes 20237700, 20238123): MTS010 = "Technical redos for 147 previously screened oncology compounds", "recommended to use MTS010 when available" — yet PR500/PR300 overlap gives duplicate rows, and a maintainer wrote "we don't have public documentation for the differences in the assay conditions" (DepMap forum, 17 Jul 2020).
- **Alamar Blue, 384-well** (BATCHIE): rounds 1–10 single plate; rounds 11–15 duplicate, QC "flagged wells whose duplicates differed by more than 0.5 in viability."

**Silence:** no source gives SD of normalised viability at 1536, or a variance decomposition of duplicate versus plate-replicate noise. Z′ ≥ 0.5 is textbook (Zhang et al. 1999), here only a threshold.

**What this does and does not settle for us.** Settles the operating scale: replicate-plate r ≈ 0.76–0.80, control-well CV < 25%, Z′ > 0.5, and 0.5 viability units of duplicate discrepancy as failure. Does not settle a per-well SD usable in a power calculation.

## FACT 3 — ordinal/rank concordance across contexts

- **Published rank method:** Boumendil et al., Biom J 2024 (DOI 10.1002/bimj.202200332) — hierarchical Bayesian 4-parameter log-logistic model; "posterior distributions of ranks and the surface under the cumulative ranking curve"; built for "limited biological resources"; simulations plus an AML screen.
- **Cross-screen rank agreement, measured:** Nair 2023 ranks combinations by the percentage of cell lines in which they are highly synergistic; two independent screens agree at "Spearman's ρ = 0.61, P = 0.00069." For *which cell lines* respond, agreement is "modest": 12 (Spearman) and 15 (Pearson) of 29 combinations above ρ > 0.25.
- **Cross-dataset:** Corsello 2020 — 84 compounds × median 236 cell lines = 16,650 points; Pearson 0.60 (PRISM–GDSC), 0.61 (PRISM–CTD2), 0.62 (GDSC–CTD2).
- **Cross-site:** Niepel et al., Cell Syst 2019 (DOI 10.1016/j.cels.2019.06.005): "center-to-center variation in GR50 measurements of up to 200-fold" before harmonisation.

**Silence:** no in-vitro dose-response ordinal regression located (PubMed `"ordinal regression" AND dose AND drug` → 7 hits, all clinical); "coefficient of concordance"/Kendall's W with drug data → 1 irrelevant hit. No published test of one shared ordering versus context-specific orderings; practice is descriptive pairwise Spearman/Pearson.

**What this does and does not settle for us.** Settles that posterior-rank models exist for combination prioritisation, and that cross-context agreement is ~0.6 between screens and ~0.6 across databases (Pearson). Does not settle a formal shared-versus-context-specific test — that gap appears real.

## FACT 4 — minimum detectable effect / replication in synergy screens

- **Only formal design/power paper for synergy:** Tan et al., Stat Med 2003 (DOI 10.1002/sim.1467) — sample-size derivation for detecting departures from simple similar action; mouse studies, not plates.
- **Actual cell-screen practice:** Nair 2023 — "four replicates per drug combination in each cell line"; one-sided Wilcoxon rank-sum at FDR < 0.1; selectivity requiring effect in ≥ 80% (n ≥ 12) of cancer lines versus two immortalised lines.
- **Replicate hierarchy:** Niepel 2019 — technical = "triplicate wells per plate" nested in "triplicate plates"; biological = different days; five centres.
- **Multi-laboratory:** *Standardized workflow enables reproducibility of drug synergism detection… ring test*, Biomed Pharmacother 2026 (PMID 42224741) — three labs; unsynchronised protocols first gave inconsistent synergy calls (abstract only; numbers inaccessible).
- **Single versus duplicate plates:** BATCHIE moved from single plates (rounds 1–10) to duplicates (rounds 11–15) after "undetectable random well failures producing corrupted data."

**Silence:** no published minimum-detectable-effect calculation, power curve, or required-n derivation for combination screens. n = 3–4 is convention, not a computed requirement; single-versus-multi-plate reproducibility is quantified only as r = 0.76–0.80.

**What this does and does not settle for us.** Settles that four replicates per combination and two plates are published practice, and that single-plate operation produced corruption. Does not settle any detectable-effect threshold — none is published for this assay class.


