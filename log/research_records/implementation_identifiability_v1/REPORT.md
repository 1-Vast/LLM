# G0/G1 report: pharmacological implementation identifiability (AURORA-A)

Date 2026-10-19. Status: completed, exploratory, known-case. No G2-G5 work, no LLM call, no purchase,
no wet-lab work. Everything below is reproducible with `python verify.py`.

## Result in one paragraph

**G0: QUALIFIED_FOR_LOGIC_TEST** (research level: ASSET_BLOCKED). **G1 engineering:
ENGINEERING_LOGIC_PASS; G1 biology: BIOLOGICAL_DISCRIMINATION_NOT_ESTABLISHED.** The published AURORA-A
evidence is enough to test evidence interpretation, premise handling and non-identifiability, but not to
build a qualified unit: no cell context has the inhibitor, the degrader and the CRBN-null binder on one
terminal endpoint, numeric terminal values and lineage are missing, and the one contrast that decides
the implementation question (degradation versus catalytic inhibition) has no recorded legal
measurement. Recommendation: continue only at known-case logic level and collect the specified missing
evidence; do not open G2.

## A. Repository status

HEAD 59c1c7bd (`Add biological residual gate results`), working tree clean at start; 28 registered
studies; previous stop decisions preserved (PROTOCOL.md). Reusable later: `evidence_registry`,
`information_tier`, `strict_decision_review`, `claim_audit`, `evaluation_contract`. No incompatibility
found. The hypothesis labels `H_E/H_M/H_C/H_O` are defined nowhere in the repository and were not used
(open item G10 in the missing-evidence register).

## B. Evidence reconstruction (what the papers support)

Sources: S1 Adhikari et al., Nat Chem Biol 2020 (PMC7610535); S2 O'Hanlon et al., J Med Chem 2026,
CCT400028 (PMC12833858). Full text read from Europe PMC XML; digests re-verified online.

| compound | what the sources establish | what they do not |
|---|---|---|
| alisertib | ATP-competitive inhibitor and degrader warhead; raises AURKA protein; G2/M arrest (MV4-11, 12 h, 1 uM) | no viability or apoptosis arm in S1; only a rescue competitor in S2 |
| JB170 | CRBN degrader; DC50 28 nM (HiBiT, MV4-11, 6 h); S-phase arrest (0.5 uM, 12 h); viability 32% of control at 1 uM (MV4-11, 72 h); apoptosis reverted by T217D (IMR5) | S2 reports DC50 39 nM in Results and 28 nM in the Introduction |
| JB211 | methylated glutarimide, cannot bind CRBN; text says it binds AURKA without degrading it; raises AURKA like alisertib; no significant apoptosis or viability loss in IMR5 at 0.5 and 1 uM, 72 h (n=3) | **not an inactive control**; no JB211 binding or kinase-activity value found; effect sizes not extracted |
| CCT400028, 50 | DC50 29 nM, Dmax 85% (MV4-11); GI50 310 and 130 nM vs JB170 1100 nM (MV4-11, 72 h); proteomics in Kelly | no cell cycle, no apoptosis, no alisertib or JB211 arm |
| compound 57 | N-methylated CRBN-null control of CCT400028; no AURKA reduction to 10 uM (Kelly) | no viability value for 57 |
| genetic reference | siRNA gives S-phase accumulation like JB170 (ED6f-h); T217D resistance mutant rescues JB170 | no knockdown viability or apoptosis; no CRISPR or kinase-dead replacement phenotype |

Twelve condition mismatches and unsupported linkages are listed in `evidence/mismatch_register.json`
(M01-M12), for example alisertib 1 uM against JB170 0.5 uM (M01), no alisertib terminal arm (M02), S1 and
S2 sharing only JB170 and MV4-11 with different protocols (M04), and one TMT batch shared by JB170,
JB211 and alisertib (M11). Nothing was pooled across incompatible conditions.

## C-D. Units, eligibility and independence

| unit | implementations | level | main failures |
|---|---|---|---|
| U1 IMR5 | alisertib, JB170, JB211 | 2 | no alisertib terminal record; no numeric values; lineage not reported; genetic reference not on the terminal endpoint |
| U2 MV4-11 | alisertib, JB170 | 2 | doses differ in every terminal pair; no strict proximal pair; numeric values and lineage missing |
| U3 MV4-11 | CCT400028, JB170, 50 | 2 | control 57 has no terminal readout; no genetic reference; numeric values and lineage missing |

Level 1: four annotation records (JB158, JB160, JB161, S2 analogues) and one mechanistic reference (the
kinase-dead depletion note). Level 3: 0. Level 4: 0. Distinct counts: 1 target, 1 target family, 3 modes
of action (inhibition, CRBN degradation, CRBN-null binder control), 5 implementations with terminal
records, 2 cell backgrounds with terminal records, 1 generalisation family from 2 papers. Both sources
are `KNOWN_CASE_LOGIC_ONLY`. No split is authorised (`candidate_split_manifest.json`).

## E. Missing evidence (ten items, `missing_evidence_register.json`)

Missing target-implementation evidence: matched alisertib viability and apoptosis in IMR5. Missing
proximal measurement: JB211 engagement and catalytic inhibition. Missing terminal endpoint: genetic AURKA
loss on viability or apoptosis. Missing control: kinase-dead replacement; viability of control 57.
Missing numbers: ED7d and Fig 6d values, Fig S7 curves. Missing lineage. Missing independent validation:
a second target family with a matched inhibitor, degrader and CRBN-null trio. Missing costs: no price,
turnaround or failure rate in either paper.
Minimal experiment package (not run, not purchased): `A_ALI_VIAB`, `A_JB211_ENGAGE`,
`A_AURKA_KD_VIAB`, `A_KINASE_DEAD_REPLACE`, 84 wells at three replicates per arm; it would complete one
AURKA unit for development use and add no second target family.

## F. Legal action menu (`evidence/actions.jsonl`)

Six bundles with controls, replicates, wells (arms x 3) and null cost and turnaround fields. Two have a
published outcome and form the legal replay menu: `A_T217D_RESCUE`, `A_JB211_VIAB`. Four are proposed
missing evidence. Replay-menu selection by outcome availability is a retrospective-design limitation.

## G. G1 tests and what they show

* Engineering (24 tests, mutation-checked on the isolation and binding tests): hidden-outcome invariance
  of the pre-purchase proposal, one observation per purchase, no outcome-bearing ids in the child tree,
  refusal of context, time and readout mismatches, premise-conditioned updates, NONE state when all
  explanations are refuted, unresolved state when nothing separates, complete costing without double
  counting, separate evidence types, lineage dependence, deterministic rebuild.
* Replay on the legal menu (isolated process): step 0 compatible set is all four explanations; proposal
  `measure(A_T217D_RESCUE)`; after the published "rescued" outcome the set is
  {scaffold-type protein loss, catalytic inhibition}; proposal `measure(A_JB211_VIAB)`; after the published
  "no loss" the set is unchanged because JB211 can only separate the two if it inhibits the kinase, a
  premise no record resolves; final state `still_indistinguishable`. Simulated spend 36 wells.
* The two published results eliminate the two off-target explanations only at known-case, qualitative
  level. The assays that would separate protein loss from catalytic inhibition (`A_JB211_ENGAGE`,
  `A_KINASE_DEAD_REPLACE`, `A_ALI_VIAB`) change the terminal decision (`advance(degrader)` versus
  `switch(alisertib_class_inhibitor)`) in the model but have no outcome, so the chain exists by design and
  is not realised in data. The T217D rescue does not separate degradation from catalytic inhibition
  because T217D lowers warhead binding for both.
* Section 9.4 is **not met**: no level 3 unit and the realised legal outcomes do not resolve the pair.
* Noise: not assessable; absence of significance at n=3 is not evidence of no effect.
* LLM-memory contamination: no LLM was run; the case is published and any later Agent result on it
  cannot be read as rediscovery.

## H. Gate decisions

| gate | decision |
|---|---|
| G0 | QUALIFIED_FOR_LOGIC_TEST; research level ASSET_BLOCKED |
| G1 engineering | ENGINEERING_LOGIC_PASS |
| G1 biology | BIOLOGICAL_DISCRIMINATION_NOT_ESTABLISHED |
| G2, G3, G4 | NOT_EXECUTED |
| G5 | NOT_EXECUTED; CONFIRMATION_BLOCKED (no qualified independent resource; designer exposure) |

An engineering pass is not evidence of discovery capability, and G1 success would not have implied
information value.

## I. Conditional G2-G5 specification

In PROTOCOL.md: entry conditions, the seven parameters to freeze (none filled, none borrowed), primary
endpoint, M0/M1 comparison, minimal Agent contract, value formulation, 2x2x2 factorial with the
interaction contrast, two evaluation modes with separate ledgers, statistics, G5 scopes.

## J. Recommendation

**Continue only at known-case logic-test level and collect the specified missing evidence.** Priority
order: (1) matched alisertib terminal arm and JB211 engagement in IMR5 (G01, G02), (2) numeric values and
lineage for the JB170/JB211 panel from the authors or Source Data (G06, G07), (3) a second target family
with an inhibitor, degrader and CRBN-null trio on a shared endpoint (G08), because one family cannot
power a held-out evaluation whatever the other steps give. If (3) cannot be found, declare the
diagnostic direction underpowered rather than widening the search. Keep the simple baselines: nothing here
supports an implementation-aware model or an Agent.

## Verification levels

Level 1 software integrity: pass. Level 2 recomputation of stored eligibility and gate fields (no
statistics exist in G0/G1): pass. Level 3 byte-identical rebuild of all artefacts: pass. Source digests
re-checked with `--online`: pass. Level 4 independent biological confirmation: not performed and not
performable from this evidence.
