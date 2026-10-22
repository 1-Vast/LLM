## Choice: Watermelon lineage-fate prediction, not TG-GATEs

I pick the **PC9 osimertinib Watermelon lineage dataset** (PMC9209846; GSE150949). Reasons: it is the only authenticated source here with genuinely paired *state* (RNA expression programs / cell-cycle score) and *function/history* (mCherry dilution) axes, a frozen lineage-level split (source309/dev84/test89; sensitivity 134/35/37 on the 206-lineage set), and a sanctioned forward-prediction question that is *not* the stopped selection-vs-transition identification.

TG-GATEs is rejected for this role: early-RNA→later-toxicity prediction is already the known EGR1/ATF3/GDF15/FGF21 line (DOI 10.1038/tpj.2013.39), the three-dose menu is toxicity/solubility-selected (not a clean dose series), treated RNA is not a free input for a new compound, and with functional signal unopened I cannot honestly claim headroom or a claim distinct from the already-suggested residual kernel. A distinguishing claim there would be speculation dressed as design.

Watermelon limits, stated up front: it can prove **within-dataset, held-out-lineage predictive structure under this sorting/capture design**. It cannot prove natural survivor prevalence, growth/death, reservoir depletion, drug efficacy, selection-vs-transition attribution (that is killed by the prior synthetic equivalence check), cross-culture generalization (n=2 cultures), or broad C4/RSI. Query units are culture/time+sort/capture/library bundles, not barcode labels; the lineage split is within-bundle, so non-independence is real and must be handled by cluster bootstrap.

---

## 1. Application, world, units, ordering, exposure, split, paid menu

**World (W):** \(P(y \mid x_{\le 7})\), where \(y\) = day14 capture-gate fate (primary binary: cycling vs noncycling with medium excluded as a pre-registered exclusion; secondary ordinal 3-class), and \(x_{\le 7}\) = {day0 founding expression-program score(s); day3 and/or day7 expression-program scores; RNA cell-cycle score; cumulative mCherry division count and its day0→3→7 increments}.

- **Input:** per-lineage feature vectors joined on unique original rownames to authenticated matrix columns; mCherry dilution summaries from the H2B-mCherry channel. Combined-replicate `clone_size`/`fate` columns are prohibited as inputs.
- **Output:** predicted day14 gate label + probability for each held-out lineage.
- **Time ordering:** predictors strictly day0–day7; label day14. No day14 expression, no day14 mCherry in the history channel. Early history predicting a late gate is forward prediction, not circular; using day14 mCherry would be circular and is forbidden.
- **Biological unit:** lineage (30nt-barcode-defined clone). **Statistical unit:** lineage, with cluster bootstrap over culture/time+gate bundle. **Paid/adaptation unit:** whole culture/time+sort/capture/library bundle (never individual barcode).
- **Allowed source/target exposure:** source309 = train; dev84 = model selection + adaptation budget; test89 = one-shot after freeze. Target-culture held-out exposure is not available (n=2 cultures), so no cross-culture claim.
- **Paid action menu (observational analogue, not wet-lab cost):** (i) adaptation label-reveal budget \(k \in \{0,10,35,84\}\) dev/test lineages; (ii) refit calls; (iii) bootstrap/compute evaluations. All counted identically across controls.
- **Source/later split:** source309 → dev84 (selection, channel allocation, adaptation) → test89 (final). Horizon split: day7→14 (dev-facing source) vs day3→14 (transfer test). Gate split: cycling vs noncycling primary.

**Authentication gap that must close first:** raw per-gate lineage counts and the day14 gate definition (which FACS channels define cycling/medium/noncycling) are not yet read. If the gate is *day14-mCherry-threshold-defined only*, then predicting it from day7 history is largely dilution persistence and the mechanism must be re-scoped to an RNA-derived outcome (day14 RNA cell-cycle score / expression-program score). This is not a nuisance; it determines whether the claim is interesting or near-tautological.

---

## 2. One falsifiable mechanism claim

> **H1 (gate-conditional channel allocation):** Conditional on day0 founding expression state, the day14 capture-gate fate of a held-out PC9 lineage is predicted by an *asymmetric* allocation in which RNA expression-program scores carry the cycling-vs-rest contrast and cumulative mCherry division history carries the noncycling-vs-rest contrast; a symmetric both-channel conditional model, each single-channel model, and an ordinary conditional mixture on the same features underperform this allocation by a pre-set margin on frozen test lineages, and the allocation rule selected on the day7→14 dev horizon transfers to the day3→14 test horizon within a pre-set tolerance.

This is a *prediction/transfer* statement, not a flow-attribution statement. Operator novelty is low (ordinary conditional prediction with a fixed channel allocation). The empirical contribution is whether the allocation is real and transferable under this design — nothing biological is claimed as ours beyond the paper's known lineage/program results.

---

## 3. Operations (≤12 lines)

1. Freeze hash split (source309/dev84/test89) and the 206-lineage sensitivity set; freeze feature definitions and the medium-excluded binary primary.
2. Authenticate matrix column keys for expression joins; forbid `clone_size`/`fate`; do not assert sampling weights.
3. Build four families on source: expression-only, history-only, symmetric both, ordinary conditional mixture/low-rank on identical features.
4. Fit on source; select family, allocation and hyperparameters on dev by a pre-registered criterion; write down the allocation rule.
5. Evaluate the selected allocation on test lineages (one shot): balanced accuracy/AUROC, cluster bootstrap by bundle.
6. Permutation control: permute history within gate; refit; the allocation's edge over expression-only must fall ≥50%.
7. Cell-cycle-score-only baseline; compare (this is the "is it just RNA cell-cycle" kill).
8. Horizon transfer: apply the dev-frozen rule to day3→14; test degradation against tolerance.
9. Parameter inheritance: refit-on-source + calibrate-on-dev vs full refit; compare test metric.
10. Program inheritance: freeze the revision rule from dev, apply to test without re-search; compare to equal-budget re-search on test.
11. C4: old improver vs new improver at identical later solver/history/permissions/budget on test; primary = equal metric at ≤50% adaptation queries, or +0.03 at equal queries.
12. Report all pre-registered metrics and the 206-lineage sign check; no post-hoc metric switching.

---

## 4. Closest same-information ordinary explanation; reproduction and differentiating test

The prior synthetic equivalence check is the honest ordinary explanation: the endpoint expression-state × division-history joint is reproduced exactly by an ordinary conditional mixture, so any "mechanism" that merely re-reads that joint is not identifiable. My H1 must therefore survive as a *held-out-lineage, forward-in-time* prediction, not as attribution.

- **Constructive reproduction:** implement the ordinary conditional mixture and a symmetric both-channel predictor on the identical feature set and split. If either matches the gate-conditional allocation within the pre-set margin on dev, H1's asymmetry claim is not supported and the ordinary model stands.
- **Differentiating test:** the permuted-history control plus the cell-cycle-score-only baseline. If the allocation's edge survives history permutation but the symmetric model's edge does not, the specific lineage history is doing work; if permutation leaves the edge, the edge was marginal-distribution leakage and H1 dies.

**Honest classification:** operator novelty ≈ none; the value is an empirical, transferable *allocation rule*, which is exactly what can be inherited.

---

## 5. Smallest decisive kill/check and pre-set criteria (before target opening)

**Smallest decisive check (cheapest first):** authenticate the day14 gate definition and per-gate lineage counts. If the gate is day14-mCherry-threshold-defined only, re-scope the outcome to day14 RNA-based cell-cycle/program score before any fitting; otherwise proceed with H1 as stated.

**Pre-registered criteria (provisional margins — must be justified by a source/dev-only power/precision analysis before test opens; these are within-dataset prediction margins, not calibrated assay noise):**

- **Headroom gate:** best source-trained model must beat class-prior/majority on dev by ≥0.10 balanced accuracy, else stop.
- **Complementarity/asymmetry:** allocation beats best single-channel and symmetric both-channel by ≥0.05 balanced accuracy on dev, bootstrap 95% CI excluding 0.
- **Permutation:** history permutation reduces the allocation's edge over expression-only by ≥50%.
- **Transfer:** dev-frozen rule on day3→14 test within 0.05 of its dev metric.
- **Consistency:** sign preserved on the 206-lineage sensitivity set; report bundle-cluster CI.
- **C4:** new improver equals old improver's test metric at ≤50% adaptation queries, or beats it by ≥0.03 at equal queries.
- **Test discipline:** one-shot opening after freeze; all pre-registered metrics reported.

---

## 6. Controls and contrasts

- **Direct:** fit on source+dev, evaluate test.
- **Ordinary retraining:** full refit on source, no inheritance.
- **Continual learning:** source→dev→test sequential refit, with and without simple replay.
- **Active learning:** uncertainty-query dev lineages vs random at equal budget.
- **Simple mixture:** ordinary conditional mixture on identical features (primary ordinary competitor).
- **Equal-budget program search:** search the same model menu with the same evaluation count directly on test — the strongest anti-inheritance control.
- **World contrast:** world-model predictive distribution vs ordinary mixture on test.
- **Agent contrast:** revision procedure's decisions vs random/equal-budget search.
- **Parameter inheritance vs full refit; program inheritance vs re-search on test.**
- **Joint contrast:** both channels vs permuted-history vs each single channel.
- **C4:** old vs new improver at identical later solver/history/permissions/budget; later predictor strength alone is explicitly *not* improved improver. No superadditivity or unlimited acceleration asserted.

---

## 7. Abandon vs escalate

**Abandon the core if:** on frozen test, the best single-channel or symmetric both-channel model matches the gate-conditional allocation within the pre-set margin, or the permutation control shows the allocation's edge is marginal-distribution leakage, or the dev-frozen rule fails the day3→14 transfer tolerance, or the C4 contrast shows the new improver needs more adaptation queries at equal metric. In any of these, drop the lineage-history allocation channel and keep the ordinary conditional predictor; do not rename the mechanism.

**Warrants deeper independent opposing review if:** the allocation beats each single channel and the symmetric model by the pre-set margin with CI excluding 0 on test, survives within-gate history permutation, transfers across horizons within tolerance, and the new improver meets the C4 criterion at equal budget. That positive would justify an independent re-analysis with an external dataset and an explicit n=2-culture caveat before any architecture is built.

---

## 8. What is hypothesis vs authenticated

**Authenticated (no new fit):** split sizes (309/84/89; 482 lineages; 206-lineage 134/35/37), unique original rownames as expression join keys, H2B-mCherry dilution as a separate history channel, three day14 capture gates, two cultures, and the prior synthetic equivalence check. **Not authenticated / unread:** expression matrix columns, raw per-gate lineage labels, gate definition, sampling weights, per-gate lineage counts, any effect size or outcome value. **Hypothesis:** H1 and all pre-set margins. I have not read expression or gate labels for this candidate, and I am not claiming headroom, power, or calibrated assay noise.