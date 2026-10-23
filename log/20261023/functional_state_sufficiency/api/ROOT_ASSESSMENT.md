# Exact API proposal assessment before any implementation

2026-10-23. One actual response, model returned deepseek-flash, finish_reason stop,3174reported tokens (787prompt+2387completion). Original is PROPOSAL.md; generated code/pseudocode was not executed. This assessment concerns its literal data/operation claims, not all low-rank or context-dependent learning.

## The key information-contract change

The established BeatAML episode reveals8 DIFFERENT drug AUCs for ONE patient. The answer instead declares n_d=8 observations for EACH drug, across basal contexts x_i, then proposes unseen-drug evaluation. Eight patients of one drug is a potentially legitimate different public-data task, but is not the old8-drug episode and cannot inherit its published local23.49%/15.07% evidence. It would need its own patient/drug split, source predictor, support definition, measured-query availability and budget contract. We do not implement it merely because those old metrics were positive.

The assertion that the ordinary covariance update does not depend on drug identity is false: its K_QS and K_SS depend on the actual purchased/query drug identities. Its Jacobian is constant CONDITIONAL ON fixed identities, not the same matrix for every purchased panel. Rank1 is neither uniquely identifiable nor uniquely justified by an8-record budget. u,v also have the ordinary multiplicative scale ambiguity; prediction may remain identifiable without those factors being individually so.

## A precise conventional counterpart under the original episode

Write purchased residuals as r_S, disjoint unpurchased queries Q. A target-patient drug-diagonal term has Q,S submatrix0; its own query residual mean is unavailable unless query feedback has been purchased. A known source mean could supply a prior offset, but would not be target feedback. If the diagonal term is interpreted on the support vector and then masked to unpurchased queries, only

`Delta y_Q = u_Q * g(x) * mean(r_S)`

remains, where g(x)=v^T phi(x). Its feedback matrix is exactly `u_Q*g(x)*1_S^T/|S|`. An ordinary context-dependent rank1 residual predictor supplied with the same phi,u,v and pooled feedback computes the same outputs/target arithmetic. This is a specific fixed-feature operator comparison, not a claim that every learned nonlinear posterior is Gaussian or that all low-rank restrictions have equal finite-budget utility.

Under the answer's alternative8-patient/new-drug contract, a_d*mean(r_d) can be a legal target-drug mean residual computed on support patients. In that interpretation it is an intercept correction, not automatically a fitted response slope. The source-learned u_d for a genuinely unseen drug is not supplied by the equations: “nearest neighbor or frozen” needs an actual descriptor/metric/transfer rule and source-only selection. None is authenticated. We do not fill it in after the fact and call the literal answer validated.

## What the answer gets right and wrong

It correctly says unrestricted direct/multitask expressivity alone does not refute finite-sample gains of a precise restriction. It correctly separates an updater component from agent/world/RSI claims and requires later common-start/equal-budget tests. These remain valid.

Its selected baseline called conditional EB is too narrow if it means only scalar global shrinkage; competent EB can already use a structured shared covariance or context-dependent low-rank prior. That is a comparator specification issue, not proof it achieves equal finite-data risk for every learned structure. The answer provides neither a source-supported rank1 error nor a demonstrated cost advantage after estimating phi and u,v. “u_d distribution concentrated subset” is not a defined heldout-drug selector or evidence that gain must concentrate there. We do not tune such a subgroup.

The final sentence dismisses CellHealth as “health is predicted” without separating genetic and drug collections. That contradicts the supplied primary evidence:357 genetic conditions have independently measured health consensus; most drug-panel70health outputs are model predictions. Static genetic conditions can support limited component tests; lacking dynamic feedback alone does not make every updater test impossible. Three cell lines constrain transfer/RSI claims but do not prohibit a small explicit experiment. No full biological identity is required for a weak statistical predictor claim.

## Root disposition pending opposing review

**NO_LITERAL_API_FIT_GO.** Do not reopen the stopped BeatAML low-rank state/probe or consistency branch, do not invent per-drug target observations, unseen-drug loadings or state axes, and do not treat genetic CellHealth truth as predictions. A substantively specified and empirically motivated context-dependent restriction remains possible; this answer does not provide it. Three source-grounded roles are independently assessing this exact response after saving their initial originals, then actually cross-questioning each other. Their disagreements and accepted corrections remain separate from this root assessment.
