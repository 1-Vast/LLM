# Exact original prediction task, split and transfer precedent

2026-10-23. Clarification requested by root after initial independent report saved. Uses only the already downloaded final primary JATS/README,0 new GET/experimental payload. No current peer report was read.

## Original operation and split

- Author inputs:357 consensus guide×cell-line profiles,952 Cell Painting features; outputs:70 separately modeled measured Cell Health phenotypes.
- **70 elastic-net regressions, one per phenotype**, pooled across three lines. This is not70 perline fits and not an action-conditioned transition model. The statement that guide identity is not used as an input does not establish intervention holdout.
- **Random15% consensus-signature holdout stratified/balanced by cell line**, yielding303 training and54 test examples. Training-only5fold CV tunes9 alpha values×11 mixing parameters separately per output. Original text lists the parameters; I did not rerun them or inspect the actual split file.
- This is **not reported as whole-gene holdout or guide-family holdout**. Since119 guides target59 genes across three lines, a random guide×line split permits the same gene (and potentially the same guide in another line) in training and test. Without reading split metadata, do not assert which exact gene/guide leaks actually occurred. Gene identity being absent from X does not remove dependence from shared biological perturbations and background structure.
- Shuffled-feature models and feature-class removal/sample-titration are author controls. A new method cannot cite outperforming shuffled features as adequate evidence against strong direct prediction.

## Cross-line work already done

The authors separately performed **cell-line holdout**, training on two of the three lines and predicting health in the third. The main text reports that viability,S-phase,early-mitotic and death phenotypes could be **moderately** predicted in heldout lines, whereas **shape-based phenotypes could not be predicted**. These are qualitative primary-author reports referring to Supplementary FigS11; no extracted figure/table values or independent reproduction is claimed.

The report also says ES2 tends to predict better overall and had higher CRISPR infection efficiency. This is a biological/measurement-strength confound and an author observation, not proof of a specific error mechanism. DNA damage in polynuclear cells and late-mitosis percentages have low prediction performance in the ordinary random-test analysis; that statement is **not a separate quantified cross-line result** and should not be conflated with the holdout conclusion.

Thus “can morphology predict Cell Health?” and “can a model trained on two lines transfer to a third?” are both explicit original tasks. A proposed new pilot should identify a different question, e.g. legally paid feedback improving an established failure at equal information/cost, and compare ordinary pooled/conditional/refit approaches. Merely recomputing the original70 elastic nets, adding gene-blocked evaluation alone or naming condition consensus a cell world is not yet the requested new core. A valid new diagnostic can nevertheless use conventional mathematics and weaker claims without prior invention of a new operator.

This clarification does not grant same-replicate joins, many independent context generations or a full observed drug-health oracle. Initial recommendation and all source limits remain unchanged.
