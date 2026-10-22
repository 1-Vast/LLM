# Data and primary-literature qualification, 2026-10-21

Agent: `data_and_literature`. Scope: metadata and primary-source search only; no model run, no dataset payload download, no sealed PRISM24Q2 or ALMANAC outcome access. Only this file was added by this agent.

## Decision

**No newly qualified dataset currently supports the complete world-model + feedback + program inheritance + RSI claim.** Two sources deserve explicit dispositions below. HTTP availability is established for small source metadata / HEAD requests; complete action coverage, biological independence, usable feedback and unexposed evaluation are separate requirements. Do not start a confirmatory experiment merely because a source is downloadable.

Local evidence read: `data/INVENTORY.md`; `log/20261020/SELF_REPAIR_QUALIFICATION.md`; `research/self_repair_qualification_20261020/QUALIFICATION.md`; `research/innovation_validation_20261020/EXTERNAL_SOURCE_QUALIFICATION.json`; the original PTV-1 REPORT and the two current log summaries. These preserve the earlier STOP decisions. The local BATCHIE directory is empty, but its observation design was already rejected on 2026-10-20; emptiness does not make the source new. PTV-1 final outcomes are exposed and its negative result must not be relabelled independent confirmation.

## Candidate 1: 2026 diffuse midline glioma perturbation resource

Primary identity: Calvo Fernández et al., *Nature Genetics*, published **2026-04-22**, DOI [10.1038/s41588-026-02550-w](https://www.nature.com/articles/s41588-026-02550-w). Application: select complementary drugs against coexisting DMG cell states. The study links drug-induced molecular profiles, state occupancy and functional follow-up. It is a useful translational reference but does not establish our RSI mechanism.

- [GSE264130](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE264130): public **2025-12-22**; 372 oncology compounds in **SF8628 and DIPG6**, 24 h PLATE-seq. Dose is constrained by 48 h EC20 or maximum tolerated serum concentration, so dose selection itself uses functional information. GEO supplementary `GSE264130_RAW.tar`: HEAD **200**, **22,056,960 bytes**, Last-Modified **2025-12-23 05:47:24 GMT**. The name RAW refers here to a TAR of processed TSV supplements, not evidence of raw sequencing reads.
- Protocol is experimentally executable: 48 h CellTiter-Glo dose titration, on-plate DMSO controls; then 24 h molecular profiling at a sublethal dose. However, public completeness of the underlying viability dose matrices has **not** been verified. A dose chosen from EC20 is not a freely held-out drug-response label.
- Critically, [GSE264412](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE264412) is described by the paper as drug-screen biopsy RNA, but GEO says **three untreated DIPG tumors**, only three samples. Its count TSV HEAD is **200**, **202,644 bytes** (Last-Modified **2024-04-19 17:14:01 GMT**). Do not count these as three additional drug-intervention backgrounds.
- The paper links [GSE262775](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE262775) treated/vehicle scRNA-seq and separate tumor-volume source workbooks. Their payloads, sizes and full action menus were **not** opened. Published selected-arm follow-up is policy-selected evidence, not a complete alternate-policy replay matrix.
- Independence: only **two** perturbational cell-line backgrounds are established. Technical wells, single cells, drug doses and animals from the same model are not new independent backgrounds. Selected in vivo arms cannot establish broad unseen-drug transfer or meta-improvement across research tasks.
- Exposure: targeted `rg` over local Markdown/qualification/report/protocol records found no GSE264130/GSE264412/DOI string. This is evidence of no matching record, **not proof of non-exposure**. Article aggregate outcomes are now read; future payload release must declare that exposure.
- Licence: article/source material states **CC BY-NC-ND 4.0**, subject to third-party exceptions. The GEO record does not supply a separately verified dataset licence here. Do not substitute a permissive code licence or assume the article licence establishes every dataset's terms.

**Disposition: PROVISIONAL DEVELOPMENT / MECHANISM-AUDIT SOURCE ONLY.** A bounded next action could inspect supplementary schema and an action-coverage census while keeping numerical held-out outcomes behind an independent evaluator. Reject as a full RSI confirmatory asset unless complete comparable functional measurements and substantially more independent backgrounds can actually be established. No such establishment occurred in this search.

## Candidate 2: BATCHIE prospective pediatric-cancer screen

Primary publication: Tosh et al., *Nature Communications* **2025-01-02**, DOI [10.1038/s41467-024-55287-7](https://doi.org/10.1038/s41467-024-55287-7). This is a necessary active-learning comparator: prospective experiment selection with measured combination outcomes, rather than evidence that model-updating or an editable scientific program is RSI.

Source: [Zenodo 13871987](https://zenodo.org/records/13871987), published **2024-10-01**, website version **v1**. The live API record returns `version: null`; pin the record ID, file checksums and date rather than silently converting this to an explicit API version field. API GET **200**. Public metadata states **CC BY 4.0**.

| File | Exact bytes | MD5 |
|---|---:|---|
| PAIR_SCREEN.csv | 24,695,289 | cf960a57c6e90771307d1ca149c8a1d4 |
| TRIPLET_SCREEN.csv | 6,725,455 | fb14309af8371d2c373acb82b0c34894 |

Total payload would be **31,420,744 bytes**; none was downloaded. Functional pair/triplet response is available, but the publication explicitly says PDX-derived-cell-line sequencing is unavailable because patient consent did not permit release. Thus matched molecular state is not established. More decisively, the prior local qualification records roughly **4%** adaptive action-space coverage: a competing policy cannot query the missing 96% without unmeasured imputation. Restricting to the original policy's selected actions changes the estimand and cannot remove selection bias. Exact independent-background counts and complete shared submenus remain unknown until a legitimate census.

**Disposition: RETAIN EXISTING NOT-QUALIFIED DECISION.** It may support an explicitly selected-menu AL benchmark or an external-method reproduction, but it is not new independent evidence for a virtual-cell feedback/RSI claim. No new download or experiment is recommended merely to revisit the same rejected unit.

## Latest primary literature and novelty boundaries

| Primary source, version/date | What is actually supported | Consequence for our proposal |
|---|---|---|
| [State](https://doi.org/10.1016/j.cell.2026.07.052), Cell 2026; predecessor [2025 preprint](https://www.biorxiv.org/content/10.1101/2025.06.26.661135v1.full) | Set-to-set perturbation prediction and cross-context evaluation | Transition modelling is existing work. A model called a world model needs added intervention/decision value over a strong direct predictor on the same information. |
| [MAP](https://www.nature.com/articles/s42256-026-01286-w), Nature Machine Intelligence, 2026 | Knowledge-informed prediction for unprofiled drugs | Knowledge grounding plus unseen-drug prediction is not our novelty; MAP is already locally exposed. |
| [VCWorld](https://proceedings.iclr.cc/paper_files/paper/2026/hash/767ff070c27c8954babe74eccf3fbe91-Abstract-Conference.html), ICLR 2026; [2512.00306](https://arxiv.org/abs/2512.00306) | Biological world-model formulation and perturbation prediction/interpretable pathways | Naming, latent transitions or plausible pathways alone cannot establish a new mechanism or planning gain. |
| [VCLMU](https://arxiv.org/abs/2610.04475), v1, **2026-10-03** | Mechanism-centric latent units and perturbation-disjoint transcriptomic recovery | Explicit mechanism units are already claimed; no experimental planning, functional decision or RSI effect follows from the abstract. |
| [Virtual-cell verification enables self-auditing AI discovery for immune rejuvenation](https://www.biorxiv.org/content/10.64898/2026.08.04.742916v1.full), v1, August 2026, **preprint** | CellQ/PACE with Analyzer–Planner–Auditor; reports 110-compound PBMC screen, revised scoring objective and independent 13-compound assay | Closest biological agent prior. Feedback-driven objective revision with a virtual-cell verifier is already claimed. Search-indexed primary full text/abstract available; direct open returned 403. No independently checked claim of inherited model-update rules or increased future improvement efficiency. |
| [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954), 2025 | Self-modified coding-agent archive, benchmark validation | Editable agents and an archive are established; not proof of biological RSI. |
| [Hyperagents](https://arxiv.org/html/2603.19461v1), submitted **2026-03-19**, preprint | Editable task and meta-agent; improvement@k and cross-domain transfer experiments | The exact requested distinction is prior art: freeze initial vs inherited meta-agent, give the same starting task-agent and k proposals, choose by validation, evaluate on untouched tasks. Compare task improvement and ability-to-improve separately. |
| [AIDE²: Recursive self-improvement of AI research agents](https://arxiv.org/abs/2609.26457), v1 **2026-09-22**, preprint | Reports seven accepted successive rewrites in an eight-day run and transfer to four held-out benchmark families | More efficient research by inherited code is already claimed. Abstract-level verification here; no biological measurements. |
| [MetaShare](https://arxiv.org/abs/2610.21887), v1 **2026-10-15**, workshop preprint | Retains failed/successful edits and signed deltas; cross-lineage retrieval; reports fewer evolution iterations | A failure bank, multi-agent critique or reuse of negative results is insufficient novelty by itself. Need a domain-specific causal/decision mechanism and matched-resource tests. |

These are source-reported results, not replications. The search is bounded, not an exhaustive novelty guarantee. No scientific score was computed by this agent.

## Falsifiable increment worth qualifying

The defensible candidate is **feedback-directed revision of the acquisition/update rule based on which experimentally measured cell-state errors actually cause functional decision errors**, with inheritance of that revised rule to genuinely new drug/context tasks. Distinguish this from an uncertainty heuristic, fixed active learner, ordinary refitting, a linear mixture, or a generic self-editing archive. The proposed contribution is a hypothesis, not established novelty.

Minimum independent test: same starting molecular/functional predictors, same historical evidence and total query/compute/API budget; initial vs inherited meta-agent each gets k edits on new development tasks, with fixed test decision utility and locked test labels. A full factorization needs strong direct predictors, world model without agent edits, agent without world model, joint system, ordinary refitting/continual learning/AL, simple mixture and equal-budget program search. For RSI, freeze the meta-agent during each improvement-efficiency audit to avoid conflating inherited task skill with the ability to generate better successors.

Stop conditions before optimisation: no complete measured action menu, no authenticated molecular-to-functional mapping, no adequate independent units, or unknown exposure => no confirmatory claim. Stop a mechanism after matched-budget development evidence shows no added decision utility or no credible headroom over conventional updating. A new split of an exposed release cannot repair these failures.

## Retrieval and resources

8 batched `web.run` calls; one Zenodo JSON GET; two NCBI HEAD requests. No DeepSeek calls, training, GPU use or experimental queries. Metadata-only network bytes were not metered; no wall-time/currency estimate is asserted. Dataset payload bytes downloaded: **0**. Numeric published aggregate claims were read; no sealed local numerical outcomes were read.

Reproduce the decisive metadata checks without opening response payloads:

```powershell
python -c "import requests,json; j=requests.get('https://zenodo.org/api/records/13871987',timeout=25).json(); print(json.dumps({'license':j['metadata'].get('license'),'version':j['metadata'].get('version'),'files':[{k:f.get(k) for k in ['key','size','checksum']} for f in j['files']]},ensure_ascii=False))"
python -c "import requests; u='https://ftp.ncbi.nlm.nih.gov/geo/series/GSE264nnn/GSE264130/suppl/GSE264130_RAW.tar'; r=requests.head(u,timeout=20); print(r.status_code,r.headers.get('Content-Length'),r.headers.get('Last-Modified'))"
rg --no-ignore --hidden -n -i -g '*QUALIFICATION*' -g 'REPORT.md' -g 'PROTOCOL.md' -g '*.md' 'GSE264130|GSE264412|s41588-026-02550|742916|Hyperagents|MetaShare' log research data/INVENTORY.md
```

The final `rg` now matches this new record; the original search before writing it returned exit 1 and no matches. Random seed: not applicable (metadata qualification only).
