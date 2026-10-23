# Independent constructive analysis: one precise constraint, no innovation promotion

2026-10-23. Read full goal objective, previous function_update_renewal DECISION and constructive/CROSS, and searched historical DECISION records before constructing this proposal. No other current reviewers' reports read. No biological labels, raw matrices or model predictions opened; no model fitted. Native collaboration role, not a fabricated API/model invocation. All original retrieval bytes and failures are retained here.

## Application and exact mathematical candidate

Application: use limited measured state/function feedback to improve prediction and selection of gene-target combinations, with later independent contexts needed before drug or inheritance claims. The specific candidate is a **common local potential constraint on response curvature**, not generic latent factorization.

Fix observable coordinates z: one declared normalized RNA coordinate per gene, with coordinate scaling fixed before response inspection. Assume there is a C3 potential E(z), locally positive definite Hessian H at control z0, and target a introduces additive conjugate force u_a = alpha_a e_a, alpha_a > 0. The target interface, coordinate identity and positivity are assumptions, not CRISPRa facts. The response solves grad E(z0+delta z)=u, and growth is an independently fitted readout h(z). No ordering is implied for simultaneous interventions.

Write T_ijk=partial_i partial_j partial_k E(z0), a fully symmetric tensor. Expanding around control gives

    delta z(u) = H^-1 u - (1/2) H^-1 T[H^-1 u,H^-1 u] + O(||u||^3).
    delta z_ab - delta z_a - delta z_b
        = - H^-1 T[H^-1 u_a,H^-1 u_b] + O((||u_a||+||u_b||)^3).

Thus one third-derivative tensor ties pair interaction across **all RNA readouts**. Let R=-H^-1 T be the state interaction tensor. Beyond ordinary input symmetry R_i,j,k=R_i,k,j, H-weighted R must be fully symmetric. This is a concrete cross-readout restriction. For rank-r state coordinates, generic quadratic vector response has r^2(r+1)/2 interaction coefficients, while a potential's cubic tensor has r(r+1)(r+2)/6. Asymptotic reduction is about factor 3. This is only a parameter-count implication, not a finite-sample generalization theorem, identifiability guarantee, or measured cost gain; estimating H and input coordinates may erase it.

Feedback would refit H/T and readout jointly under symmetry, then propagate a changed T to unobserved readouts/combinations. This is ordinary constrained system identification with a meaningful prior unless a distinct data-supported estimation/decision operation is supplied. It is not RSI. Unknown freely learned force mixing destroys the cheap observable reciprocity test; it cannot be introduced after a failed gate to rescue this interface.

## Most direct small hypothesis gate from existing single RNA

Let M_ia denote measured single-target-a mean shift in readout i relative to the matched control, using **exactly the already declared RNA coordinates**. In the small-force limit,

    M = K diag(alpha), K=H^-1 symmetric positive definite, alpha_a>0.

For any observed target/readout overlap:

1. Offdiagonal reciprocal entries must have the same sign: M_ab M_ba >= 0 (zero patterns also agree in exact arithmetic).
2. Every nonzero triple obeys the diagonal-symmetrization cycle identity

       M_ab M_bc M_ca = M_ba M_cb M_ac.

3. Some positive column scaling must make the matrix symmetric positive definite; in particular diagonals must be positive and 2x2 principal minors of K positive. Cycle/sign tests alone are necessary, not sufficient.

The force magnitudes cancel in these identities. A known positive rescaling of each RNA coordinate, with its force transformed as the dual covector, does not change the sign/cycle properties. Conversely an arbitrary latent rotation plus an unconstrained target input map changes the hypothesis: this gate authenticates only the specified target-force interface. M units are normalized expression units; alpha units are energy per that coordinate, and K units are coordinate_i*coordinate_j/energy. Taking z to be logCP10K is a mathematical model choice, not evidence that transcriptional forcing is physically conjugate to logCP10K. A potential in molecule-count coordinates need not imply a potential with the same naive target forcing after nonlinear log transformation.

**YES: an existing single-RNA-only, source-only feasibility gate is possible, without paired growth or new double-RNA assays.** It can falsify the literal common linear susceptibility + positive target-local force interface; it cannot falsify every nonequilibrium response, all nonlinear potentials, or the full drug discovery goal. The original CRISPRa perturbations are finite endpoint shifts, not differential doses. Therefore failures on M can reflect nonlocal/finite forcing rather than absence of an underlying local potential. State this in the gate's name and decision. Do not infer a physical violation of reciprocity from uncalibrated endpoints.

Before numerical opening freeze coordinates, target overlap, missing values, technical control centering, normalization, scale-aware distance to the symmetrizable cone, and a practical tolerated approximation error. Aggregate pseudobulk means permit an algebraic/descriptive compatibility check, not a confidence statement. Precision-aware rejection needs separately qualified single/control resampling or independent biological repeats; cells are not biological-task replicates. No new raw data were opened in this report. No outcome-dependent coordinate, edge or dose selection. If only normalized aggregate means are allowed, report compatibility residual rather than statistical falsification. Endpoint approximate-fit failure stops expansion of this fixed interface, and does not authorize trying arbitrary learned force maps until something fits.

Passing this necessary gate would NOT justify training H/T yet. The nonlinear pair constraint needs target-pair state observations with legal acquisition charges, and ordinary competing predictors receiving the exact same observations. Scalar growth alone does not identify functional-null state curvature. The earlier exact scalar-equivalent repair STOP remains untouched.

## Strongest ordinary competitor and novelty boundary

The strongest same-information comparator is standard unconstrained multivariate quadratic regression / symmetric-input bilinear tensor regression with matched rank and capacity selection, ordinary union refit, plus the **identical potential model with ordinary constrained refitting**. The latter is not a different architecture and must not be relabeled as an inferior control. Add a reduced-rank shared-factor response tensor with the same state/function payloads and equal full cost. A source-only pilot would compare constrained versus unconstrained estimation, not world versus direct by naming. Any later agent claim additionally needs fixed acquisition, standard active design, simple mixture and equal-total-budget search, with new state feedback equally available to controls.

No unique-expression argument is made: the unconstrained model contains the potential model. Finite-sample benefit could still arise from valid constraints, but neither the existence of a subset nor parameter reduction is a new algorithm. An actual mechanism would need an independently justified way to learn/accept/transport this constraint or to exploit it for better experiments beyond ordinary constrained estimation/design. No such distinct operation has yet been supplied. **NO_NEW_CORE_PROMOTION.**

## Primary-source checks, with limits

1. Original 2025 bioRxiv manuscript, DOI 10.1101/2025.06.27.661814v1, retained cofluct.body/text. Search metadata called it “Co-fluctuations of genes in single cells predict transcriptome-wide outcomes to perturbations”; actual original page title is **Fluctuation structure predicts genome-wide perturbation outcomes** (CIPHER). Original Methods 1.1 treats conjugate exponential tilts; 1.3 explicitly derives minimal-KL perturbation-conjugate systems; 1.4 analyzes soft modes even with asymmetric Jacobian/noise. Results explicitly uses shared control covariance and optimizes two force components for double-target reconstruction. Therefore shared covariance, soft biological programs and conjugate response are **occupied**, not fresh ideas. Its nonequilibrium soft-mode allowance does not validate full symmetric susceptibility for arbitrary gene-target forcing.

   Important evaluation limit: Methods 1.5 solves the best u_i against the measured terminal state; Methods 3 says this optimal magnitude is computed for each single and double perturbation. Its double-target reconstruction advantage should not be cited as a blind heldout-double prediction gain without fixed/independently inferred force amplitudes. This limitation does not make covariance modeling novel again. It changes the fair comparator's information contract.

2. Original 2026 Nature Communications paper **Origins and breadth of pairwise epistasis in an alpha-helix of beta-lactamase TEM-1**, DOI 10.1038/s41467-026-70627-5, retained helix_epistasis.body/text. It describes global context dependency, a two-state folding/free-energy model and saturation between log-fitness and Potts energy. This is evidence that nonlinear biophysical scalar maps already explain interaction structure; it is not evidence that human CRISPRa genes form a shared equilibrium potential. Do not substitute a global-saturation trick as a new core.

3. Original 2026 arXiv **PerturbDiff: Functional Diffusion for Single-Cell Perturbation Modeling**, 2602.19685v1, retained full original HTML. It models population distributions as random variables in RKHS to represent latent-context variability. “Functional” here means function-space diffusion, not measured growth-function supervision. It highlights why one deterministic mean-potential assumption may omit relevant population variability, but does not itself prove our constraint wrong.

4. CellxPert 2605.00930v1 HTML returned 404; no full-method claim based on its search snippet. OpenAlex search results are discovery metadata, not primary method evidence. No exhaustive novelty search claimed. The cofluct page is actual article content despite DOI landing/title metadata drift; exact bytes/version URL retained. No paper outcomes reproduced.

## Historical exclusions and decision

Reviewed earlier DECISION boundaries: fixed nuisance/nullspace constrained-ridge novelty STOP (update_rule_renewal); exact linear scalar shared-operator equivalence STOP (function_update_renewal); early-feedback mixture updater STOP (norman_feedback_transport); anchor propagation/ordinary Gaussian equivalences remain stopped. This proposal does not change their algorithms or retry their data configurations. The new **testable assumption** is positive diagonally symmetrizable target susceptibility and integrable cross-readout curvature; that is more specific than a generic subspace but not an original method yet.

Decision: **RETAIN_EXPLICIT_INTERFACE_HYPOTHESIS / NO_NEW_CORE_GO / NO_MODEL_FIT_NOW.** A tightly registered single-RNA compatibility gate is scientifically legitimate if root wants it, with interpretation restricted above. Stop that fixed interface when a frozen approximation tolerance fails; do not use a lack of biological repeats to manufacture confidence. Stop novelty promotion if the proposed update remains ordinary constrained refit or CIPHER-style force optimization. Even if it passes, do not imply agent/inheritance/joint/RSI evidence. All five contribution claims remain unestablished.

## Failures and actual resource use

Three OpenAlex GETs and four primary GET attempts; no DeepSeek calls or biological fits. One initial primary retrieval script failed because bs4 was absent; replaced parsing with standard-library text stripping, preserving original HTML. Two rg wildcard-path searches failed on PowerShell literal wildcard interpretation; the later recursive directory + glob search succeeded. All failures are recorded here and source receipts retain status/bytes/hash. Retrieved article outcomes are author claims, not our experiments.
