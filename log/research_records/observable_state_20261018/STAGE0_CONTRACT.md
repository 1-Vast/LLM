# Stage 0 contract (DRAFT, not frozen): per-family typed-edit bets, agent versus matched proposers

Study: `research/observable_state_20261018`. Design source: `ENHANCEMENT_AGENT.md` (subagent output) after the repository cross-check in
`NOVELTY_REVIEW.md`. Development study on exposed PRISM 19Q4; never independent confirmation. **Stage 0 used labels and fingerprints
only** (`stage0_families.py`, `STAGE0.json`): no outcome, activity or missingness was read, no LLM was called, nothing was frozen.
Items marked **[OPEN]** must be settled and hashed before Stage 1; Stage 1 also needs the user's authorisation for the first use of
search-side outcomes and for LLM spend.

## 1. Question and prior

Can a Scientific Agent propose typed response-state edits (one per MoA family) that are confirmed on held-out chemistry **and**
held-out lineages more often than a matched conventional enumerator (A2) and a non-LLM knowledge rule (A2k)? Prior from
`program_revision_20261017` on the same data: LLM vs enumeration +0.004, 20-23% wrong direction, 62-88% insufficient evidence. The
expected result is a null; the contract exists to make that null well powered and attributable, and the thesis survives only if
the agent beats **both** A2 and A2k.

## 2. Units and splits (computed in Stage 0)

* Episode = one MoA family. 1,145 families; none crosses a fold.
* Within-family split by connected components of ECFP4 Tanimoto >= 0.5, whole components assigned by salted hash (`obs-state-stage0`)
  until ~40% of the family is held out; every search-held-out pair is < 0.5 (asserted). Eligible: >= 4 search and >= 3 held-out compounds.
* **Result: 136 eligible families** (96 with >= 10 compounds, 61 with >= 15); 1,473 search and 1,212 held-out compounds; by fold
  28 / 38 / 22 / 24 / 24. The 80-family stop rule **passes**. Eligibility ignores activity by design, and the largest families are
  receptor classes (COX, adrenergic, dopamine...) whose cytotoxic content is unknown: a family with no viability signal can only produce
  null bets for every arm, which dilutes but does not bias the paired contrast. **[OPEN]** whether to restrict to families with
  search-side activity (allowed only from `D_search` outcomes, so only in Stage 1, declared before any held-out read).
* Lineages: 21; held-out lineages (7, by salted hash): colorectal, gastric, kidney, peripheral_nervous_system, skin,
  upper_aerodigestive, urinary_tract = 175 lines; search lineages (14) = 370 lines. Line counts are not independent units.
* **[OPEN] Comparator set F'** = other-family compounds of the same fold; they are not purged against the held-out compounds. Fix before
  freezing: either purge F' to Tanimoto < 0.5 from F's held-out compounds or state that F' similarity is irrelevant to the contrast.

## 3. What an arm returns

Exactly one `ResearchEdit` per episode (primitive `interaction`, `split` or `local_exception`), accepted by `research_edit.validate`, hashed
before any held-out read: a state variable z, a sign, a minimum magnitude of the crossed contrast, an applicability scope and a stated
probability p of confirmation. **[OPEN] state-variable vocabulary**: a closed list built from local DepMap 19Q4 (mutation of gene g in a
fixed gene list, expression tercile of gene g, lineage indicator) and fixed before any proposal; a proposal naming anything else is
inadmissible and counts as not confirmed for that arm.

## 4. Confirmation test (held-out compounds x held-out lineages), published PRISM values, no synthetic noise

For each held-out compound d and state z: delta_d = mean over held-out-lineage lines with z = 1 minus mean over z = 0 lines of the log2
fold change. Contrast = mean over F of delta_d minus mean over F' of delta_d. **Confirmed** = registered sign, magnitude >= the edit's
declared minimum, and a one-sided permutation p < 0.05 (family-label permutation over F union F', 10,000 draws, seed 20261018).
A cell needs >= 8 lines in each z level among held-out lineages and >= 3 held-out compounds, else the edit is **untestable and counts as
not confirmed for every arm**. The held-out side is read only once per (arm, episode) through `masked_interface` role `transfer`.

## 5. Arms (same episodes, vocabulary, data view; one edit each)

Zero (random admissible edit: the base rate and the false-positive rate), Fixed (no interaction), A2 (enumerate all admissible family x
variable edits, rank by `fit_interaction` F with a stability bootstrap on the search side), A2k (non-LLM rule: "the family's target gene is
mutated or highly expressed"; needs the PRISM `target` column, **[OPEN]** mapping), A3 (agent: deepseek-flash only, <= 3 calls per episode,
ledger-capped at USD 3, the estimate is unverified), A3-blind (identities, targets and gene symbols masked). Every arm sees the same aggregate
search-side view. The A1 posterior-sampling policy is not used in P1 (it is for the optional decision secondary).

## 6. Estimands, statistics, thresholds (to be hashed)

* **P1** = mean over episodes of (confirmed_A3 - confirmed_A2), paired by episode, clustered by family (sensitivity: PRISM target class,
  **[OPEN]** table); 4,000-draw cluster bootstrap, seed 20261018; one-sided 95% bounds. With E = 136 and discordance 0.3 the paired-binary SE is
  about 0.047 and the MDE (80% power, one-sided 0.025) about 0.12; at discordance 0.4, 0.14. Dependence between families sharing targets or
  lineages may enlarge this (up to roughly double); this is not taken from `POWER.json`.
* Secondary: A3 - A2k, A3 - Zero, A3 - A3-blind, Brier score of the stated p (A3 vs A2 using bootstrap-stability p), untestable share by arm.
  Holm over the three withdrawal comparisons (P1, A3 - A2k, A3 - Zero).
* **Agent claim withdrawn** if: upper bound of P1 < +0.10; or lower bound of A3 - A2k <= 0; or A3 does not beat Zero.
  **Typed-edit thesis withdrawn** if neither A2 nor A3 beats Zero's false-positive rate by more than 0.10.
* **Decision secondary (S2)** only if the cheap headroom check (H0) is >= 15%: confirmed edits may change which contexts are read and where
  nominations are refused, with the backend fixed; predictor-changing edits are descriptive in advance.

## 7. Limits

Exposed data; memorisation of published PRISM/DepMap associations cannot be excluded (A2k and A3-blind bound it); confirmation needs a later
screen (sealed PRISM 24Q2, not authorised); truer edits may not change decisions (R1 precedent); eligibility ignores activity.

## 8. Freeze plan (not executed)

FREEZE0 will hash this contract, `STAGE0.json`, `stage0_families.py`, `research_edit.py`, `masked_interface.py`, the state vocabulary, the gene list
and the A2k mapping, after the [OPEN] items are closed. `STAGE0.json` recomputes byte-for-byte (`verify.py`).

## 9. Closure of the [OPEN] items and run order (authorised by the user 2026-10-18: "full permissions until the test is completed")

Authorisation scope: use of search-side outcomes, deepseek-flash calls and one held-out read through `masked_interface`. **Not** authorised
and not done: opening any sealed tier (PRISM 24Q2 not local), downloads, commits, pushes.

* **Comparator F'**: other-family compounds of the same fold, purged to Tanimoto < 0.5 from every compound (search and held-out) of the
  family (`obs_core.build_world`; tested).
* **State vocabulary** (closed): `expr:<gene>` (above the panel median, DepMap 19Q4 expression) for the 40 DRIVERS and every PRISM `target`
  gene of the eligible families present in CCLE expression, and `mut:<gene>` (damaging or hotspot, non-silent) for the 40 DRIVERS. 1,211 variables;
  admissible = >= 8 lines in each state level in both search and held-out lineages (1,187). Counts are metadata, so no arm can choose an untestable
  variable; an edit with < 3 valid held-out compounds is untestable and counts as not confirmed.
* **A2k**: top-3 target genes of the family by compound count; first admissible of `expr:g`, `mut:g`; sign -1, magnitude floor, p = 0.5; no
  admissible target -> no edit (counts as 0). Many hashed-ID families have no target annotation, so A2k covers fewer episodes (reported).
* **Target-class cluster** (sensitivity): the family's most frequent PRISM target gene, else the family.
* **Confirmation**: magnitude floor 0.10 log2FC for every arm; >= 4 finite lines per state side per compound; >= 3 valid compounds each side;
  one-sided family-label permutation p < 0.05 (10,000 draws, seed 20261018). Zero = mean over 20 random admissible edits per family.
* **Agent arms**: deepseek-flash through `src/agent/llm.py`; <= 3 calls per (episode, arm); shortlist = top 12 admissible variables by search-side |Welch t|
  plus the full vocabulary (A3-blind: anonymous codes, no family name, no targets). A2 stated p = bootstrap stability of its pick (200 resamples).
* **Run order**: FREEZE0 (this contract, code, STAGE0.json) -> `run_stage1.py` (all edits, write-once `EDITS.json`, `LLM_LOG.json`) -> FREEZE1 ->
  `run_confirm.py` (ONE masked transfer read, write-once `RECORDS.json`) -> `analyse_obs.py`. No regeneration of agent edits after the first run.
* **Not run**: the decision secondary S2 and the H0 headroom check (declared descriptive / not run); the A1 and campaign code are unused here.
* The claims, withdrawal rules and thresholds of section 6 stand unchanged. Cost: reported from the LLM log; the USD 3 cap is an unverified estimate.
