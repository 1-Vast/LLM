# Block K: measure or predict (kinetic horizon, 2026-10-10)

The question is whether a frozen virtual cell's forecast of the **early** (24 h) cell state can
replace measuring that state when the decision concerns a **later** fate (5-day viability). If it
cannot, the block asks why:
* **no ceiling**: even perfect early knowledge adds nothing beyond a strong cheap prior;
* **no transport**: the forecaster fails in the decision's own platform;
* **timing**: the informative state appears later.

The protocol is registered in [PROTOCOL.md](PROTOCOL.md) and was frozen on 2026-10-10T09:13:29Z
(`FREEZE.json`). Results are in `RESULTS.json`, and independent checks in `VERIFIED.json`.

## Data and units

| Source | Identity | Units |
|---|---|---|
| Tahoe-100M filtered obs and X_hvg | `State-Tahoe-Filtered@fdf87abe` | 16 confirmation reference lines with PRISM (15 development) |
| STATE ST-HVG-Tahoe zero-shot | `final.ckpt` sha256 `2c9b2e74...` | forecasts from each line's own control cells |
| MIX-Seq (McFarland 2020, scPerturb copy) | sha256 `94a72400...` | 48 unseen confirmation lines (24 development) in pool A; pool C replicate; 24-line trametinib time course (pool D) |
| PRISM Repurposing 19Q4 | figshare 9393293 v4 | 5-day viability |
| DepMap 19Q4 CCLE expression | figshare 11384241 v3 | DepMap-scale prior over about 400 external reference lines |

Splits are `SPLIT.json` and `MIXSEQ_SPLIT.json` (seed 20261010), written before any outcome was
parsed. The sealed extractors refuse confirmation and time-course tiers before the freeze, by name
(`TIER_SEALED`). The three Tahoe zero-shot lines' PRISM values remain sealed.

## Results

**Development gate** (`GATE.json`; point estimates, MUB 0.05 r):
* MIX-Seq 24 h to 5-day: **MEASURE_EARLY**. The ceiling was +0.139; STATE's increment was -0.150.
* Tahoe 24 h to 5-day selectivity: **USE_PRIOR**. The ceiling was -0.182.

**Confirmation:**

| Test | Result | Verdict |
|---|---|---|
| M1: 24 h measurement complements the DepMap prior (48 lines, 6 drugs) | -0.021 [-0.109, +0.078]; 4/6 drugs | **fail** |
| M2: STATE forecast added to the prior | -0.091 [-0.182, -0.005] | **transport refusal confirmed** |
| M2: STATE line-specific RNA skill | trametinib 0.059 [0.032, 0.082]; others about 0. Split-half ceiling 0.35-0.79; MIX-Seq basal transfer 0.11-0.30 | no transport |
| M2: same line, Tahoe versus MIX-Seq observed response | r 0.13 (trametinib, 6 lines); about 0 for the other drugs | platform-bound |
| M2: same platform, pool A versus pool C trametinib | context r 0.65; generic r 0.91 (32 lines) | reproducible within platform |
| M3: top-10 lines, measurement policy minus prior | -0.061 [-0.165, +0.169]; 2/6 drugs | **fail** |
| M3: STATE policy minus prior | -0.127 [-0.250, +0.085] | not better |
| T1: when to observe (trametinib, 24 lines) | response magnitude r with 5-day: 3 h 0.21, 6 h 0.25, 12 h 0.31, 24 h 0.56, 48 h 0.68. Increment over prior: 24 h +0.11 [-0.06, 0.32]; 48 h +0.16 [0.01, 0.36] | information accrues late |
| T2: temporal fingerprint | STATE's 24 h forecast matches MIX-Seq's 12 h response best (generic r 0.43 at 12 h vs 0.37 at 24 h and 0.25 at 48 h). Tahoe's observed 24 h response peaks at 6 h (0.51). The scale never reaches 1 (at most 0.58). | no horizon identity across platforms |
| T3: kinetic readout as a rate | pooled r 0.11 [-0.04, 0.24] | not supported |
| K1: Tahoe 24 h early state over the CCLE prior | -0.107 [-0.155, -0.059] | **USE_PRIOR confirmed** |
| K2: potency, kinetic vs share | 0.505 vs 0.388; difference +0.117 [-0.084, +0.363] | direction replicated, CI includes 0 |
| K3: G1-shift sign for top-variance drugs | +0.136 [+0.002, +0.254] | sign replicated |

**Post hoc** (labelled; `posthoc/`):
* A paired re-analysis on common lines leaves M1-M3 unchanged.
* The development gate's own interval was [-0.049, +0.298]. A lower-bound rule would have
  abstained.

**Verification.** Freeze precedence, gate arithmetic, exact rerun and poisoning invariance pass.
The independent arithmetic check **failed** because of an unpaired estimand in the frozen evaluator
(`DEVIATIONS.json` D1). The paired re-analysis gives the same verdicts.

## Interpretation and limits

The virtual cell's failure here is a transport failure, not only a ceiling failure. The
line-specific response it learned does not carry to another platform. It does not even carry for
the same lines' observed Tahoe responses, although the MIX-Seq response is reproducible between
MIX-Seq experiments (r 0.65).

For this decision, measuring at 24 h did not beat a strong DepMap-scale prior on independent
lines. In the trametinib time course, the informative signal arrived at 24-48 h, and only a 48 h
measurement added to the prior.

The early cell-cycle direction (G1 accumulation) relates to later fate with a drug-class-dependent
sign:
* for the most variable, largely cytotoxic Tahoe drugs, G1 accumulation means relative sparing
  (K3);
* for trametinib it means sensitivity (T1, G1 shift r -0.59 at 24 h).

**Limits:**
* There are 48 and 16 confirmation lines, six and 217 drugs, and a single time-course drug.
* MIX-Seq has about 35-60 cells per line and condition.
* PRISM is a different assay (5-day, 2D, barcoded pools) from both single-cell platforms.
* The candidate STATE gene order is supported by line identity (18 of 18) but not certified by
  lineage.
* No mechanism, efficacy or general dual-core claim is made.

## Promoted

* `src/maestro/world_model_value.py`: `IncrementEstimate`, `plan_measure_or_predict`. This is the
  interval rule: ADMIT, MEASURE_EARLY, USE_PRIOR or ABSTAIN. It is a conservative correction
  motivated by D4; it has not been validated as improving decisions.
* `tools/evaluation/increment.py`: the paired increment with a unit bootstrap. It reproduces
  `posthoc/paired_reanalysis.json` exactly.
* `tools/analysis/platform_identity.py`: the cross-platform axis identity check. It reproduces
  18 of 18, and its docstring says that passing it does not imply response transport.

The kinetic readout, STATE use on non-Tahoe platforms and the measurement-first policy are **not**
promoted.

## Reproduction

```text
python split.py; python drug_match.py; python mixseq_index.py            # written once; refuse to overwrite
python prism_extract.py {development,mix_development,external_mix,external_tahoe}
python mixseq_extract.py {A_control,C_control,D_control,A_treated_dev}
python mixseq_state.py {A,C,D} v1                                         # GPU, about 2 min in total
python gate.py; python freeze.py                                         # before freeze only
bash run_sealed.sh                                                       # sealed tiers, evaluate.py, verify.py
python posthoc/paired_reanalysis.py; python posthoc/gate_uncertainty.py
python make_receipt.py
python -m pytest test_kinetic_horizon.py
```

Bulk arrays are in `data/external/kinetic_horizon_20261010/` (git-ignored). Downloads total
391 MB of PRISM, 1.46 GB of MIX-Seq and 301 MB of CCLE. STATE used 5,421 forward sets in 143 GPU
seconds. No LLM was called.
