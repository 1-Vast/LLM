# Development log (pre-freeze; 2.5 uM search block only)

All entries are dated 2026-10-19 and precede `FREEZE.json`.

Development used only the HTS002 2.5 uM reads of the search block. The RSD study had already opened them (its search
block), and so had the heavy-tail development. No outcome of the decoupled layer was computed on any other block or dose
before the freeze. The 0.625 and 10 uM reads were opened earlier the same day by the heavy-tail test stage. This study's
development did not load them: the smoke run read only the 2.5 uM cache.

1. **Inputs read, no data.** These files set the design:
   - RSD: `REPORT.md`, `PROTOCOL.md`, `DEVELOPMENT_LOG.md`.
   - Heavy-tail: `REPORT.md`, `PROTOCOL.md`, `DEVELOPMENT_LOG.md`, `README.md`.
   - Code: the frozen `ht_core.py`, `ht_run.py`, `ht_data.py`, `rsd_core.py`, `rsd_run.py`.

   Facts taken from those reports:
   - Pooled over 0.625 and 10 uM, rsd's selected-pair 80% coverage is 0.698 and its optimism +0.030.
   - `ht_compound` (nu 20 in all 6 units) has selected-pair coverage 0.749 and optimism -0.003 on its own picks, but
     costs D2 -0.048.
2. **Design decisions, made before any decoupled-layer outcome was computed:**
   - **Interval model = the heavy-tail `ht_compound` rule.** Same geometry, same nu choice from the frozen
     reference-only utility, same ML scale. With this choice, `dec` and `ht_compound` differ only in the ranking, and
     `dec` and `rsd` differ only in the intervals: a factorial comparison.
   - **Likelihood-chosen nu (nu_ML) as a secondary arm** (`dec_ml`). For an interval model, a likelihood choice of nu is
     the natural alternative. It is not primary, to keep one pre-specified method.
   - **"Gaussian signal + compound noise" as a secondary arm** (`dec_noise`). It is the literal noise swap. It is not
     primary, because the Gaussian signal posterior assumed a base noise scale that the compound model rejects for noisy
     compounds.
   - **Fixed-definition baseline intervals.** For `raw`, `raw2` and `shrink` the noise comes from the fixed q = 0
     reference VC: flat-prior replicate noise for raw reads, and a scalar-reliability posterior for `shrink`. These
     arms existed only as decision arms before. Their coverage gives the zero-method reference for calibration.
   - **Primary readout = 0.625 + 10 uM.** This makes the numbers directly comparable to the heavy-tail pooled test.
     2.5 uM is secondary, because this study developed on its search block.
   - **Reads only from the existing heavy-tail caches.** The study refuses any dose without a cache and checks that
     the cache folder is unchanged after each load.
   - **Bootstrap, seed and stratification as in the heavy-tail pool.** The `rsd` and `ht_compound` intervals and the
     per-unit sums must then reproduce the frozen heavy-tail records. This is the pipeline check.
3. **Metadata check (treatment table only, no read values).** HTS002 has an 8-point dose series in the metadata. Doses
   other than 0.625, 2.5 and 10 uM exist but were not considered: they are the same compounds, this study does not
   know whether earlier MAESTRO studies opened them, and choosing a tier is the owner's decision.
4. **Unit tests** (`test_dc.py`, 8 tests, pass), covering:
   - the flat-prior raw/raw2 interval definitions, which are calibrated on simulated Gaussian replicates;
   - the bootstrap p values, Holm and the verdict rule;
   - write-once outputs;
   - refusal of an unopened dose (no cache written);
   - refusal of the confirmatory stage.
