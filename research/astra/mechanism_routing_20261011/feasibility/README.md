# Block N feasibility record (2026-10-11, exploratory)

These probes chose the block N question under the 2026-10-11 requirements:
* the LLM must do work that simple algorithms cannot;
* data must be few, cheap and local;
* every LLM contribution needs an ablation against strong non-LLM methods.

None of them is confirmatory:
* F and P use GSE92742 values opened by block M.
* P2-P3 read PRISM aggregates over all drugs before the block N split.
* V and B use development drugs only, after the split; confirmation PRISM values are sealed in
  `../TIERS_RECEIPT.json`.

Numbers come from the JSON files named in each section.

## F: the agent's prior claims about where, when and which genes (`probe_emh_claims.json`)

Block M's agent wrote line, time and gene claims for every mechanism class before any value was
read. Scored directly on 874 active drugs:

| Claim | Agent | Control | Data reference |
|---|---|---|---|
| Line selectivity (Spearman per drug) | 0.014-0.021 | shuffled claims -0.004; DepMap genotype rule 0.029 | same drug 6 h vs 24 h 0.158; class-mates 0.056 |
| Time profile (24 h minus 6 h) | 0.04-0.08 | | class-mates 0.20 |
| Gene direction (signed mean z) | 0.77-0.80 | shuffled 0.56-0.59 | gene-frequency baseline 1.73 |

**Verdict:** text-only prediction of where, when and which genes is weak. A frequency baseline
doubles the agent on gene direction, as Yuan et al. 2026 report. Line selectivity has little
reproducible headroom in nine L1000 lines. The direction is dropped.

## P: transcriptional anomalies adjudicated by PRISM (`probe_anomalies.json`)

* 178 active drugs respond more like another class than their own. Many alternatives are CNS
  receptor classes, consistent with shared cationic-amphiphilic responses.
* 158 have PRISM data; 56 involve one of the 32 classes whose members' PRISM profiles agree.
* Of those 56, PRISM sides with the L1000 alternative in 55% of drugs.
* Non-LLM signals already rank the cases:
  * L1000 margin, Spearman 0.41;
  * Hub target overlap, 0.32;
  * Morgan similarity, 0.30.

**Verdict:** too few adjudicable cases for a powered test. Not pursued.

## V: predicting which lines a drug kills, without an LLM (`probe_viability.json`)

Endpoint: selective r, the Pearson r over 578 PRISM lines after removing the generic killing
profile. Population: development drugs, 69 of which kill at least 5% of lines.

* **Ceiling.** The secondary screen against the primary for the same drug gives 0.18 overall and
  0.27 for killers.
* **Known-class killers.**
  * class mean 0.18;
  * L1000 transfer (virtual cell) 0.18;
  * target kNN 0.16;
  * chemical kNN 0.10.
* **Novel-class killers** (own class hidden):
  * L1000 transfer 0.14 [0.09, 0.20];
  * target kNN 0.03;
  * chemical kNN 0.02.

**Verdict:** the virtual cell carries cross-mechanism information that targets and chemistry do
not.

## Agent routing pilot (`../development/pilot_novel_class.json`; $0.25)

Setup: 69 development killers, novel-class regime, four agent arms.

| Predictor | Selective r | Difference |
|---|---|---|
| Virtual cell, L1000 transfer | 0.142 | |
| Agent routes to mechanism classes | 0.039 | vs target kNN +0.016 [-0.036, +0.060] |
| Agent adjudicates the virtual cell's neighbours | 0.082 | vs virtual cell -0.060 [-0.104, -0.020] |
| Agent routes added to the virtual cell | | vs virtual cell -0.014 [-0.030, +0.002] |

The remaining arms showed no effect:
* literature vs none: -0.004;
* name masked vs named: +0.008;
* agent biomarkers vs the target-expression rule: -0.000.

**Verdict:** as a forecaster, or as a critic of the virtual cell's evidence, the agent subtracts
value.

## B: biomarker discovery from part of the lines, without an LLM (`probe_biomarker_mining.json`)

Lines with complete CCLE features are split in half (seed 20261011): 281 test lines, and
discovery subsets of 40, 80, 160 and 280 lines. Values are test-line r for the 69 development
killers:

| Discovery lines | top-1 | top-5 | ridge | Hub-target top-1 | random-20 top-1 | Virtual cell L (no discovery data) |
|---|---|---|---|---|---|---|
| 40 | 0.039 | 0.053 | 0.079 | 0.032 | 0.021 | 0.171 |
| 80 | 0.044 | 0.051 | 0.105 | 0.039 | 0.031 | 0.171 |
| 160 | 0.058 | 0.081 | 0.124 | 0.032 | 0.039 | 0.171 |
| 280 | 0.078 | 0.103 | 0.139 | 0.034 | 0.045 | 0.171 |

**Verdict:**
* The virtual cell's transfer prior, built from other drugs, is worth more than 280 lines of the
  drug's own data.
* Restricting mining to Hub targets does not help.
* The agent's chance is a feature set that beats unrestricted mining at 40-80 lines, or one that
  adds to the virtual cell.
