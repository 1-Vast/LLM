"""The repository's measured research experiences as PolicyExperience records (provenance and audit pattern per record).

Numbers are transcribed from `research/EVIDENCE.md` and the cited study results; `audit_experiences.py` checks that each
`record_pattern` appears in the cited evidence text and recomputes three of them from RESULTS files. Units are NOT comparable
across tasks; the dependence group is the dataset/screen family.
"""
from __future__ import annotations

from policy_memory import PolicyExperience as P

E = "research/EVIDENCE.md"
EXPERIENCES = [
    P("acq-lookahead", "A_drug_response", "PRISM 19Q4 second-pool choice, held-out groups", "one-step posterior lookahead", "fixed A-optimal design",
      -0.106, (-0.262, 0.022), "events_per_64_compounds", "internal_heldout", "not_supported", "prism19q4", E, "-0.106",
      "low held-out headroom (+7%); probabilities ~10x overconfident", "second-pool choice only"),
    P("acq-agent-vs-lookahead", "A_drug_response", "same", "agent-searched value program", "handwritten lookahead", 0.008, (-0.033, 0.054),
      "events_per_64_compounds", "internal_heldout", "not_supported", "prism19q4", E, "+0.008", "unchanged performance; 1 of 12 proposals accepted", "ten lookahead features"),
    P("fp-ridge-feedback", "A_drug_response", "PRISM purged batch, 3 pool reads, unmeasured pairs", "ridge-plus-feedback", "structure prior", 1.056, (0.626, 1.526),
      "events_per_64_compounds", "development", "supported", "prism19q4", E, "+1.056", "", "3 pools; not at 16 logical lines"),
    P("fp-r1", "A_drug_response", "same", "analogue-anchored update R1", "ridge-plus-feedback", 0.139, (-0.579, 0.870),
      "events_per_64_compounds", "internal_heldout", "not_supported", "prism19q4", E, "+0.139", "development +0.81 did not replicate; noise draw moves it as much as the CI", "kNN analogue conventional"),
    P("g1-candidate", "A_drug_response", "Beat AML 16 queries per sample", "low-rank candidate state model", "drug-specific ridge", 0.098, (0.045, 0.153),
      "hits_per_16_queries", "development", "not_supported", "beataml", E, "+0.098", "net lower bound -0.005 < 0.05 practical gate", "Beat AML only"),
    P("g1-feedback", "A_drug_response", "Beat AML 16 queries per sample", "ridge plus feedback", "drug-specific ridge", 0.083, (0.042, 0.127),
      "hits_per_16_queries", "development", "supported", "beataml", E, "+0.083", "", "Beat AML only"),
    P("obs-agent-vs-enum", "A_drug_response", "136 MoA-family bets, held-out chemistry x lineages", "agent typed edit (deepseek-flash)", "conventional enumerator", 0.022, (-0.022, 0.074),
      "confirmation_rate", "internal_heldout", "withdrawn", "prism19q4", E, "+0.022", "agent claim withdrawn; stated p 0.45 vs 0.081 observed", "closed vocabulary, one edit per family"),
    P("obs-target-rule", "A_drug_response", "same", "non-LLM target-gene state rule", "random admissible edit", 0.037, (0.003, 0.075),
      "confirmation_rate", "internal_heldout", "unconfirmed", "prism19q4", E, "+0.037", "exploratory, unadjusted; below the 0.10 margin", "target-annotated families"),
    P("seed-policy", "A_drug_response", "PRISM seed-program library, corrected contract", "seed library policy", "strong model", 0.356, (-0.088, 0.856),
      "hits_per_line", "development", "unconfirmed", "prism19q4", E, "+0.356", "ridge on the same ten features matches it", "scoped optional baseline"),
    P("ctx-bridge-feedback", "A_drug_response", "Beat AML one-shot context transfer", "exploit-first bridge feedback", "fixed bridge", 0.073, None,
      "hits_per_line", "development", "supported", "beataml", E, "0.073", "", "workflow transfer inside Beat AML, not biology", ci_note="interval in the study report, not transcribed here"),
    P("blockq-planner", "A_drug_response", "sealed GSE70138 equal-well campaigns", "certificate planner", "sparse hub fixed design", -0.044, None,
      "selective_r", "internal_heldout", "not_supported", "lincs_l1000", E, "-.044", "planner lost at N wells, wins at 2N", "L1000 landmark 10 uM", ci_note="campaign-level count test (0/11), no interval in the register"),
    P("blockn-vc", "A_drug_response", "421 sealed PRISM drugs, unseen mechanism class", "VC transcriptional transfer", "target kNN", 0.116, (0.053, 0.181),
      "selective_r", "internal_heldout", "supported", "prism_l1000", E, "+0.116", "", "adds only on 160-line screen, not on 40 lines"),
    P("blockp-agent", "A_drug_response", "975 sealed compounds, 38 campaigns", "agent loop", "virtual cell alone", 14.0, None,
      "unexpected_hits", "internal_heldout", "not_supported", "lincs_l1000", E, "+14", "p 0.075 at 7x turnaround; matched by a conventional ReAct agent", "L1000 library", ci_note="reported as total hits with p 0.075, no interval"),
]
