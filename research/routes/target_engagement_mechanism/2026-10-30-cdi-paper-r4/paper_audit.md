# Paper audit and transfer boundary

## Source identity

You et al., *Virtual-cell verification enables self-auditing AI discovery for
immune rejuvenation*, bioRxiv v1, posted 2026-08-11, DOI
[10.64898/2026.08.04.742916](https://doi.org/10.64898/2026.08.04.742916).
Crossref, OpenAlex, the bioRxiv API and Semantic Scholar agree on the identity
and abstract. Europe PMC indexes PPR1296302 but reports no full text/PDF.

The accessible evidence is abstract-level for this follow-up. The prior local
audit contains selected indexed text passages, but no authenticated complete
paper, supplement, code, weights, prompts, logs or condition-level matrix. The
Astra audit records PDF/HTML/JATS HTTP 429, Highwire 403 and Europe PMC 500;
the public repository searches did not identify an official CellQ repository.
See `../2026-10-30-cdi-r3/doi_paper_audit_astra.md` and
`../2026-10-30-paper-virtual-cell-reference/evidence_audit.md`.

## What the paper establishes at the inspected level

The abstract reports three operations:

* PACE retains ten directionally scored, cell-type-resolved gene-set modules,
  selected for stability across four PBMC cohorts and evaluated in an in-house
  434-donor cohort.
* CellQ maps each single-cell transcriptome to eight discrete residual-vector-
  quantized tokens aligned to a language-model vocabulary. It claims
  perturbation prediction and sensitivity to weak module shifts missed by
  differential-expression recovery.
* An Analyzer–Planner–Auditor screened 110 compounds in primary PBMCs, found
  aged-down modules more reversible than aged-up modules, changed an
  equal-weight score to a balance-constrained minimum, and reports a separate
  13-compound T-cell validation.

These are author-reported claims, without abstract-level effect sizes,
uncertainty intervals, exact dose/time, replicate nesting, perturbation type,
CellQ split, or functional raw values. Compound counts are not replicate
counts. The paper therefore supports a workflow pattern, not a reproducible
mechanism for same-target affinity differences.

## Transferable principle

Use a compact, directional state representation as an auditable intermediate;
keep each module visible; and require an external function assay to validate a
score or objective revision. The virtual cell should expose its predicted state,
uncertainty and provenance. The Agent may revise a pre-registered rule only
after an independent endpoint, with the old rule and failed alternatives kept.

The paper does not justify copying eight tokens, a multimodal LLM, or the
mean-to-min rule. A small hierarchical state model can test the same principle
under public-data constraints. The relevant new object for CDI is the relation
between a matched molecular contrast and a functional contrast, not a larger
language-model representation.

## Closest-prior boundary

DrugReflector already demonstrates functional feedback revising a transcriptomic
screening proxy; MDA and BATCHIE cover model-audit/value-of-information and
budgeted biological selection. The paper's self-auditing workflow therefore
cannot be claimed as a new Agent architecture. CDI remains conditional only if
its intervention gate makes a target-mediated contrast identifiable and forces
an abstention when competing explanations remain equivalent.
