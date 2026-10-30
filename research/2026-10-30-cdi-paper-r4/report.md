# Paper-informed CDI revision: from virtual-cell verification to an intervention gate

## Finding

The user-supplied 2026 bioRxiv paper gives a useful way to use a virtual cell:
keep a compact, directional representation of a perturbation state, verify it
against an external functional readout, and version the score rule when the
external evidence exposes a failure. Its CellQ/Analyzer–Planner–Auditor story
does not, at the evidence available here, solve the narrower drug-discovery
problem of transferring a same-target molecular difference into a cell-function
difference.

The most defensible revision is an **intervention-gated target-contrast**
design. A virtual cell predicts the relative response of two same-target drugs
across contexts. An Agent selects a matched context, dose/time, target
perturbation, exposure control or orthogonal endpoint only when that observation
can separate a target-mediated world from a nuisance world at equal cost. If it
cannot, the system abstains. This is a conditional capability hypothesis, not a
new architecture or a demonstrated Agent advantage.

## Why this is the right transfer

PACE and CellQ suggest retaining directional module-level information instead
of hiding it in one score. The external T-cell assay shows the importance of
checking a proxy against function. AdaMBind suggests adapting from a small
target-specific support set; PBCNet2.0 suggests using a relative molecular
contrast. These ideas become scientifically useful only when the observation
can identify whether a molecular ordering is target-mediated or is explained by
exposure, off-target activity or assay scale.

The distinction matters for drug optimization: a stronger enzyme binding value
should change a cell decision only under the contexts where target occupancy is
functionally limiting. A predictive association from PRISM cannot establish
that path. The r3 FLT3 pilot's weak held-out association and near-zero
expression-conditioned contrast are consistent with several explanations.

## Evidence and data gate

The paper is a preprint. Full-text retrieval was bounded and failed through
429/403/500 routes; training data, perturbation classes, dose/time, replicate
nesting, CellQ splits and functional raw values remain unknown. The independent
resource scout found no public table with all required engagement, perturbation,
function, exposure and preparation fields. PRISM 24Q2 and DepMap 26Q1 are the
best cheap identity/viability/genetic anchors, while PXD047949 and an FLT3 CETSA
study are separate engagement exemplars. Their joins cannot be treated as
matched validation.

A bounded metadata download improved the screen contract but not the mechanism
gate: PRISM 24Q2 exposes screen-level 2.5 µM/5-day treatment, triplicate codes
and exact `depmap_id` joins. Its extended annotations contain 35 FLT3-target
rows, yet only two normalized target IDs joined exactly to the treatment table;
keyword search added three names without an engagement measurement. The raw
`120H` token is retained as an identifier token, not promoted to a structured
exposure field. This is a mapping result, not a biological FLT3 result.

The separate GeneEffect branch was run under a fixed 500 MB/10-minute stream
budget. The official DepMap 26Q1 file was streamed once with matching byte count
and MD5; only the header and `FLT3 (2322)` row were retained. An exact
`DepMap_ID` join to the existing PRISM 19Q4/MTS010 pair table yielded 409,428
rows from 395 cells, 153 pairs and eight nominal doses. Using Chronos dependency
tertiles (more negative values = stronger inferred dependency), the
`ΔpKd`-versus-high-minus-low dependency contrast had descriptive Spearman
`rho = 0.0717`, close to the expression-tertile `rho = 0.0601`; the repeated-row
gene-effect versus response correlation was `rho = -0.0056`. This is a
cross-release genetic concordance check, not a cellular engagement or causal
test, and it does not close the intervention data gate.

The independent overlap search found two useful near-overlap engagement
resources: CellEKT (2025; MV4-11/HEK293T, midostaurin-FLT3 probe competition,
0.1–10,000 nM, 1 h, n=2) and a live-cell kinase probe assay (2025; Jurkat,
dasatinib/dinaciclib, 60–90 min, mostly n=2). Neither exposes a verified
PRISM/DepMap/GDSC row-level barcode and dose-time crosswalk. The search therefore
keeps `data_unavailable`; no PRIDE raw files or large supplements were
downloaded.

## Minimum test

Freeze two same-target pairs, including a near-null pair, at least three
contexts, matched dose/time and exposure, target perturbation/rescue or a
qualified cellular-engagement assay, independent blocked assay days, and one
orthogonal function endpoint. Give every selector the same initial block and
remaining action budget. Compare direct measurement, ordinary hierarchical
regression, random/fixed-balanced selection and standard VOI. Evaluate the
target-gating statistic on held-out contexts and assay days, with function and
engagement kept as separate endpoints.

The result is positive only if the target-sensitive contrast attenuates under
intervention and returns under rescue while controls remain balanced. A null or
equivalent result is an honest identifiability boundary. A masked PRISM replay
may precede this study, but it cannot prove target mediation or prospective
savings.

## Current decision

Proceed only with the schema/data-acquisition gate and preserve the candidate as
a conditional pilot. Do not implement CellQ, MAML, PBCNet2.0 or a larger
virtual-cell representation, and do not promote `src/` or `tools/` code from
this round. The research objective remains active because the decisive matched
resource and intervention test are still missing.
