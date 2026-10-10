# Block M: calibrated falsification of executable mechanism hypotheses

Started 2026-10-10. This file states the scientific problem and the design intent before any L1000
value was read. The registered protocol, thresholds and freeze are in `PROTOCOL.md` and
`FREEZE.json`, written after development and before the sealed confirmation run.

## 1. The problem

A perturbation acts on cells through a mechanism we cannot observe directly. What we can observe is
a small number of affordable profiles: here, landmark-gene transcription in one of nine cell
contexts at one of two times. Several mechanisms are plausible. The scientific task is:

* decide which candidate mechanisms the observations **falsify** and which survive;
* choose the next observation that would falsify the most survivors;
* say when two mechanisms **cannot** be separated by any affordable observation;
* say when **no** candidate fits, so that the hypothesis set itself must be revised;
* and keep the rate of wrongly falsifying the true mechanism at or below a declared level.

Mechanism here means the drug's annotated mechanism class (Drug Repurposing Hub). That is a
target-level mechanism with known ground truth, which is why it can be scored. Hypothesis
components that are finer than the class (context requirements, timing, direction of specific
genes) are scored separately as claims of the hypothesis.

## 2. Why it is hard, and why MAESTRO is relevant

* **Convergence.** Many mechanisms end in the same generic programs (proliferation loss, stress).
  Two mechanisms can look alike in one line at 24 h and differ in another line or at 6 h.
* **Context and time gating.** Responses depend on lineage and genotype and unfold at different
  speeds. MAESTRO's block K found that information about 5-day fate appears at 24-48 h, and earlier
  blocks found some mechanisms separable only at 72 h.
* **Few or no reference drugs.** Most classes have one to five drugs; many have none in the data.
  A data-only world model cannot represent a mechanism it has never seen.
* **Overconfident elimination.** MAESTRO's belief planner under-forecast wrong eliminations about
  five-fold on external data, and its scenario cards under-forecast P(wrong) 2-19 fold. Likelihood
  elimination is not a calibrated falsification test.
* **Plausible but non-predictive language.** Recent work (Yuan et al. 2026) reports that LLM
  mechanistic reasoning over-predicts differential expression and can lose to a gene-frequency
  baseline. An LLM's hypothesis is a claim to test, not evidence.

`task.md` already requires that a hypothesis set conflicting with all accepted evidence be marked
invalid. No code in `src/` implements that requirement.

## 3. Proposed method (design intent)

1. **Executable mechanism hypothesis (EMH).** The agent writes, for each mechanism class and before
   seeing any measurement, a typed object: direct targets; proximal and late landmark genes with
   directions; generic programs; kinetics; expected magnitude at 6 h and 24 h; expected response in
   each of the nine lines; context requirements; falsifiers; literature citations restricted to
   retrieved PMIDs. Levels are ordinal; the agent supplies no numbers (`emh.py`).
2. **Two compilers into a predictive world model.** A *data* compiler builds a mechanism-
   conditioned model from reference drugs of the class: a prototype per (line, time) and a shared
   potency that couples a drug's observations across lines and times. A *knowledge* compiler turns
   an EMH into the same kind of model, with amplitudes calibrated on reference drugs of other
   classes. A class without reference drugs exists only through the knowledge compiler.
3. **Calibrated falsification.** A nonconformity score compares the observations with each
   hypothesis's compiled prediction. Its null distribution comes from reference drugs scored
   against their own (left-out) class under the same observation set, so the rejection rule
   carries a split-conformal guarantee on marginal coverage of the true class, conditional on the
   design being chosen without the scored observation.
4. **Falsification-driven design.** The next observation minimises the expected number of
   surviving hypotheses, simulated from the compiled models with resampled reference residuals.
5. **Identifiability and adequacy.** Pairs that no option separates are reported as
   observationally equivalent within the menu (`NOT_IDENTIFIABLE_IN_MENU`). If every hypothesis is
   falsified, the set is reported exhausted (`HYPOTHESIS_SET_EXHAUSTED`) and the agent proposes
   revised hypotheses from the observations; these are compiled and tested like any other.

None of the ingredients is new by itself (split conformal prediction, expected-information design,
hierarchical response models, LLM hypothesis generation). The claim under test is a capability:
calibrated, design-aware falsification over a literature-defined hypothesis space that includes
mechanisms with no reference data, with explicit identifiability and adequacy outputs.

## 4. Falsifiable hypotheses (to be thresholded in PROTOCOL.md)

* **H1 validity.** On held-out drugs the true class survives at a rate of at least 1 - alpha;
  uncalibrated likelihood elimination at matched set size does not.
* **H2 world-model content.** The mechanism-conditioned data compiler gives smaller valid sets than
  a mechanism-agnostic model and than class-permuted prototypes.
* **H3 design.** Falsification-driven design gives smaller valid sets at equal observation budget
  than fixed, random, largest-expected-response and LLM-chosen designs.
* **H4 knowledge.** For classes without reference drugs, knowledge-compiled EMHs keep valid
  coverage and falsify more wrong classes than EMHs permuted across classes; literature-grounded
  EMHs do at least as well as literature-free ones.
* **H5 identifiability.** Separability predicted from reference drugs predicts the separability
  realised on held-out drugs.
* **H6 adequacy and revision.** When the true class is withheld, exhaustion is flagged more often
  than when it is present, and agent revision recovers the true class more often than a
  deterministic nearest-class revision.
* **H7 interaction.** Four configurations at equal budget: agent without world model; world model
  without agent knowledge; agent reading world-model output through a simple interface; the full
  loop.

## 5. Units, data and splits

* GSE92742 (LINCS L1000 phase 1) Level 5 landmark signatures; nine core lines x {6 h, 24 h} at
  10 uM. Units are drugs (Repurposing Hub names, so salt forms share a role).
* `SPLIT.json` (seed 20261010, metadata only, written before expression was read): 1,586 drugs in
  424 single-mechanism classes; 726 reference, 358 development and 502 confirmation drugs; 212
  singleton classes appear only as queries.
* Development uses reference and development drugs. Confirmation drugs are read once, after the
  freeze.

## 6. Exposure disclosure

LINCS L1000 phase 1 and phase 2 data were used by earlier MAESTRO blocks (2026-09-26 to 09-27) for
measurement choice between time points and for belief planning, on a transcriptomic MoA proxy task
whose headroom was small. Those blocks used different drug pools, tiers and estimands; their
archived copies were removed in the 2026-09-14 and 2026-10-09 clean-ups. The confirmation drugs of
this block were never designated as a confirmation set before, but this session cannot prove that
no earlier analysis looked at them. They are therefore described as *held out within this block*,
not as never-seen data.
