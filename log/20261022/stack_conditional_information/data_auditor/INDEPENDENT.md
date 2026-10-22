# Independent data/evaluation audit: STACK conditional-information gate

2026-10-22. Auditor `/root/functional_auditor`. Saved before reading any current-phase peer draft or implementation. Reviewed `PROTOCOL.md` SHA256 `8ec783e18e8f7a7716e3976bf975f34890bf51655069e7b8262e9764db23049a`, prior identity/header/collision projections and acquisition-summary metadata. No raw/XLSX access, assay-value conversion, network, provider call or fit. This document does not edit the root protocol.

**The main conditional-information question is meaningful and narrowly testable. One scientific claim needs correction before response exposure: beating D0 alone and D24 alone does not show that intermediate D history is needed beyond their joint information.** Most other concerns are operational definitions to freeze and check in the forthcoming non-fit code audit.

## Exact source and cell boundary

Existing metadata supports three Full tables, each with 1,833 named exact library-entry rows and 87 unidentified `#N/A` identity-error rows. Full wide blocks provide paired exported-row records, not authenticated well/run/replicate records. NLS in T98G+DMSO has the already documented source-supported operational live-reporter interpretation; keep its literal and do not claim exact cross-screen calibration. Acquisition-summary metadata reports v1 status200, size/SHA256 match and qualified downloads; the code must actually compare each object with its exact expected version-bound hash before opening a numerical address, rather than trusting a boolean or hashing bytes without an expected value. This auditor did not open/hash raw objects.

The concrete whitelist implied by the protocol and authenticated headers is:

| Full source | SG prefix columns (0,4,8,12,16,20,24h) | Live prefix columns in the same order | Live72 target |
| --- | --- | --- | --- |
| T98G+DMSO | C,D,E,F,G,H,I | AC,AD,AE,AF,AG,AH,AI (NLS) | AU |
| T98G+TMZ | C,D,E,F,G,H,I | AC,AD,AE,AF,AG,AH,AI (mKate2+) | AU |
| U2OS | C,E,G,I,K,M,O | BL,BN,BP,BR,BT,BV,BX (mKate2+) | CV |

Bind addresses to the exact `Full` worksheet and named-row map, not sheet order, active sheet, broad rectangular ranges or an arbitrary file. For these exports the named rows are 2–600 and 688–1921; use the frozen metadata map to establish them. A601:A687 and their responses remain closed. Blank trailing Full rows are not new observations. Header/identity metadata is distinct from assay-cell conversion.

Seven L and seven SG values per named row imply 25,662 prefix assay cells per screen and 76,986 total; there are 5,499 potential L72 target cells, authorized by role/stage. No other U2OS2h frames, no future SG, no other live times, no QC sheet/member mask, and no AUC/Norm.AUC/LED/result-side-table values belong in these arrays. The TMZ side-table Plate must not become original row plate. Library plate/position likewise supplies no authenticated screen/run plate. No response-derived drug-control identity is allowed for the 87 error rows.

The parser test should use synthetic workbooks with malformed **closed numerical cell contents** to show those contents are never converted or used. Valid XML syntax is a separate container requirement; parsing an entire XML tree without converting closed values is not cryptographic sealing. Do not use pandas/openpyxl bulk value extraction that silently converts every response. Access-ledger stages must account for every requested legal field, including invalid/absent authorized cells.

## Roles and independence

1,833 exact entry names plus the one conservatively grouped two-entry SMILES conflict gives exactly 1,832 role groups. The specified split is 1,099 train, 366 validation and 367 test groups. Preserve exact names, including their whitespace/case, in group keys; do not trim/salt-strip/fuzzy-join them. Doxycycline Hyclate and E-64 stay different entries in one role/bootstrap cluster, not a claimed common chemical. All three screens for any name share its role. The role map must freeze source/file/Full/row/literal name/group/role before responses, with no response-derived reshuffling.

The test is unseen recorded-entry generalization within the three fixed exported screens. Exact Catalog/CAS uniqueness does not prove unique chemical entities; the known shared SMILES is contradictory annotation, not verified chemical equivalence. No name/hash/row/structure/target/library layout is a model input. Same-group membership across contexts prevents the direct leakage of the same named compound's L72 from a training screen into a test screen. It does not create new-cell-line, independent-run or independent-task validation.

## Complete observation and exposure sequence

The common 14-value prefix eligibility condition is scientifically defensible **as a conditional dual-channel acquisition panel**. It gives L-only and snapshot arms the same observations/availability mask as history, while denying those arms unused D feature values. This estimates D benefit on successful dual-channel acquisition; it cannot estimate unconditional value when SG acquisition fails. A negative/error/absent/nonnumeric/nonfinite selected observation makes that row invalid, zero remains valid, and no clipping/replacement/interpolation is allowed. The rule deliberately differs from historical HCT116's all-images-required abort and must not be applied retroactively to that study.

Freeze these implementation definitions before exposure:

- Coverage denominator is **all frozen named entries assigned to that role and screen**, not groups, prefix-valid rows, author-QC rows or scored rows. Numerator is prefix-and-target complete rows. The two-entry conflict group contributes two entries to MAE/coverage but one group to group counts/bootstrap.
- Interpret the group minimum as the intersection of the three screen-specific sets of complete-case contributing groups; define whether a two-entry group contributes when at least one entry is complete in each screen. The natural minimal reading is at least one per screen. Report this explicitly. The minimum is a guard, not an instruction to drop every row whose group is incomplete elsewhere.
- Row-level invalidity is handled by the fixed common mask; overall eligibility for a useful-gain decision is governed by the registered95% and group guards. Do not silently turn any single invalid value into a new all-panel abort, or silently ignore the guards. If an additional semantic/container failure is meant to abort globally, identify that failure before values.
- If train/validation coverage already fails, report qualification insufficiency without model selection or unnecessary test-target exposure. If failure first becomes known at test-target qualification, preserve the already saved predictions; no target/threshold/model/cohort repair follows. A qualification failure is not a D-channel negative.

The proposed order protects test labels if enforced in code: prefix all roles; L72 train/validation only; fitting/selection/refit; save **all four selected-arm forecasts plus both fixed-anchor forecasts**, and abstentions for every fixed test entry×screen; hash/close that prediction file; only then authorize test L72. Prediction arrays must exist independently of target-validity filtering, with the actual L24 anchor. Test-target validity may restrict the registered scored panel but cannot affect prediction construction, selected configs or eligibility-by-prefix. Test arrays must not leak into scaler fitting or hyperparameter decisions. Qualification after test exposure must not restart selection.

## Model and metric arithmetic

The stated base dimensions are correct:7 absolute live log values+6 anchored differences+3 slopes+3 screen one-hots=19. Snapshot arms add2=21; D history adds7 logs+7 ratios+1 slope=34. D-history contains both snapshot arms' information. Transform/ratio definitions and fixed physical times are explicit; future/time-grid completion is unnecessary.

The14configs are6Ridge+4HistGradientBoosting+4ExtraTrees. Four arms×(14trials+1refit)=60 model fits. Use identical role/row masks and y−s24 supervision; reconstruct predictions with the observed s24. Train-only scaling and train+validation-only selected refit are appropriate. The fixed persistence and OLS anchors are diagnostic and cannot substitute for a failed main comparison. Equal trials are an honest matched search budget, not equal wallclock/FLOPs or a proof about every possible direct predictor.

Specify the sample-weight normalization scale, not just equal screen totals. A natural choice is `N/(3*n_screen)` for each included row, hence sum weights=N and each screen total=N/3, recomputed separately for train and train+validation. A global weight scale changes Ridge's effective regularization, even though it does not change relative screen weights. Unweighted train-only StandardScaler moments remain allowed as preregistered. Validation selection must use the same three-screen macro MAE, with lexicographic tie-breaking and no test input.

Screen macro MAE is appropriate to the declared equal-screen application: equal weight for each of three screen-specific mean absolute log errors, with equal weight per eligible entry **within** a screen. It is not group-average MAE and should not pool all rows and accidentally overweight a better-covered screen. Recompute screen denominators after the fixed complete-observation mask. The .05log2 threshold is a pragmatic error-scale convention, not a direct3.5% reduction in raw density error or an assay noise estimate.

The paired role-group bootstrap should resample the367 frozen test groups, taking each selected group's entries, contexts, fixed missingness and all paired model errors together, then recompute each screen mean and the macro difference. The conflict pair remains one cluster with two entries; repeated sampled groups need actual multiplicity. This sensitivity describes sampling of these recorded-entry groups conditional on fitted models and fixed screens. It does not capture refit/model-selection uncertainty, biological-run uncertainty, or three independent replications. The protocol's point/per-screen decision rule is explicit and intervals must not become a new post-test pass criterion.

## Required scientific claim correction

Example countermodel: only D0 and D24 matter and each adds complementary static information about L72; all intermediate D values are irrelevant. A history model given both endpoints can then outperform each separate snapshot model. Thus the registered four-arm comparison can establish full-prefix D information beyond L-only and beyond either **individual** time point, but cannot establish that intermediate temporal history is necessary beyond joint endpoints.

Two valid pre-exposure resolutions:

1. Keep the four-arm budget and narrow every dynamic-history verdict to “full-prefix D exceeds either single-time snapshot”; explicitly leave intermediate-history contribution untested. This is the simpler resolution for the main information gate.
2. Add a `dead_endpoints` arm receiving z0,z24 and the two corresponding raw ratios (23total features) under the same14configs+refit, freeze its comparison and thresholds now, and require history to beat it as well. Five arms imply75fits. This tests extra intermediate-history features beyond endpoints, still without identifying a biological mechanism.

This is not permission to add endpoints after an exposed disappointing result. Resolve before any assay conversion; record the rationale in an append-only pre-exposure addendum. The main L-only versus D-history information claim does not depend on which resolution is chosen.

## Decision and forthcoming code audit

Support the main narrowly conditional experiment after the claim correction and operational definitions are frozen. No useful-gain verdict or scientific qualification can be given before actual values. The next authorized work is a **non-fit code audit** after root notifies that code is ready, including exact cell/stage whitelists, source hash checks, role maps, weighting/macro arithmetic, bootstrap multiplicity, fixed model budget, and test-target independence. This independent draft is saved first and will not be silently rewritten to reflect peer/code findings; later exchanges go in separate records.

Historical HCT116 observation-domain failure, prior compound/RSI negatives and all frozen STOPs remain unchanged. This standard direct-predictor test supplies no new algorithm, world-model advantage, agent benefit, inherited capability or improvement-of-improver result. A qualified failure stops expansion of this exact registered fixed-dose24→72h application; it does not prove universal absence of D information.

Reviewed metadata hashes: IDENTITY_SUMMARY `ddc94524f8060dda78b18caa772469fb506ee4be080220a33d7623afb3ce68ac`; SECOND_MARKER_PROJECTION `07c0c0b78ec0eb837bb790321cff89ec4482ab072a84db8eca80a0e629898044`; METADATA_COLLISIONS `90eb9245b29adae93f8ef796b950f0dd3925275ff61666acb90ee3467c67b74f`; RAW_ACQUISITION_FINAL `c0db79a26267ced29dfa5c96f0cc5c7cba0f7cf291228b900010acedf57c8f82`.
