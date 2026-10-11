# Block P problem statement (draft, before freeze)

## Diagnosis of MAESTRO before this block

Blocks K, M and N, and the unfinished block O, give five facts that set the problem:

1. **The virtual cell's one confirmed asset is transcriptional transfer** (block N).
   * Compounds with similar L1000 responses have similar PRISM killing profiles.
   * This holds across annotated mechanisms; it beats targets and chemistry for unseen classes
     and replicates on the secondary screen.
   * STATE did not transport across platforms (block K) and lost to basal-similarity transfer
     (phenotype anchor).
2. **Every LLM knowledge role so far was null or harmful** (blocks M, N).
   * Each role was a single-shot judgement on a prediction task.
   * None was part of a closed loop in which the system pays for observations and must act on
     them.
3. **Deterministic planners rarely beat fixed designs** when the task has no headroom: protocol v2,
   block M, and block O's feasibility F1 (adaptive choice of which L1000 or viability measurement to
   buy for one compound; 8-unit smoke run).
4. **What has not been tested** is the scientific loop the virtual cell exists for. That loop is
   choosing which compounds to send to an expensive phenotypic screen, using cheap
   transcriptional profiles, and learning from each screen's outcome.
5. **Data constraint.**
   * GSE70138 (L1000 phase 2) holds 975 PRISM compounds never used by block N, and 542 block-N
     compounds.
   * Its phase-1 to phase-2 bridge is weak. A compound's own GSE92742 signature is the nearest
     reference for its GSE70138 signature only 12% of the time (F1).
   * The virtual cell's same-platform library for new compounds is therefore small (542). Every
     compound a campaign screens enlarges it, which is a concrete mechanism by which the agent's
     choices change what the virtual cell can predict.

## The scientific problem

**Discover compounds that selectively kill a target tumour lineage, from a library profiled only
by L1000, under a screening budget.**

* **Unit:** a campaign = (target lineage, library). It is one of 14 lineages with at least 20 PRISM
  lines.
* **Action:** screen one compound in PRISM. This reveals its 578-line viability profile and costs
  one compound-screen.
* **Hit:** mean log2 fold change in the lineage at least 0.5 below the rest, and at most -0.5 in the
  lineage.
  * In development, such hits replicate on the independent secondary screen 60-100% of the time,
    against 1-26% for non-hits (F0).
* **The discovery that matters is the unexpected hit.** Its annotated mechanism class has no known
  selective member for that lineage in the reference library. Corsello et al. (2020) showed that
  such hits exist (non-oncology drugs that kill selectively), and an annotation lookup cannot find
  them.

## Why both cores are needed (hypotheses to falsify)

* **Virtual cell.** It ranks unscreened compounds by transferring killing profiles from
  transcriptionally similar screened ones. This is the only evidence source that reaches across
  mechanism classes.
* **Agent.** It runs the campaign:
  * a persistent ledger of what was screened;
  * a hit model refit on every outcome (arbitration among the virtual cell, annotation, targets,
    chemistry and a gated LLM prior);
  * acquisition, budget, verification against an independent assay, and stopping.
* **Synergy hypothesis.** A screened compound becomes a same-platform reference for its
  transcriptional neighbours in the library. The agent's choices therefore decide how much the
  virtual cell can transfer, so the gain from feedback should be larger with the virtual cell than
  without it (a factorial interaction).

## Data

* Primary: PRISM 19Q4 primary screen x L1000 GSE70138 (phase 2) and GSE92742 (phase 1); development
  on the 1,403 exposed block-N compounds.
* Independent confirmation: the 975 GSE70138 compounds never used in block N, with PRISM outcomes
  sealed (`extract.py`, `TIER_SEALED`).
* Independent biological validation: the PRISM secondary screen (different plates, a dose-response
  run), available for 397 of the 975.
