# Biological depth of the virtual cell and agent: pre-registered protocol

Frozen 2026-09-26, before any SciPlex3 expression response or model output was computed in this
workspace. The machine-readable parameters are [`protocol.json`](protocol.json) and the
literature anchors are [`anchors.json`](anchors.json); the SHA-256 of all three files is recorded
in `log/20260926/README.md` before the preparation step runs. A later change to any of them is a
new version with its timing recorded, never an edit in place.

## 1. Question

Does MAESTRO's virtual cell carry **perturbation-specific biology**, or does it reproduce only
the generic response that most drugs share? And do the agent's reasoning components read a
measured transcriptional response mechanistically?

"Biological depth" is made operational as ten literature anchors and eight metrics. Every
metric is computed on **out-of-fold** predictions: a compound, with all its doses and all three
cell lines, is predicted by a model that never saw it.

## 2. Why the usual metric is not enough

A drug-response predictor can score well on gene-wise error while knowing nothing about the
drug, because most treated profiles share a large common shift (stress, proliferation arrest,
plate effects). The `systematic` arm predicts exactly that shared shift and nothing else. The
primary metric therefore subtracts it: B1 correlates prediction and observation **after
removing the mean training response at the same line and dose**. Direction anchors are scored on
the same centered shift, so an arm cannot pass them by predicting the average drug.

A direction-scramble control (B2) checks the metrics themselves: permuting the gene order of a
centered prediction must destroy B1. A metric that survives scrambling measures magnitude, not
biology.

## 3. Data

SciPlex3 (Srivatsan et al., Science 2020): A549, K562 and MCF7 at 24 h, 188 compounds, four doses
(10 nM to 10 uM), two replicates. Pseudobulk groups are cell line x compound x dose x replicate,
each matched to vehicle cells of the same line and replicate. Genes are fixed without looking at
any drug response: the 2000 genes with the highest mean expression in vehicle cells, plus every
anchor gene. Structures come from the chemCPA SciPlex subset, the Broad Repurposing Hub and, for
one compound, PubChem. Salts and stereoisomers of one molecule share a skeleton group, which is
the split unit (185 groups).

## 4. Arms

| Arm | What it knows | Role |
|---|---|---|
| `zero` | nothing | floor |
| `systematic` | line and dose | the shared response every other arm must beat |
| `ridge_chem` | fingerprint x line, dose | linear baseline |
| `knn_chem` | five nearest training structures | retrieval control |
| `mlp_existing` | repository's current learned rung | what MAESTRO has today |
| `latent_pca` | PCA latent + transition head | representation baseline |
| `latent_mae` | masked reconstruction latent + head | reconstruction-objective ablation |
| `latent_jepa` | JEPA latent + head | the upgrade under test |
| `latent_jepa_moa` | + declared pathway annotation | annotation-conditioned family |
| `latent_jepa_moa_shuffled` | + permuted annotation | control for the row above |
| `replicate_ceiling` | the other replicate | noise ceiling |

The latent arms share one **pharmacological transition head**: the latent shift is a sum of two
dose-gated directions, `g_k(dose) * v_k(compound, line)`, with `g_k(0) = 0` exactly and each
EC50 learned from structure. The first direction can capture on-target response at low dose and
the second the additional response that appears only at high dose. The factorisation is a
modelling choice; it is not evidence that such components exist.

The JEPA encoder follows V-JEPA 2 (Assran et al., arXiv:2506.09985) in predicting a **latent**
target rather than raw values, adapted to biology in two ways. The masks hide whole co-expression
modules, so the encoder must infer one gene program from others. The context and the target
are minibulks built from **different cells of the same condition**, so the representation is
pushed to encode the condition and to ignore cell sampling. The masked-reconstruction arm keeps
the masks and views and changes only the loss, which isolates the latent-prediction objective.

Encoders are pretrained only on vehicle cells and on the training fold's compounds; a held-out
compound's cells are never seen, even unlabelled.

## 5. Metrics

B1 specificity, B2 scramble control, B3 mechanism retrieval, B4 potency ranking, B5 context
specificity, B6 anchors, B7 uncertainty usefulness and B8 cross-assay coherence (exploratory),
defined in `protocol.json`. Uncertainty is clustered by compound throughout; cells are not
replicates.

Arms that receive the pathway annotation as input are excluded from B3, where it would be
circular. They are compared on B1, B5 and B6, where the annotation is a claim about the
compound whose value the measured response can confirm or refute.

## 6. Anchors

Ten anchors (`anchors.json`), each from the literature or DepMap and none from SciPlex3: HSP90
inhibitors induce HSF1 targets; a glucocorticoid induces receptor targets in A549; ER
antagonists lower estrogen-response genes only in ER-positive MCF7; trametinib lowers the MEK
pathway activity score in KRAS-mutant A549; prolyl-hydroxylase inhibitors induce hypoxia genes;
BET inhibitors induce HEXIM1; an anthracycline activates p53 targets in the TP53-wild-type lines
more than in p53-null K562; BCR-ABL inhibitors hit K562 hardest; HDAC inhibitors dominate the
response magnitude; and an IDH1 inhibitor and an aromatase inhibitor, with no functional target
in these lines, stay within the vehicle null.

Each anchor is first tested on the **observed** data (does the screen contain the biology?),
then on out-of-fold predictions (does the model reproduce it without having seen the
compound?). Only anchors that hold in the data count against a model.

## 7. Primary comparisons and verdict rules

- **P1** `latent_jepa` minus `knn_chem` on B1 over responsive conditions, paired by compound.
- **P2** `latent_jepa` minus `latent_pca` on B1: does the learned representation help at all?
- **P3** anchors reproduced by `latent_jepa` versus `mlp_existing`.

The verdict rules in `protocol.json` define "specific signal", "beyond retrieval", "near
ceiling", "anchor depth" and "knows what it does not know". The virtual cell is called
**sufficient for advisory ranking** only if it has specific signal, anchor depth and useful
uncertainty. A negative result on any primary comparison is reported as that, and the simpler
arm is retained.

## 8. Agent probe

The agent components receive an anonymised measured signature, with no name, structure or
annotation: the 20 most increased and 20 most decreased genes of each responsive line. They
choose the mechanism class from a closed list. Arms: frequency prior, the retrieval tool alone,
DeepSeek with and without the tool's evidence card, and Jev with and without it. Primary: the
paired difference that the card makes to DeepSeek. The class label is a vendor annotation, so
the score is **annotation agreement**, not mechanism accuracy. Budget caps: USD 3 DeepSeek, USD
0.5 Jev, charged by the provider ledger.

## 9. Disclosure of what was seen before freezing

Seen: the h5ad structure (cell counts per line, time, dose and replicate; 4,512 treated groups;
median 129 cells); the compound list with pathway and target annotations; the structure
resolution (187 of 188 from local sources, one from PubChem; three duplicate skeletons); the
Repurposing Hub target coverage (161 of 188); and the DepMap facts cited in `anchors.json`
(ABL1, BCR, ESR1, TP53, MDM2 and KRAS gene effects; hotspot calls; PRISM line coverage).

Not seen: any expression value of a treated group, any shift, any model fit or prediction. The
repository's earlier `evaluation/model_validation.py` was read as code; none of its outputs
exist in this workspace.

## 10. What no outcome of this protocol licenses

A pass is a statement about 24 h transcriptional responses of three cancer lines in one screen.
It is not target engagement, viability, a mechanism, or behaviour in an untested context. An
anchor reproduced by a model shows that the structure-to-response mapping it learned transfers
to that compound; it does not show that the model understands why.
