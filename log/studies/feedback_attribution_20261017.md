# Feedback attribution

Development study on the exposed Beat AML 2.0 domain, pre-registered and frozen before any group
outcome; `verify.py` VERIFIED. It confirms nothing. It also contains the Phase 1 audit of the
context-transfer implementation (`AUDIT.md`).

* **Shared probes.** All groups share four probes. Feedback helps without RNA (+0.096), RNA helps
  once readouts arrive (+0.065), and the low-rank update beats an overall-sensitivity update
  (+0.081). Deranging the readouts costs 0.115.
* **Weak comparator.** The RNA prior's registered gain is against a comparator weakened by an
  incoherent event score. Against the item prior it gives -0.017, and a drug-specific ridge on the
  same PCs beats it (+0.065).
* **The confirmed engine against the ridge.** The confirmed two-round engine is not shown better
  than that one-round ridge (+0.023 [-0.029, +0.077], post hoc).
* **What helps.** A coherent event score (+0.04 to +0.08) and eight probes instead of four
  (+0.065). The reference planner always chose eight. No selector beats tuned exploit-first.
* **Cost.** 0 wells, 0 USD.
* **Blocked.** Independent confirmation: no unexposed domain is local, and PRISM 24Q2 independence
  is unverified.
