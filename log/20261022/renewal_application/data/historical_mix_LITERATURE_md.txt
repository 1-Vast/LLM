# Literature consulted for block K (verified sources; limits noted)

## Sources

| Source | What it establishes | Limit for this block | Use here |
|---|---|---|---|
| McFarland et al. 2020, *Nat Commun* 11:4296, doi:10.1038/s41467-020-17440-w (MIX-Seq) | Pooled multi-line scRNA-seq responses. 24 h (and some 6 h) responses predict PRISM/GDSC viability better than baseline omics in random forests. Cell-cycle shifts track sensitivity for selective drugs. | Baseline features are learned from 24-99 lines. There is no virtual-cell forecast, no measure-or-predict decision, and the time course is not evaluated for decisions. | Data (scPerturb copy). M1 is framed as a replication under a stronger, DepMap-scale prior. |
| Peidli et al. 2024, *Nat Methods* 21:531, doi:10.1038/s41592-023-02144-y (scPerturb) | Harmonised copies of public perturbation datasets, including MIX-Seq. | Experiment identifiers are partly lost; pools are recovered from line composition (`mixseq_index.py`). | Data access. |
| Corsello et al. 2020, *Nat Cancer* 1:235, doi:10.1038/s43018-019-0018-6; PRISM 19Q4 figshare doi:10.6084/m9.figshare.9393293 | Pooled barcoded 5-day viability for 4,518 compounds (primary) and 1,448 compounds over 8 doses (secondary). | Different assay, time and format from Tahoe. Within-line cross-screen agreement is only 0.33 in development lines. | Late endpoint. |
| Ghandi et al. 2019, *Nature* 569:503, doi:10.1038/s41586-019-1186-3; DepMap 19Q4 | CCLE baseline expression across about 1,200 lines. | Bulk RNA from different culture batches. | DepMap-scale cheap prior. |
| Adduri et al. 2025, bioRxiv doi:10.1101/2025.06.26.661135 (State) | A set-based transition model trained on Tahoe-100M and other data. Its authors note that deep models do not consistently beat linear models across contexts. | The checkpoint is a 24 h, Tahoe-platform model. It ships no ordered HVG list (see the axis audit), and cross-platform zero-shot use is untested by its authors. | World model under test. |
| Zhang et al. 2025/2026, Tahoe-100M (bioRxiv doi:10.1101/2025.02.20.639398; *Cell* 2026) | 50-line pooled spheroid perturbation atlas at 24 h. | Single time point. Absolute counts are not identifiable from relative shares. | Early same-spheroid readouts. |
| "Virtual Cells Need Context, Not Just Scale", bioRxiv doi:10.64898/2026.02.04.703804 | Context diversity, not cell count, drives cross-context generalisation. Common metrics reward predicting average responses. | Preprint; read via abstract and search summary. | Motivates separating generic from context-specific transport. |
| Roohani et al. 2025, *Cell* (Virtual Cell Challenge) | Zero-shot generalisation to new contexts is considered premature. | Covers genetic perturbations, not drugs or time. | Context for M2. |
| Hafner et al. 2016, *Nat Methods* 13:521, doi:10.1038/nmeth.3853 (GR metrics); Harris et al. 2016, *Nat Methods* 13:497, doi:10.1038/nmeth.3852 (DIP rate) | Endpoint viability confounds division rate with drug effect. Rate-based metrics separate them. | Both need counts over time. Pooled villages identify only relative shares. | Motivation for a kinetic readout. |
| Kafri et al. 2013, *Nature* 494:480, doi:10.1038/nature11897 (ergodic rate analysis); Kuritz et al. 2017, *J Theor Biol* 414:91, doi:10.1016/j.jtbi.2016.11.024 | Steady-state snapshot densities encode transit rates. Ergodic analysis maps onto age-structured population models. | Assumes a steady-state, asynchronous population. A 24 h drug response is a transient. | Basis of `k24` (phase fractions to duration shares to minimal slowdown). The steady-state assumption is a stated limit. |
| Gross et al. 2023, *Nat Commun* 14:3450, doi:10.1038/s41467-023-39122-z | Phase-specific rate models fitted to live-cell reporter time courses. Drug cell-cycle effects vary over time. | Four breast lines with imaging, no transcriptomics. | Supports reading phase snapshots as rates; motivates T3. |
| Tirosh et al. 2016, *Science* 352:189, doi:10.1126/science.aad0501 | S and G2/M gene lists for scRNA phase scoring. | Relative scoring, sensitive to platform. | MIX-Seq phase calls with a fixed reference. |
| Szalai et al. 2019, *NAR* 47:10010, doi:10.1093/nar/gkz805 | Perturbation transcriptomes are dominated by death and proliferation signatures that predict viability. | Bulk L1000. | Explains why response magnitude carries viability information. |

## Gap this block addresses

No retrieved work evaluates a frozen virtual cell's forecasts as a substitute for an early
measurement in a later-fate decision. None separates the ceiling (value of perfect early knowledge
beyond a strong prior) from forecaster transport across platforms. None evaluates a static
perturbation model against a held-out time course (temporal fingerprint). This absence is a
search result, not a proof.
