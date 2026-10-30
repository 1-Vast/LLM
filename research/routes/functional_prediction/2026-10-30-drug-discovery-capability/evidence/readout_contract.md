# The economical pooled-response resource and what it identifies

2026-10-30. This source/estimand finding is an analytical stepping stone. It is not a validated biological mechanism, author-error finding, independent drug-discovery benefit or Agent advantage. The original question is frozen in review/question_v1.md; the independent assessment is review/initial_assessment.md. The full goal stays ACTIVE / NOT_ACHIEVED.

## Actual source, units and access

Rhaister, *Back to basics: Observed statistics are sufficient to predict drug responses*, DOI10.64898/2026.06.09.731197, bioRxiv v1,2026-06-12. Official API metadata, original JATS, publisher HTML and equation GIF were acquired. Root inspected selected original model/baseline/EmeraldBay/sensitivity passages and visually read eqn18; this is P-level reading, not the complete paper/code/SI. These are different representations of one article, not independent biological confirmations.

The model uses ridge reconstruction from observed perturbations across reference contexts, additive fallback and optional molecular summary-statistic views. The paper already owns economical functional-probe prediction. A general claim that few functional probes plus a virtual cell predict new-context responses must compare directly with this ordinary model; the present work does not claim to invent it.

The experiment harvests a pooled panel after5days of drug/vehicle. Counts for sensitivity use minimalQC; released transcriptomic profiles use fullQC. Eqn18 defines `P[c,p]=n[c,p]/sum_c n[c,p]` and `S[c,p]=log2(P[c,p]/P[c,vehicle])`. The current public README explicitly describes a cell-count-proportion phenotype. Its label `growth_rate` does not, by itself, establish an absolute growth-rate, death or GR-normalized endpoint.

The public HF API advertises the compact metadata/summary files. The summary was actually downloaded through one explicitly counted302redirect:52,053B,SHA256 `3b4b9e451eab1106b7e47aac1b68d5181f0e684c021c88fc63f0dca01d7cc5c9`, equal to the advertised LFSoid. The physical file contains responses, but only the `cell_line` and `condition` columns were semantically read. No `growth_rate` values, column statistics, predictions or effect comparison were accessed. No expression shards or model weights were downloaded. Physical acquisition and numerical outcome exposure are different facts.

## Metadata actually verified

The local script data/inspect_summary_metadata.py reads only two identity/design columns; its result is data/summary_metadata.json. It verifies:

| Item | Actual metadata result | Scientific limit |
|---|---|---|
| Table | 4,992rows; columns cell_line,condition,growth_rate | No sample/plate/preparation keys in this summary schema |
| Support | 52lines×93conditions =4,836unique keys | This released summary has complete identity-key support, not certified culture/biological replication |
| Row multiplicity | 4,784keys occur once;52keys occur four times | All fourfold keys are DMSO_TF; repeated vehicle rows do not make every drug condition replicated |
| Controls | DMSO_T0once per line; DMSO_TFfour rows per line | Independent preparation and treatment-control pairing remain unknown |
| Single treatments | 44non-control single-drug conditions,19drug names, literal concentration units uM | Target annotation/MoA/independent chemotypes are not established by names alone |
| Combinations | 47multi-tuple conditions | Neither synergy nor common schedule/causal-rescue coverage follows from combination labels alone |
| Filter explanation | Dropping T0and combinations leaves45conditions, including endpoint vehicle | This may explain the article's45condition count; it does not explain six panel plus fourteen target unique drugs when only19non-control names remain |

The README's27-drug annotation table and the summary's19non-control drug identities may reflect different release/filter scopes. That separate metadata table has not been acquired, so this is not a verified contradiction. The article's literal23dose wording and later2–3doses are not silently rewritten. Frozen source passages and DS038 original output remain unchanged.

## Conditional identification and independently sharpened boundary

Define the matched endpoint vehicle fold `g[c,p]=N[c,p]/N[c,0]`, where Nmeans viable burden in the same population universe. This is not time-zero net growth, a death probability, reproductive capacity or clinical efficacy.

With common within-sample recovery `n[c,p]=s[p]N[c,p]`, set `R=2^S` and `G[p]=sum_c N[c,p]/sum_c N[c,0]`. Then `R[c,p]=g[c,p]/G[p]`. A matched viable-total fold Gidentifies gunder this observation model. Without a qualified scale, relative data admit multiple absolute responses. Within-drug ratios between lines cancel the scale; fixed-line absolute cross-drug rankings or absolute thresholds need compatible scales or sufficiently informative bounds. These are established compositional identities, not a new algorithm. Uniform suppression can yield zero relative response; this is an analytical example, not an observation about these cultures.

The independent review sharpened the practical boundary. With stable but unknown line-specific recovery `n[c,p]=s[p]a[c]N[c,p]`, the shared denominator is the **recovery-weighted** total fold, not necessarily physical G. Relative ratios of line-specific folds remain valid, but simply multiplying by an unweighted viable total can be wrong. The review's analytic counterexample has controlN=(1,1), recoverya=(1,2), treatedN=(1,0.5), givingR=(1.5,0.75)andG=0.75; GRdoes not recover(1,0.5). No scientific computation or source result is claimed by this construction.

Under stable recovery, calibrated weights can restore the common-factor calculation. Alternatively, independently known true baseline proportions wgive `g[c,p]=G[p]R[c,p]/sum_c w[c]R[c,p]`; a known absolute fold of a valid internal reference line also fixes the common scale. Recovered T0or vehicle proportions are not automatically true proportions, and calling a line insensitive is not an independent calibration. Treatment-dependent differential recovery can invalidate even relative comparisons. Finite counts, zeros, pseudocounts, denominator exclusions and averaging over differently paired replicates require uncertainty and pairing treatment.

## What can change the next decision

The current cheap table is a concrete relative-response resource and a strong ordinary prediction baseline source. It does not yet qualify an absolute-burden reconstruction/advancement experiment: matched absolute functional anchors, recovery validation, preparation pairing and exact loader transformation of the released column remain unverified. This is a lack of the required contract, not a biological falsification or assertion that the authors possess no calibration.

A virtual cell could model both functional burden and its observation mapping. An Agent might acquire a missing anchor, revise an inferred drug response or abstain. Demonstrated benefit would require a useful real decision, shared per-condition measurement costs, feasible assay timing and held-out validation against fixed counting/calibration, ordinary corrected-response models, simple sequential rules and direct functional assays. With no bounds on the missing positive scale, all nonzero absolute-threshold decisions can remain ambiguous; an adaptive label does not create selective savings. Existing public sequencing data are cheap to reuse, while a new sequencing deployment need not beat a direct low-cost screen.

Adopt now: distinguish relative context preference from absolute burden, preserve the observation model in any virtual-cell task, and use the verified19-drug/44single-condition identity support for possible relative-task planning. Do not admit a routine predictor benchmark solely to fill an experiment count. Restart the absolute line only with actual matched functional/recovery/calibration evidence, or select an explicitly relative drug-discovery claim and justify its contribution independently. The resistance-rescue resource branch has its own evidence contract and is not adjudicated by this compositional finding.
