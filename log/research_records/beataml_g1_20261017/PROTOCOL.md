# Beat AML gate G1: does the low-rank state model beat a strong static model with feedback, net of an extra round?

Study: `research/beataml_g1_20261017`. Written 2026-10-17 before the G1 run and frozen by `FREEZE.json`.
Local only, $0, no provider call, no new data, no sealed tier. Nothing in `context_transfer_20261017` or
`feedback_attribution_20261017` is edited; their code is imported read-only.

## 1. Question and gate

`feedback_attribution_20261017` (REPORT section 6) fixed gate G1 and left it open:

> Pre-register one candidate before computing it: the coherent score, plus exploit-first probes with
> k in {4, 8, 12} chosen on source patients; together with "S_ridge + feedback", a ridge prior updated by
> the same readouts; tested against A_item, S_ridge and D. Proceed only if the candidate beats S_ridge,
> the strongest one-round model, by more than 0.05 hits per sample at the lower bound, net of 0.05 per
> extra round. Otherwise stop the low-rank state model, and keep only the feedback design pattern on
> whichever prior is strongest.

This study runs that gate, once, on the exposed Beat AML 2.0 domain. It is **development**, not
confirmation: Beat AML shaped the confirmation, its repair and this design.

**The gate (registered, strict reading).** Let `diff` be the per-sample total hits of the frozen candidate
minus the total hits of S_ridge over the same 16 queries, `lo` the lower end of the 95% patient-cluster
bootstrap interval of its mean, and `extra` the extra assay rounds of the candidate over S_ridge (2 - 1 = 1).

    G1 PASSES  iff  lo - 0.05 * extra > 0.05      (i.e. lo > 0.10 hits per sample)

Two weaker readings are reported but do not decide: gross (`lo > 0.05`) and net-positive
(`lo - 0.05 * extra > 0). The 0.05 hits per round is the declared value of a round (about 72 h on banked
cells), not a measured price. The gate is a single pre-registered test, so there is no multiplicity
adjustment.

**Consequences (pre-registered).**

- G1 passes: the candidate may be carried to gate G2, which needs a new, independent, powered domain that
  is not local; nothing is run or built here beyond a statement of what G2 would need.
- G1 fails: **stop the low-rank state-model branch**. No further variant of
  `BridgedTransferModel` (rank, prior, scorer, probe rule) is developed on this domain. The feedback design
  pattern (a few exploit-first probes, one update, the rest) is kept only on whichever prior this study shows
  to be strongest, and only as far as `RF - S_ridge` shows a net gain. A failure is reported as "no benefit
  at the declared margin and round price", never as "no better than ridge" unless the interval says so.

## 2. Domain, folds and comparability

- Beat AML 2.0: 520 primary AML samples from 479 patients, 165 inhibitors, probit AUC, frozen selective
  events (robust z <= -3, residual to the sample median, items measured in >= 100 samples), as built by
  `context_transfer_20261017/data_beataml.py` and read through `feedback_attribution_20261017/common.py`
  (inputs refused unless their digests equal the confirmation's).
- Outer folds: the confirmation's five patient-disjoint folds (salt `context-transfer-subject`). Model and
  every statistic fitted on a fold use that fold's source patients only. Tie-breaks use the same hashed item
  order. Query: one archived 7-dose AUC profile; 16 queries per sample; an unmeasured pair is a spent query
  with no hit (archive task).
- Rank: 20 for every low-rank arm (the attribution study's primary configuration). Availability weight
  `q` = the model's source archive coverage for every arm.
- Outcome: **total** known frozen events among the 16 queried inhibitors, per sample (probe queries count).
  Total hits, not follow-up hits, so one-round and two-round arms are on the same footing.
- Exposure (declared): `feedback_attribution_20261017` already computed, on these samples, the totals of the
  coherent low-rank arms at k = 0, 2, 4, 8 with probes chosen by the coherent low-rank score
  (0.808, 0.867, 0.900, 0.965) and the follow-up hits of S_ridge after four population-prior probes. The
  quantities this study adds were **not** computed before the freeze: S_ridge choosing all 16 queries,
  k = 12, the ridge-plus-feedback arm, the inner choice of k, and every contrast below. A parity check on
  fold 0 of the previously computed arms ran before the freeze; it prints no G1 contrast.

## 3. Arms (all spend 16 queries per sample)

| Arm | Prior | Probes | Update | Rounds |
|---|---|---|---|---|
| `A_item` | empirical item ranking: `q` x source event rate | none | none | 1 |
| `S_ridge` | drug-specific ridge on the sample's 30 basal PCs (the attribution study's S_ridge) | none | none | 1 |
| `C0` | low-rank RNA state, coherent score | none | none | 1 |
| `RF` | S_ridge | top-k by S_ridge | conditional-Gaussian update of the ridge residuals (section 4) | 2 |
| `E` | low-rank RNA state, **promoted** score | top 4 by promoted score | low-rank posterior (the confirmed `b_exploit`, rank 20) | 2 |
| `CAND` (frozen candidate) | low-rank RNA state, coherent score | top-k by coherent score | low-rank posterior | 2 |

`k` for `CAND` and for `RF` is chosen separately for each outer fold from {4, 8, 12} on the fold's source
patients only (section 5). The totals at every fixed k (`C_4`, `C_8`, `C_12`, `RF_4`, `RF_8`, `RF_12`) are
recorded and reported, but only the chosen-k arms enter the gate and the decomposition.

The candidate is exactly the coherent exploit-first design of the attribution study (`x4_coh`, `x8_coh`
there) with `k` selected inside the fold. Its score, probe rule, update and tie-breaks are unchanged.
`S_ridge` is that study's `strong_state` S_ridge probabilities, used to choose all 16 queries.

## 4. The ridge-plus-feedback arm (`RF`), defined once

Inputs per outer fold (source patients only):

- For each inhibitor j with >= 30 measured source samples and a valid event threshold: ridge prediction of
  its AUC from the 30 basal PCs, with the penalty chosen by leave-one-out over `RIDGE_ALPHAS`; the same for
  the sample median G. These give the S_ridge mean `m0_j = yhat_j - a_j - b_j Ghat` and variance `v0_j`
  exactly as `strong_state` computes them, and the event probability `Phi((c_j - m0_j) / sqrt(v0_j))`.
- Leave-one-out residuals of the ridge fits give a residual matrix `R` (source samples x (items + G)).
  `Sigma` = pairwise-complete second moments of `R` (a pair needs >= 30 common samples, else its
  covariance is 0), shrunk toward its diagonal by `lambda = 0.1`, then projected to positive definite by
  clipping eigenvalues at 1e-3 of the mean eigenvalue.

Update for one sample with probe set P (exploit-first under S_ridge) and returned readouts:

    e_P  = y_P - yhat_P                               (ridge residual at the returned probes)
    s_j  = Sigma[j, P] - b_j * Sigma[G, P]            (covariance of the event residual e_j - b_j e_G with e_P)
    m_j  = m0_j + s_j Sigma_PP^-1 e_P
    v_j  = max(v0_j - s_j Sigma_PP^-1 s_j', 0.05 * v0_j)
    p_j  = Phi((c_j - m_j) / sqrt(v_j))

With no returned readout the update is empty and `RF` equals `S_ridge` on the remaining queries. It uses
the same readouts as `CAND`, a fixed event (like the coherent score), and no latent factor model and no
Virtual Cell. A sensitivity version `RF_s` uses `lambda = 0.5`; it is reported and never used to decide.

## 5. Choosing k on source patients only

For outer fold f the fold's source patients are split into 3 patient-disjoint inner folds by the hash
`g1-k:<f>`. For each inner fold, every model and statistic is refitted on the other inner folds, and the
arm is replayed on the held-out inner samples at k = 4, 8, 12. `k` = the value with the highest mean total
hits over all inner held-out samples; ties go to the smaller k. The outer targets are not read until `k` is
fixed (a test perturbs the outer targets and checks that the choice does not move). `RF` has its own inner
choice with the same rule.

## 6. Reports (all in RESULTS.json)

Paired differences of per-sample totals, patient-cluster bootstrap 95% interval, one-sided sign-flip p
(frozen `common.paired`). For every contrast the mean, interval, extra rounds, and the net lower bound
`lo - 0.05 * extra_rounds`.

- **Gate:** `CAND - S_ridge` (registered above), with the strict, gross and net-positive readings.
- **Model versus extra observations** (unadjusted, descriptive):
  - `C0 - S_ridge`: the model's value with no observation, one round each.
  - `CAND - C0`: the value of the probe round for the candidate.
  - `RF - S_ridge`: the value of the same probe round for a ridge prior.
  - `CAND - RF`: the model's value when both get the same two-round protocol.
  - identity: `CAND - S_ridge = (C0 - S_ridge) + (CAND - C0)`.
- **Other comparators:** `CAND - A_item`, `CAND - E`, `E - S_ridge`, `S_ridge - A_item`, `RF - A_item`.
- **Sensitivity (not deciding):** every fixed-k arm against S_ridge; `RF_s`; per-fold gate contrasts; the
  chosen k per fold and the inner means; probe return share and wasted queries per arm.
- **Precision statement.** The attribution study's intervals for related two-model contrasts were about
  +-0.05 wide. The strict gate therefore needs a point estimate of roughly 0.15 hits per sample. A failure
  with an interval that straddles the margin is "not demonstrated", not evidence of absence.

## 7. Parity (stop conditions)

Before any record is written, on all 520 samples:

1. `C_4` and `C_8` totals equal `t_x4_coh` and `t_x8_coh`, and `C0` equals `t_vc0_coh`, of the attribution
   study's primary records (sample by sample);
2. `E` total equals `probe_hits + h_D` of that study's `probes_vc` records at rank 20;
3. the S_ridge probabilities equal `strong_state(...)["S_ridge"]` of that study, fold by fold;
4. `RF` with all readouts withheld ranks exactly like `S_ridge` (checked on synthetic data in tests).

Any mismatch stops the run with `PARITY_FAILED` and nothing is written.

## 8. Cost accounting

Queries 16 per sample for every arm (about 112 treatment wells if run). Rounds: 1 for `A_item`, `S_ridge`,
`C0`; 2 for `RF`, `E`, `CAND`. Compute seconds are recorded. No LLM, no wells, no new data.

## 9. Files hashed by `FREEZE.json`

`PROTOCOL.md`, `g1_arms.py`, `g1_run.py`, `g1_analyse.py`, `test_science.py`. Not hashed: `DEVIATIONS.json`,
`seal.py`, `verify.py`, run outputs and the parity reference copied from the attribution study.
