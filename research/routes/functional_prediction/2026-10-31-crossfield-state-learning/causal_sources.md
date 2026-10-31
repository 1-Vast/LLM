# Causal and longitudinal transfer source notes

Date: 2026-10-31, Asia/Shanghai. Independent scout; targeted original-method reading, not an exhaustive survey. No outcomes, model fitting, author-code execution, installation, paid API, shared library edits, or biological experiments. Four original papers inspected. Network: two successful HTTP requests, 3,170,255 bytes; no failures. Receipts and derived reading extracts are in `causal/`. The recent arXiv release date was refreshed against the official Atom API. Existing biological and transport originals were reused without new requests.

## Constructive finding

The useful transfer is to design a **small randomized bridge at the next decision**, and ask whether a measured early state preserves the *difference between next actions* across histories. This can need less than reconstructing all future molecular states, but still needs actual, correctly joined next-action outcomes. Statistical transfer cannot manufacture that bridge from unmatched expression and terminal-screen arrays.

Let `H` denote the previous exposure/history; `S` an early measurement available before a next challenge; `A` the next randomized challenge; and `Y` a fixed later endpoint. The candidate restriction is

`E[Y(1)-Y(0) | S=s, H=h] = tau(s)`

on a declared region where histories overlap in measured state. This is weaker than `E[Y(a)|S,H]=m_a(S)`: history may change baseline survival equally under both actions while leaving the next-action contrast stable. Therefore absolute-response prediction can fail while the treatment decision remains transferable. This is an ordinary causal-effect-modifier/surrogate design principle, not a novel architecture or an established biological law.

An early state may be **post-treatment for H and pre-treatment for A**. Conditioning on it generally does not identify the total causal effect of H. Randomizing A after S can nevertheless identify conditional next-action effects among the population actually eligible at that decision. If previous exposure killed or selected cells, the target is that eligible population; it must not silently become the original baseline population. If the state assay is destructive, randomly allocated sibling cultures and authenticated preparation lineage can target preparation-level effects; same-cell trajectories are unnecessary, but arbitrary matching of separate studies is invalid.

## Original sources and exact reading

All reading levels below are **P** (selected primary-method passages). No source is fully audited or reproduced.

### C1. Counterfactual Recurrent Network: longitudinal assignment and representation

Ioana Bica, Ahmed M. Alaa, James Jordon, Mihaela van der Schaar. *Estimating Counterfactual Treatment Outcomes over Time Through Adversarially Balanced Representations*. ICLR 2020. Inspected original arXiv:2002.04083v1, dated 2020-02-10.

- Original: https://arxiv.org/pdf/2002.04083 . Local `causal/sources/crn_2002.04083.pdf`; SHA256 `a4bb711cbc68be6771d74b9cdad218e732475a52e5321f88d97c6be5b6ad677e`.
- Read: PDF pp.1-7, Appendix B p.14, Appendix C p.15 through the displayed weighting definitions, Appendix F p.20. The original title/conference banner/version were checked. Additional appendices, implementation and numerical tables were not audited.
- Section 3, p.4, Eq.1: the estimand is expected future potential outcome under an intended treatment sequence conditional on measured history, not factual forecasting under the historical assignment policy.
- Appendix B, p.14: consistency; positivity at each decision given observed history; sequential strong ignorability/no hidden common causes of assignment and outcome. The source explicitly says the last assumption is not testable from the observational distribution alone.
- Sections 4-5, pp.4-6: encoder maps treatment/covariate history to a representation; treatment classifier is adversarially confused while outcome error is minimized; decoder forecasts under specified future actions. Theorem 1 establishes equality of representation distributions at the global minimax optimum. That mathematical equality is not, by itself, proof that an arbitrary lossy representation preserves all effect modifiers or that an unmeasured confounder has disappeared. A constant representation also balances distributions, which makes retained outcome information essential.
- Section 6, p.7 and Appendix F, p.20: counterfactual validation uses a specified PK-PD simulator, not observed real patient counterfactuals. Tumour growth, drug concentration and radiotherapy have distinct terms; Eq.22 carries drug concentration forward with a one-day half-life. Treatment assignment depends on the previous 15 days of tumour diameter. Hence one current abundance snapshot need not encode exposure memory. A biologically defensible target state may need measured/resolved residual drug exposure and recovery rate, not just transcript abundance.

**Transfer:** retain assignment history and prospective action labels; if an adaptive policy uses early state to select the next drug, ordinary outcome regression need not estimate counterfactual effects. A small randomized next-action bridge is preferable to presuming that representation balancing fixes missing confounders. In a fully randomized fixed protocol there may be no assignment confounding to remove, so adversarial balancing is not automatically useful.

### C2. Transportability foundation: what may be reused across studies

Judea Pearl, Elias Bareinboim. *Transportability across studies: A formal approach*. UCLA technical report R-372, 2011/revised 2018 (identity/version as printed in the existing original; no new formal-publication claim).

- Original: https://ftp.cs.ucla.edu/pub/stat_ser/r372.pdf . Reused `reference/papers/pearl-bareinboim-r372/paper.pdf`; SHA256 `df9508c95e46ee8b1c301ec785f36c5736044a0fd7ec95f013960e75ff846dbb`.
- Read: selected PDF pp.4-5, 8-11. Proofs outside these pages and the complete transport algorithm were not read in this scout.
- Example 2, p.4: a predictive proxy can change its relationship to the real response modifier, so matching on the proxy need not transport effects. Example 3, p.5: a treatment-dependent biomarker generally requires intervention-dependent weighting; the ordinary baseline standardization formula is invalid.
- Section 3.2, p.8: transportability is relative to the available experimental information; source average effects alone can be insufficient even when source stratum-specific effects would suffice.
- Theorem 1 / Definition 4, p.10: an S-admissible covariate set separates target/source selection from outcome in the manipulated graph. Corollary 1, p.11: for observed **pre-treatment** S-admissible covariates, a source conditional causal response can be standardized to the target covariate distribution. Here the source uses `S` for a selection node; this differs from our early-state symbol.

**Transfer:** first distinguish a shifted state distribution from a changed state-to-response mechanism. If only state prevalence shifts and the conditional action effects are invariant, a source contrast law can be integrated over the target state's distribution. If drug exposure, assay denominator, survival selection, or downstream response mechanisms change, reweighting molecular embeddings cannot justify this formula. Whether a state is pre-treatment depends on the specific action being estimated.

### C3. Recent update: common transport across interventions, with explicit shift uncertainty

Yorgos Felekis and colleagues. *Generalised Transportability via Causal Abstractions*. arXiv:2608.15645v1, preprint. Official Atom API independently refreshed in this scout: published/updated 2026-08-16. Peer-review acceptance unverified.

- Original: https://arxiv.org/html/2608.15645v1 . Reused `reference/papers/arxiv-2608.15645/paper.html`; SHA256 `3edea1248fb9597df7383639aa98a89a33441420604b49fb3be3fba80bc4bf6b`.
- Date check: https://export.arxiv.org/api/query?id_list=2608.15645 ; saved `causal/sources/traca_atom.xml`.
- Read: HTML `#S3.SS1` (Section 3.1) in full; `#S3.SS2` through Definition 8 and the start of Definition 9; `#S11` in full. Formal proofs, exact-model existence characterization, certificate derivations and numerical experiments were not audited. Derived extraction `causal/traca_sections.txt` contains the selected sections; retaining text beyond the read boundary is not a claim of reading it.
- Section 3.1: same variables, causal graph and intervention semantics; a specified shifted-node set; source observational/interventional and target observational information. These are substantive assumptions, not consequences of similar embeddings.
- Section 3.2, Lemma 1, Eqs.13-14: independent observational or per-intervention stochastic kernels always exist because a constant kernel can output the required target distribution. Definition 8, Eq.15 instead requires **one common kernel across interventions**. Therefore separate per-drug alignment fits are not evidence for a shared biological transfer rule.
- Section 11: uncertainty geometry and directional shifts are declared domain assumptions; observational matching can select the wrong radius and fail to provide desired interventional coverage. Source-reported performance claims were not independently verified and are not imported here.

**Decision-changing transfer:** require one frozen relation to predict held-out action/history combinations; do not recalibrate each action on its held-out target outcomes and call the result transport. Source uncertainty certificates cannot be imported without the specified graph, shift class and coverage conditions. This changes the test object, not the target's evidence level.

### C4. Biological overlap: early functional state and sequential intervention already exist

*Novel selective strategies targeting the BCL-2 family to enhance clinical efficacy in ALK-rearranged non-small cell lung cancer*. Cell Death & Disease, published 2025-03-20. DOI:10.1038/s41419-025-07513-3; PMC11926089. Publication date and identity checked in original JATS.

- Original: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11926089/fullTextXML ; landing https://doi.org/10.1038/s41419-025-07513-3 . Reused `research/routes/functional_prediction/2026-10-31-functional-state-drug-response/challenge/sources/alk_dbp_original.xml`; SHA256 `868c87d72625008d547dce134736f04ba6c6a28900e505378a8ef5b7a218815b`.
- Exact XML locators use zero-based `.//body//sec` and direct `./p`: sec2/p0; sec4/p0-p3; sec5/p0-p2; sec7/p1; sec11/p0; sec12/p0; sec18/p0; sec19/p0; Fig3-Fig5 captions. Read these selected results/methods. Full supplementary experiments, public processed replicate joins and source data were not inspected. The previous challenge synthesis was used to locate originals, but original methods were re-read here.
- Sec2/p0/Fig1: 16-hour ALK-inhibitor-induced dynamic BH3 priming precedes 96-hour death under the same therapies/concentrations. It is not inherently a prediction of a new deferred challenge.
- Sec11/p0: DBP is a functional challenge: drug exposure, collection, viability staining, permeabilization, BH3 peptides for one hour, fixation and cytochrome-c flow readout. Delta priming is treated minus untreated release. At least three independent experiments. The assay is destructive; collection at 16 hours does not imply a usable result at 16 hours.
- Sec12/p0: 96-hour Annexin V/DAPI endpoint with a separately specified cell input. Shared preparation/replicate linkage is not established by these two assay descriptions alone.
- Sec4/sec5: induced anti-apoptotic dependencies motivate combinations described as sequential; distinct cell backgrounds show different dependencies and incomplete rescue. Crucial timing qualification: the Fig3F/Fig4D captions specify 96-hour death and drug concentrations, but do not give the in-vitro ALK-TKI-to-BH3-mimetic delay, washout or continued first-drug exposure. Do not fill in a 16-hour treatment switch from the DBP calendar, or silently relabel these arms as concurrent.
- Sec7/p1/Fig5D is an actually timed next action: inhibit PI3K/AKT or MAPK **after 24 hours of lorlatinib**, with the figure caption describing 96-hour death. Whether lorlatinib was washed out is not resolved by these passages. This is direct prior art for using early adaptation to motivate a subsequent drug challenge, but not an authenticated per-preparation state/next-action/outcome table.
- Sec18/p0/Fig4F has a different in-vivo schedule: S63845 first, brigatinib **one hour later**, with distinct weekly schedules over three weeks. It cannot be treated as the same ALK-first in-vitro sequence or a concurrent regimen. This is a close prior to early functional-state-guided therapy and a reason to compare with a direct mechanism-oriented functional probe. It does not establish our proposed cross-history contrast invariance.

## Smallest discriminating design, without running it

1. Fix one meaningful decision time and two feasible next actions, a later endpoint/denominator, and the population eligible at that decision. Record observation availability, washout/continued exposure, reseeding, counts, batch and preparation lineage. Choose histories that can produce overlapping measured states; histories with disjoint state support cannot test history removal.
2. Across independent preparations, measure the early state before action assignment and randomize the next action within each history/preparation block. A minimally informative factorial skeleton is two prior histories × two next actions, repeated over independent preparations; this is a design skeleton, not a sufficient sample-size claim. Destructive state assays require randomized/exchangeable siblings. Avoid assigning one action only in one history.
3. Compare an ordinary count/recovery/exposure/history model with the state-only contrast model, then with the state-plus-history contrast model. Freeze any source-to-target relation before target test outcomes are accessed. Separate within-overlap residual-history tests from held-history prediction; unseen categorical history intercepts are not meaningful extrapolation baselines.
4. **Minimum falsifier:** at overlapping measured states, the randomized difference between next actions differs across histories by more than a prospectively justified consequential-error tolerance, reproducibly across independent preparations. This challenges *the measured-state contrast restriction*. First rule out state noise, misjoined siblings, exposure differences and endpoint drift; it does not refute every possible richer state or a general cellular mechanism.
5. **Positive result needed:** equivalence of action contrasts within the declared tolerance with adequate precision, then a held-history/preparation prediction or action choice that improves on equally available simple kinetic/count and functional-probe alternatives. A nonsignificant interaction is not equivalence. Absolute-response calibration is a separate claim.

If assignment is observational rather than randomized, consistency, sequential exchangeability and history-specific positivity must hold at every decision; censoring/eligibility also needs a declared selection model or an explicitly restricted estimand. Tiny action probabilities imply effective-information collapse even if nominal positivity is nonzero. Hidden drug exposure or unmeasured adaptation that drives both policy and outcome defeats a purely observed-data causal interpretation. Balancing, g-computation, reweighting and transport cannot repair absent action support, absent future endpoints, missing preparation identities, or changed measurement semantics.

## Scope and stop

This pass delivers a conditional design principle and four traceable original sources. It supplies no new biological validation, novelty certificate, sample-size calculation, numerical admission, causal identification of exposed MAESTRO screens, or demonstrated assay saving. No native web search tool was exposed; discovery was a local index/source pass plus one known original acquisition and one official recent-release check. Prior local full-text provenance is recorded in `causal/local_receipts.json`; no claim of exhaustive 2025-2026 literature coverage is made. Budget stopped at two of eight permitted requests because the selected originals already resolve the transfer question.
