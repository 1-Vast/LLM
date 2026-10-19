# Conditional pharmacological action units, 2026-10-19

This study asks four questions about same-target drugs (A, A'), a partner B and a cell line c:

1. Is substitutability (A' standing in for A) reproducible?
2. Can it be learned beyond strong baselines?
3. Does it transfer to unseen implementations?
4. Can counterexamples refine it, so that an agent can use it for diagnostic experiments and combination redesign?

Data: Jaaks 2022 GDSC anchored combination screen, which MAESTRO had already exposed in October 2026. Everything here is
therefore development evidence.

**Decision: NARROW.** The programme as briefed is STOP.

- **Gate: CONDITIONALLY QUALIFIED.**
  - Swap contrasts reproduce across seeding dates: r = 0.31.
  - The reproducible part is partner-specific, not partner x line: conditional share 0.08.
- **Phase 2 (unseen implementations), interaction endpoint: NOT_BEYOND_BASELINE.**
  - The frozen learned substitution model is 49% worse than a functional-similarity kernel.
  - Post hoc, the same-target sibling copy is beaten by that kernel and ties the identity-free partner mean.
- **Phase 2, efficacy endpoint: INCONCLUSIVE.** Potency matching does about as well.
- **Phase 3 (counterexamples), interaction endpoint: PARTNER_SPECIFIC_REFINEMENT.**
  - One probe of the same partner cuts error by 17%. Probing a different partner makes it worse.
  - It has no decision value: equivalence calls at epsilon 0.03 do not move, even when every unit is probed. So agent
    value is bounded at zero.
- **Independent confirmation: BLOCKED** (no untouched local tier).
- `verify.py`: ALL OK.

| File | Content |
|---|---|
| `REPORT.md` | Results in the brief's priority order, decision, limits |
| `PRIOR_ART.md` | External (PHAROS and others) and internal novelty gap analysis |
| `PLAN_P1.md` | Reproducibility gate, written before any response column was read |
| `PROTOCOL_P2.md`, `FREEZE.json` | Phase 2 leave-one-implementation-out protocol and freeze |
| `PROTOCOL_P3.md`, `FREEZE_P3.json` | Phase 3 refinement protocol, frozen before any phase 2 result existed |
| `DEVIATIONS.md` | Deviations and disclosures |
| `CENSUS.json` | Design-only eligibility census |
| `REPRO.json`, `DECOMP.json` | Gate and variance decomposition |
| `LOFO_*.json`, `lofo_units_*.csv` | Phase 2 results (write-once) and partner-level unit tables |
| `REFINE_*.json` | Phase 3 results (write-once) |
| `POSTHOC.json` | Post hoc reference comparison (not pre-registered) |

Code (maestro conda env `/d/anaconda/envs/maestro/python.exe`; run from this folder):

```
python plates.py                    # cache/plates.csv from the raw-data zip (seeding date per plate; no response read)
python census.py                    # CENSUS.json (design only)
python repro.py                     # REPRO.json (write-once gate)
python repro_decomp.py              # DECOMP.json (write-once)
python freeze.py                    # FREEZE.json (write-once)
python lofo.py SYNERGY_DELTA_AUC    # LOFO_*.json (write-once); also SYNERGY_OBS_AUC; --smoke for an execution check
python refine.py SYNERGY_DELTA_AUC  # REFINE_*.json (write-once); also SYNERGY_OBS_AUC
python posthoc.py                   # POSTHOC.json
python verify.py [--data]           # read-only verification
```

Source files are in `data/external/gdsc_combinations/jaaks2022_figshare/`: the original and validation fitted files, the
raw-data zip and the glossary. They were downloaded 2026-10-19 with the user's approval, about 271 MB. The original
fitted file's MD5 is `786589e5eb556670cc7d24356487f8fd`.

No LLM or paid call, no sealed tier, nothing committed.
