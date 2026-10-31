# Conditional functional response across controlled cell mixtures, v1

Frozen for an independent challenge on 2026-10-31. This is an untested research candidate, not an admitted numerical experiment, a new algorithm or an established useful Virtual Cell mechanism. Its equations below are ordinary accounting/null identities, not novelty claims. Parent: this episode's pass-1 open selection and pass-2 target/source reading. Candidate revisions used: zero of two.

## Scientific question and proposed capability

Can a cell response law conditioned on independently measured local drug exposure and environmental state predict functional burden in an unseen cell mixture or organoid condition, beyond ordinary state-specific response weighting? The proposed use is preclinical selection of interventions and follow-up measurements in heterogeneous tumors. The practical problem is separating complementary killing of existing populations from exposure-dependent changes of cellular action; a pooled synergy score does not settle it.

Inputs at use time would be pretreatment cohort identities/composition, drug identity/dose/time, matched untreated growth, and measured local exposure/oxygenation where the proposed environmental conditioning is claimed. The learned object would be a cohort's expected viable descendants per seeded cell conditional on those measurements. Integrate that response over the measured cohorts/exposure distribution to predict absolute viable burden, with uncertainty. This conditional transport relation is the hypothesis; no chosen architecture, sufficient public dataset or validated parameterization exists yet.

## Separate the known nulls

Let p_k be the initial proportion of a stable pretreatment cohort k, N0 the total seeded cells and G_k,d(T) the expected viable descendants per initially seeded cell at time T under intervention d. Under a cell-autonomous count model at fixed environment,

    N_d(p,T) = N0 * sum_k p_k G_k,d(T).

For a matched vehicle with positive G_k,0, the normalized count is

    Y_d(p,T) = sum_k w_k(p,T) r_k,d(T),
    w_k = p_k G_k,0 / sum_j p_j G_j,0,
    r_k,d = G_k,d / G_k,0.

This ordinary mixture includes differential untreated growth. Raw initial fractions are not automatically the correct weights for vehicle-normalized endpoints. Cell autonomy across population members does not imply independent action of two drugs inside one cell: G_k,AB may be an arbitrary measured/fitted cohort response. A state-conditioned ordinary model with source-combination information is therefore a mandatory rival when the candidate receives that information.

Only under a further justified within-cohort independent-action assumption for a true survival-probability endpoint, let q_k,AB = q_k,A q_k,B and use the same eligible cohort weights w in all arms. Then

    Q_AB - Q_A Q_B = Cov_w(q_k,A, q_k,B).

Consequently pooled Bliss can report excess or deficient killing solely because sensitivity varies across cohorts. The covariance identity is elementary algebra. Binary survival, a count/growth ratio and ATP luminescence are distinct endpoints; drug/state-dependent ATP per cell or proliferation prevents silently treating CellTiter-Glo as these survival probabilities. Neither the cell-autonomous mixture nor Bradley's independent feature-block composition guarantees drug independence. The latter is a product over disjoint coordinates, whereas a population mixture sums over mutually exclusive cohorts.

Post-treatment fractions alone do not identify absolute killing, stable cohort effects or transitions. They can change through selection, growth, marker changes and capture. Stable lineage tracking or another identifiable observation design is needed when state labels switch. Combination responses are not identified by pooled single-agent marginals without further assumptions or informative measurements.

## Proposed distinguishing observation

Change initial composition while controlling total seeding/density, media, duration and geometry; separately measure any exposure/oxygen variation that the hypothesis uses. Count absolute viable cells by stable baseline cohort, with matched untreated controls and independent cultures. Hold out entire preparations/donors and at least one mixture or organoid condition. State response rules and environmental adapters are frozen before those outcomes are opened.

Compare a direct condition regression, growth-normalized independent mixtures with flexible within-cohort combination action, and an established transport/mechanistic model under identical measurements and source-combination information. Compare the exposure-conditioned law to its version without measured exposure and to the applicable type-conditioned independent-action reference. Whole-mixture interpolation, extra post-treatment information or a weak pooled Bliss comparator cannot establish the proposed capability.

Useful evidence would be reproducible held-condition functional prediction or intervention-selection benefit and a response pattern that distinguishes the competing explanations. An exposure-conditioned predictor winning alone is predictive evidence, not proof of a unique cellular or physical mechanism. Nonlinearity with composition alone also does not identify communication: density, proliferation, exposure, state switching and endpoint measurement can produce it. If the conditional response fails transfer, or ordinary weighting/regression accounts for its benefit, retain that result and stop the claimed advance. No numerical utility threshold is set because no admissible task has been selected; it must be frozen before outcomes if one becomes available.

## Closest priors and the unresolved contribution

- D-SPIN already owns shared-network/state-distribution modeling and compositional program recruitment. Its inspected local original is a preprint version; final-Cell methods are not claimed audited.
- The 2026 DMG original (10.1038/s41588-026-02550-w) and 2025 AML original (10.1158/0008-5472.CAN-24-3840) already target complementary cell states and nominate combinations using measured drug effects. State complementarity, schedule changes and a target-union predictor are not new here.
- Palmer, Chidley and Sorger (10.7554/eLife.50036) supplies independent action/cross-resistance and biological-culture controls. Ordinary weighting and the covariance identity are inherited, not inventions.
- Bradley (arXiv:2509.16447v1) supplies a strong disjoint-feature-block composition principle, whose observation/factorization assumptions do not become valid for mixed cell populations by analogy.
- AIVOs (10.1016/j.bioactmat.2025.12.030) motivates cellular/environment coupling but is a review. Transport, oxygenation and rule-based simulated cells are mature methods. Exposure-conditioned mixture prediction could already be covered by established multiscale pharmacology; a distinct contribution remains unverified.

The potential contribution is a measured, transferable conditional functional relation in a specific biological system, if a qualified independent test establishes one. At this version there is no demonstrated novelty, utility, unique identification or broadly recommended new core. An independent review must assess whether even a conditional recommendation is justified and which premise still lacks evidence.

## Current feasibility and stop/restart

The DMG publisher/Reporting Summary authenticates matched monotherapy/combination orthotopic DIPG4423 tumor-volume endpoints; it also supplies state-count source-data descriptions for a different subcutaneous DIPG17 experiment. GEO GSE262775 describes 24 end-of-five-day monotherapy/vehicle scRNA samples. These are useful functional and state resources, but do not yet authenticate initial cohort composition per functional preparation, same-model composition contrasts, local exposure or the held-mixture crosswalk needed here. This is a joined-frame gap, not an assertion that public functional data are absent. AML's index-patient selected-pair flow assay and separate bulk assay retain preparation/endpoint limits.

No response workbook or selected outcome has been opened and no matrix is admitted. A necessary next gate is a source-authenticated same-preparation schema with identifiers, untreated denominators, intervention/time, independently assigned initial mixture, stable cohort observations and independent replication. If only workbook headers are needed, first obtain independent admission of a metadata-only projection whitelist; do not inspect response cells to decide eligibility. Unmet measurement conditions park this candidate. LLM agents and virtual-organ scale-up remain downstream of an independently useful Virtual Cell result.

Raw source locators: investigator/handoff.md pass-2 passages and original dmg2026.xml; scout/handoff.md pass-2 anchors and sources/pass2_elife_50036.html; the separately reviewed AIVOs report and original JATS. These original bodies remain local acquisition evidence.
