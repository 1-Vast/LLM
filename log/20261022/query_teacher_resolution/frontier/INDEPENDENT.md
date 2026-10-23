# Query-supervised synthetic gradients have a concrete published precedent

2026-10-22. **STOP the broad novelty claim “train a synthetic/local teacher by held-out query objective without true-gradient imitation.”** The authenticated SIB primary explicitly implements that principle. **Full residual-gated hidden-teacher formula: exact prior-art equivalence remains UNRESOLVED; NO_PROMOTION.** No biological performance finding is made. This position was drafted without reading current peer drafts. Root subsequently notified me that peers found the rank-one transfer restriction; that notification is disclosed rather than counted as an independent discovery here. No peer result is used to establish the primary-source conclusion.

Read the full mandatory goal-objective and update_rule_renewal/CONTINUATION.md. Checked local update_rule_renewal/root_prior query metadata, source report and existing static-SGM source, and local learned-optimizer metadata. The prior local metadata already identified arXiv 2004.12696v1 but did not contain its full method. All historical STOP scopes remain. No protected partitions, biological values, datasets, weights, or author training code were opened or executed.

## Decisive primary evidence

*Empirical Bayes Transductive Meta-Learning with Synthetic Gradients*, arXiv **2004.12696v1**, official https://arxiv.org/html/2004.12696v1 . Saved body 425890 bytes, SHA256 **a3737569e532f5c05b7a7a4c58f20a9193d9ad3d4c56d2bc3bca3afdc50104fe**, HTTP 200, UTC 2026-10-22T13:06:23.258123+00:00. Source/readable text and receipt are in sources/ebm.*. Read Table 1, the introduction's operational description, equations 5–10, Algorithm 1, Figure 2 caption, and section 5.1.1 architecture/training details plus the stated K variants. Not a full proof/appendix/code audit or replication.

The paper calls its method synthetic information bottleneck (SIB). Let S_t be labeled support, X_t query inputs, and D_t=(X_t,Y_t) labeled query during meta-training. It constructs q_{theta_t^K}(w), with theta_t^0=lambda(S_t) or a global learned initialization. The query labels are withheld from the inner inference network both during source training and deployment; they supervise the outer task objective during source training. Query *inputs* are visible to the inner procedure, so this is transductive held-out-label evaluation, not a claim that the entire query sample is unseen in the update.

Equation 7 is the outer negative ELBO:

    J(phi,psi,f) = mean_t { E_{w~q_phi(S_t,X_t)}[-log p_f(D_t|w)]
                           + KL[q_phi(S_t,X_t) || p_psi] }.

Its phi includes the initialization network lambda and synthetic-gradient network xi. Equation 10 specifies a finite inner recurrence:

    theta^{j+1} = theta^j - eta [ E_epsilon mean_i {
        xi(yhat_i) (partial yhat_i / partial w)
                    (partial w(theta^j,epsilon) / partial theta) }
        + grad_theta KL(q_theta || p_psi) ].

Here xi receives predicted query outputs; it replaces the unavailable derivative of label loss with respect to predicted output. The remaining Jacobian factors are computed, not predicted away. The explicit statement near readable-text lines 1983–2040 is decisive: “we do not introduce an additional loss” between xi and the true loss gradient, because xi “will be driven by the objective in (7).” It further says the synthetic gradient “is not necessarily a good approximation to the true gradient.” Algorithm 1 updates phi through this inference computation using the outer posterior/likelihood objective. This is concrete source evidence, not the construction of a duplicate algorithm given an ordinary name.

## Stop-gradient and cost boundaries

Figure 2 and its caption state that detach stops backpropagation down to the feature network. The associated footnote says the dependence of theta^K on f is deliberately removed to simplify the update of f. This does **not** globally detach xi or the inner recurrence from the outer objective. Section 5.1.1 freezes the pretrained feature network during the reported meta-training. A layerwise series of synthetic-gradient modules for Bayesian feature-network updates is discussed as future work; that passage is not evidence that SIB implements the exact hidden-layer teaching rule proposed here.

Reported architecture: a three-layer xi MLP with hidden width 8c for c-way classification, a support-feature class-average initialization with learned per-feature scaling, and cosine-similarity classifier. Feature network choices include Conv-4 and WRN-28-10, pretrained on source classes. The source reports 40000 SGD training steps, batch size 8, learning rate .001, and 1000 validation tasks reused for hyperparameter selection. Default query set size is 15c. The comparison includes finite K=1,3,5 synthetic-gradient steps. These are author-described settings, not our execution or a fairness certification.

Deployment runs lambda(S), then K classifier/posterior update passes over the available query inputs with xi and the relevant Jacobians/KL term. Source pretraining and outer differentiation are not free, and query input access is part of the information/cost contract. The paper supplies a finite computation; it is not merely an ideal Bayesian argmin that an ordinary comparator would need infinite effort to solve. No measured runtime/memory parity with our teacher is established.

## Comparison to the previous frontier rule

Our rule uses fixed legal key k, u=Ak, h=tanh(u), e=y-b^T h, r=tanh(P[k;u;b]), followed by A'=A+eta_A e r k^T and b'=b+eta_b e h. P and initialization/rates were proposed to be trained through support recurrences by held-out query squared loss plus a fixed pairwise ranking loss. No training has actually been performed.

| Component | Authenticated SIB | Frontier rule | Evidence consequence |
|---|---|---|---|
| Teacher learning signal | Query-label likelihood plus KL through finite inference; no gradient imitation loss | Query functional squared/ranking loss through finite support updates | The broad external-query teaching principle is already implemented; changing the task loss alone does not establish a new core. |
| Inner teacher input | Current predicted query output vector | Labeled support key, hidden preactivation and head; residual multiplied afterward | Input dependence is different; literal whole-program equality is not established. |
| Updated state | Classifier/posterior parameters reached through output Jacobians | Hidden A and head b, with explicit rank-one A step | SIB does not in the inspected implementation directly predict our hidden preactivation error. |
| Unlabeled query access | Used during inner transductive adaptation | Not used by a single support update; evaluated afterward | One may not give SIB free query access or deny an allowed query pool to a deployment control. |
| Signal constraint | xi is not required to imitate true gradients; can act without query labels | Hidden write forced to zero whenever support residual is zero | A specific representational restriction; no benefit of this restriction is shown. |
| Detach | Cuts feature-network dependency in inference | Local target interpretation holds target fixed; explicit recurrence must retain outer P derivative | Both require correctly scoped differentiation; global detaching is not the claimed teacher training. |
| Finite cost | K query passes plus finite MLP/Jacobians; pretrained features and source meta-training | Per-support products Ak, P[k;u;b], rank-one write and head step; source unroll cost | No cost-preserving full reduction proved; the broad learning mechanism nevertheless has a real finite precedent. |

The earlier 2009.09675 static-SGM source establishes local activation/label-conditioned synthetic gradients, MAML-associated pretraining and frozen transfer, but trains SGMs against true gradients. SIB resolves the missing objective-level precedent directly. Combining facts from two papers does not prove a single published implementation equal to every part of our formula. Conversely, the remaining exact tanh parameterization, residual multiplication and domain replacement do not become a qualified innovation simply because that exact string was not found. A concrete computational/statistical advantage of those differences is still absent.

## Minimal executable discriminator and current decision

A minimal **interface discriminator**, not a biological performance experiment, is now defined: hold support observations, model state and teacher parameters fixed, vary only unlabeled query inputs, then compare the state returned by one inner update. Our A',b' are invariant because the update reads no query inputs. SIB equation 10 can change because both xi(yhat_i) and the classifier Jacobian depend on those inputs. For example, in the deterministic scalar linear-likelihood part of equation 10 with fixed xi=1 and zero KL contribution, w'=w-eta*mean_i x_i; changing mean query x changes the update. This finite witness falsifies a proposed **whole-program** equality reduction without pretending to prove a new contribution. It uses a declared specialization of the source recurrence, not a reproduction of its classification experiments. It is specified here and not executed, because source-level input dependence already establishes the distinction and root requested no duplicate structural toy.

The stronger useful next test must target the residual-gated hidden write itself at common information/compute, not only compare it against the 2020 true-gradient imitation teacher. A faithful query-trained synthetic-gradient control and a support-only gradient-imitation local control would separate objective choice from local representation choice; any transductive SIB adaptation must be labeled and charged as such. No biological pilot is justified merely to show that one untrained formula differs from another. There is currently no demonstrated functional task requiring this parameterization, no new biological constraint yielding a justified teacher direction, and no finite-cost/variance advantage claim beyond hypothesis.

Decision: **QUERY_ONLY_TEACHER_OBJECTIVE_NOT_NEW; FULL_FORMULA_EXACT_PRIOR_UNRESOLVED; NO_PROMOTION.** This is narrower and stronger than the preceding unresolved broad-objective status, without reviving a false complete-equivalence claim. World-model, agent, inheritance efficiency and improved-improver value remain untested. Family membership is not a rejection reason. Full project goal ACTIVE / NOT_ACHIEVED.

## Request and provenance accounting

Exactly three requests were attempted under this phase cap: (1) SIB official HTML above, HTTP 200; (2) targeted export.arxiv.org metadata query for learned local losses / meta-learning backpropagation / learning to teach, HTTP 429; (3) a remembered candidate identifier/title, https://arxiv.org/html/1808.03044v2, HTTP 404. Failed bodies and receipts are retained. The latter two provide no usable bibliographic or algorithm evidence and were not retried. This record does not claim that all locally available papers or all relevant prior work were exhausted. No sources beyond this cap were requested.

Code is only research/query_teacher_resolution_frontier_20261022/source.py. New records only this frontier directory. Git HEAD inspected: 47a0e2dea5a7dd42379fa17eb3621caf6bd0114c. No experiment, source author-code execution, API model call, biological label access, or data/weight download occurred. The source request script's plain-text extraction preserves mathematical TeX alongside text; cited equation numbers are the primary location anchors.
