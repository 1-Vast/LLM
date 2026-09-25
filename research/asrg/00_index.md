# MAESTRO ASRG research assignment — index

Prepared 2026-09-25 against `1-Vast/LLM` at `b41bab1` (branch `claude/sharp-bardeen-q4yt0t`,
identical to `origin/main`, clean tree). **No repository file was changed.**

## Deliverables in this folder

| File | Assignment section |
|---|---|
| `01_repository_audit.md` | 4 — repository gap audit, evidence-labelled, minimal integration surface |
| `02_data_and_costs.md` | 3 — data and three-cost matrix, primary pilot plus one external branch |
| `03_experiment_protocol.md` | 5 — frozen protocol: splits, arms, budgets, metrics, leakage guards, ablations, rejection criteria |
| `04_decision_memo.md` | 6 — ranking of the three options, go/no-go gates, milestones, unavailable assets, unresolved assumptions |

## Executable specification of the model and its algebra

The formal content of assignment section 2 exists as runnable code rather than prose, in
`../asrg_analysis/`. These scripts are the authoritative statement of the claims and were all
executed on 2026-09-25.

| Script | What it establishes |
|---|---|
| `algebra_checks.py` | (1) The dual residual is not identified: shifting `ideal_hat` by any vector moves mass between `r_goal` and `r_realization` and leaves their sum `g − actual_hat` unchanged; along `ideal_hat = actual_hat + t(g − actual_hat)` a norm-based branch rule flips at `t = 1/2`. (2) With a **predicted** anchor, `argmax` of the analytic gain equals the nearest predicted candidate for any positive-definite `W`; with a **measured** anchor it equals `argmin ‖g − (ŷ(a) + e0)‖_W`, and the two disagreed in 1,483 of 2,000 random instances. (3) The reachability lower bound held in 3,000 random instances. (4) `E[Gain] = Gain_hat − tr(WΣ)`, confirmed by Monte Carlo |
| `synthetic_selection.py` | Synthetic property check of measurement anchoring and shrinkage across shared-error fractions and query budgets. **Synthetic, not biological evidence.** Results in `synthetic_results.json` |
| `worked_example.py` | The illustrative worked example, with invented numbers, including a rank-2 effect span and a non-vacuous reachability bound |

Headline synthetic numbers (mean regret, lower is better): with `σe = 1.0`, applying the anchor
in full was worse than nearest-predicted when errors were candidate-specific (16.79 vs 7.78),
better when they were mostly shared (0.67 vs 7.59), and κ-shrinkage matched or beat both at
every setting (5.48 vs 7.61 and 7.91 at a half-shared error). Under a budget, updating the
shared error from each measurement lowered regret at every K tested.

## Delivered in chat, not as a file

The literature evidence map and the prose model specification were interrupted mid-write by a
safety classifier and were not regenerated. Their substance was summarised in the session
reply: the identity result, the non-identifiability result, the measured-anchor mechanism, the
State backend constraint, the data licences, and the benchmark papers that set the bar. Say the
word and I will produce either of them as its own small file.

## Verified sources

Venue and date were confirmed from proceedings, journal or official repository pages where those
were reachable. Direct fetches of arxiv.org, openreview.net, zenodo.org, the Figshare API,
huggingface.co, NCBI, PMC and ai.meta.com were blocked by this environment's network policy;
items marked *(index)* were confirmed only through a search index.

**World models, latent actions, planning**

- LAPA, *Latent Action Pretraining from Videos* — ICLR 2025, peer-reviewed. https://arxiv.org/abs/2410.11758
- AdaWorld, *Learning Adaptable World Models with Latent Actions* — ICML 2025, PMLR 267:18744–18771. https://proceedings.mlr.press/v267/gao25u.html
- DINO-WM, *World Models on Pre-trained Visual Features enable Zero-shot Planning* — ICML 2025, PMLR 267:79115–79135. https://proceedings.mlr.press/v267/zhou25t.html
- V-JEPA 2 — preprint, June 2025; V-JEPA 2-AC post-trained on under 62 h of Droid video, MPC on distance to a goal embedding *(index)*. https://arxiv.org/abs/2506.09985
- FLAM, *Factored Latent Action World Models* — preprint, Feb 2026. https://arxiv.org/abs/2602.16229
- LAOM, *Latent Action Learning Requires Supervision in the Presence of Distractors* — ICML 2025. https://arxiv.org/abs/2502.00379
- *Learning Latent Action World Models In The Wild* — preprint Jan 2026; ICML 2026 poster listing. https://arxiv.org/abs/2601.05230
- UniVLA, *Learning to Act Anywhere with Task-centric Latent Actions* — RSS 2025 per official repo. https://arxiv.org/abs/2505.06111
- PLDM, *Learning from Reward-Free Offline Data* — preprint Feb 2025; NeurIPS 2025 *(index)*. https://arxiv.org/abs/2502.14819
- *Horizon Generalization in Reinforcement Learning* — ICLR 2025. https://arxiv.org/abs/2501.02709
- SPOT, *Supported Policy Optimization for Offline RL* — NeurIPS 2022. https://arxiv.org/abs/2202.06239
- TuRBO, *Scalable Global Optimization via Local Bayesian Optimization* — NeurIPS 2019. https://arxiv.org/abs/1910.01739

**Perturbation models, inverse design, cell models**

- PDGrapher, *Combinatorial prediction of therapeutic perturbations using causally inspired neural networks* — Nature Biomedical Engineering, 9 Sep 2025. https://doi.org/10.1038/s41551-025-01481-x
- State, *Predicting cellular responses to perturbation across diverse contexts* — Cell, 17 Sep 2026. https://www.cell.com/cell/fulltext/S0092-8674(26)00921-9 · code https://github.com/ArcInstitute/state (code CC BY-NC-SA 4.0; weights under a separate non-commercial licence)
- chemCPA, *Predicting Cellular Responses to Novel Drug Perturbations at a Single-Cell Resolution* — NeurIPS 2022. https://arxiv.org/abs/2204.13545
- SAMS-VAE — NeurIPS 2023. https://arxiv.org/abs/2311.02794
- Cell-JEPA — preprint, Feb 2026; improved absolute-state reconstruction but not effect-size estimation, within K562 only *(index)*. https://arxiv.org/abs/2602.02093
- CellFlow — bioRxiv, Apr 2025. https://www.biorxiv.org/content/10.1101/2025.04.11.648220v1
- CellOS — bioRxiv, June 2026 *(index)*. https://www.biorxiv.org/content/10.64898/2026.06.18.733163v1
- GeneSpeak-FP — preprint, July 2026. https://arxiv.org/abs/2607.17671
- Connectivity Map — Science 2006. https://www.science.org/doi/10.1126/science.1132939
- L1000 CMap — Cell 2017; 978 landmark and ~11,350 inferred genes. https://doi.org/10.1016/j.cell.2017.10.049

**Benchmarks and critiques that set the bar**

- Ahlmann-Eltze, Huber, Anders — Nature Methods 22:1657–1661 (2025): deep models did not outperform simple linear baselines. https://www.nature.com/articles/s41592-025-02772-6
- Systema — Nature Biotechnology, 25 Aug 2025: systematic variation inflates common metrics. https://www.nature.com/articles/s41587-025-02777-8
- *The Metric Picks the Winner* — preprint, June 2026: the metric inverts rankings on unseen chemistry. https://arxiv.org/abs/2606.12639
- *Benchmarking virtual cell models for in-the-wild perturbation response* — preprint, Apr 2026. https://arxiv.org/abs/2604.27646
- Virtual Cell Challenge 2026 — Arc Institute project page. https://arcinstitute.org/news/virtual-cell-challenge-2026
- BioDiscoveryAgent — ICLR 2025. https://arxiv.org/abs/2405.17631
- IterPert — RECOMB 2024. https://www.biorxiv.org/content/10.1101/2023.12.12.571389v1.full

**Data assets**

- sci-Plex, Srivatsan et al. — Science 367(6473):45–51, 2020; 3 lines, 188 compounds, ~650,000 cells. https://doi.org/10.1126/science.aax6234
- scPerturb, Peidli et al. — Nature Methods 21:531–540, 2024; Zenodo record 13350497 v1.4, CC-BY *(index)*. https://doi.org/10.1038/s41592-023-02144-y
- LINCS Cell Painting — A549, 1,571 compounds, six doses 0.04–10 µM, 48 h; code BSD 3-Clause, data CC0 1.0; spherizing fitted across all plates. https://github.com/broadinstitute/lincs-cell-painting
- Way et al. — Cell Systems 2022, paired L1000 and Cell Painting in A549, 1,327 shared compounds. https://www.cell.com/cell-systems/fulltext/S2405-4712(22)00402-1
- Tahoe-100M — bioRxiv Feb 2025; CC0-1.0, 50 lines, 379 agents, 1,135 drug-dose conditions *(index)*. https://www.biorxiv.org/content/10.1101/2025.02.20.639398v1
- JUMP Cell Painting — bioRxiv 2023.03.23.534023, later Nature Methods; >250 TB total *(index)*. https://doi.org/10.1101/2023.03.23.534023
