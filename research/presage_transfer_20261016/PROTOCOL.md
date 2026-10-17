# PRESAGE-inspired target-pathway transfer: bounded P0 development gate

Written before this study reads PRISM response values. Grade: development on previously
exposed PRISM 19Q4, never fresh confirmation. No PRISM 24Q2 or paid API access.

## Question and stopping rule

Does a functional gene representation improve unprofiled-drug viability-profile
prediction beyond chemistry, mechanism class, shared-target identity and empirical
neighbour transfer? This is a PRESAGE-inspired pharmacological adaptation, not a
PRESAGE reproduction. No genetic-to-drug response equivalence is assumed.

P0 passes only if the pathway arm's compound-macro Pearson gain over **every**
non-biological baseline is at least 0.01, its family-cluster bootstrap 95% lower
bound is positive, and its mean score exceeds all 20 correspondence-permuted arms
(randomisation p <= 1/21). The 0.01 threshold is a development screening requirement,
not a cost-validated clinical effect. If P0 fails, stop P1/P2/P3 and LLM expansion.
The only lower-burden alternative is the strongest already-run conventional baseline.

The proposed later methodological difference is choosing an observation jointly with
its evidence-conditioned transfer revision to maximise terminal functional benefit.
Falsifier: fail to beat a development-selected fixed sparse design and fixed-model
Bayesian design at equal assay/proposal/compute budgets on separate terminal outcomes.
P0 does not test that methodological contribution.

## Sources and split

Use existing raw PRISM 19Q4 replicate-collapsed primary screen (2.5 uM; source time
not individually authenticated), treatment metadata and the retained knowledge-reality
compound census. Reactome_2022 from the Enrichr distribution is a non-response
pathway-membership annotation, fetched as a byte-pinned snapshot. Reactome's direct
host refused access. Do not use the unqualified local ESM cache, MAP text embeddings,
CCLE outcome-fitted projections or PRESAGE's response-containing cache.

Eligibility: every compound in the metadata-only retained census, every line with
a nonmissing DepMap ID in the primary screen's cell metadata (amendment A1 excludes
the ten CONTROL_BARCODE spike-in rows, which are not cell lines).
No activity, observed-effect or response-missingness
filter. Average upstream columns sharing a Broad core; these are dependent releases,
not independent experiments. Refuse metadata/identity mismatch. Use existing five
family folds, but reassign all families connected by compound connectivity to one
fold before reading outcomes. Record remaining scaffold, target and MoA overlap;
claim unseen compounds only, not unseen scaffolds, all targets or contexts.

All same-compound responses are withheld from that compound's training. No anchors.
Assay-line-specific decoder outputs are legitimate known-context inputs; no unseen-cell
or contextual-adaptation claim. Terminal outcomes here are held out from fitting but
are historically exposed processed measurements, not independent culture confirmation.

## Representation and models

Morgan radius 2 / 2,048 bits, fixed Gaussian projection to 64 dimensions; mechanism
membership projection to 64; functional gene pathway membership projection to 64.
Projections are fixed label-free draws; no PCA, text embedding or whole-outcome scaling.
Gene rows are normalised individually. Average target vectors per drug. Apply a fixed
coordinate rotation for inhibition, activation, degradation, mixed and unknown classes;
do not sign-flip inhibition into knockout. Metadata annotations are candidate targets,
not measured engagement. Unknown targets have zero prior features and the chemical
branch remains. No dose/time transport is fitted.

Ridge arms: chemistry; MoA; chemistry+MoA; chemistry+MoA+matched random target
embeddings; chemistry+MoA+pathways; pathway alone. Last two combined arms have
identical capacity. All use alpha in {1,10,100}, selected by raw-response MSE on
one held-out *training* fold, then refit on all outer training folds. Features are
centred/scaled using training rows only; targets use training line means. Training
missing entries are imputed to that mean, explicitly an approximation to masked loss.
Additional baselines: chemical Tanimoto neighbours and ungated chemical+target/MoA
neighbour averaging, using the existing RKT neighbour parameters. The production
RNA RKT calibration/certificate is inapplicable to viability and is not transported.
Fixed fusion averages pathway and chemistry+MoA predictions; ungated residual transfer
fits pathway ridge to training chemistry+MoA residuals without reliability gating.

Twenty global gene-to-pathway correspondence permutations preserve target sharing,
drug MoA, coverage, target-degree bin and pathway-count bin. They permute **feature
rows**, leaving gene names and drug-target edges fixed; this is not consistent renaming.
Matched random embeddings preserve identity/sharing and coverage at the same dimension.

## Outcomes, uncertainty and reporting

Primary: per-compound Pearson correlation across measured lines, zero for degenerate
or unscorable rows. Secondary: compound-macro raw MSE on available measurements.
Missingness is used only for scoring; no prediction or nomination sees it.
Nominate 1, 3, 5 or 10 lines per compound from predictions alone, ties by fixed line
index. A hit is measured log2 fold change <= -1; missing nominations cost a slot and
score no hit. Report hit yield, recall/false exclusion and missing selections. This
is a retrospective ranking diagnostic, not a calibrated abstention rule or P2 campaign.
No expression-derived gene set score is labelled measured viability.

Use mechanism-family/connectivity components as bootstrap clusters, 2,000 resamples,
seed 20261016. Cells are not independent trials. These clusters still do not authenticate
culture/batch independence. Freeze protocol, code, metadata, representation and raw
source bytes before running; replay checks authenticate all inputs. Save per-compound
scores, predictions and split identities. Record wall/CPU time, public bytes, API=0,
real purchased assays=0; nominal nomination slots are scenarios, not invoices.
