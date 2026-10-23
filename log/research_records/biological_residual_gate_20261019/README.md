# P0 Biological Residual Information Gate, 2026-10-19

Does biological information about how a drug intervenes add reproducible, transferable, decision-relevant value beyond
functional drug similarity? Data: the exposed Jaaks 2022 screen, so this is development evidence. This study also
audits `../action_substitution_20261019`.

**Decision: UNDERPOWERED by the frozen rule. For this action space the evidence supports STOP.**

- **Gate 1 (UNDERPOWERED).** Target annotation adds +2.8% beyond the functional kernel (family CI -0.9% to +7.7%;
  real vs shuffled targets p = 0.010), and balanced accuracy is lower.
- **Gate 2 (UNDERPOWERED).** Biological mismatch does not predict B5's consequential errors on held-out families
  (AUROC 0.48). Kinobeads binding was worse than B5 (sibling study).
- **Gate 3 (FAIL).** The reproducible opportunity in choosing among same-family alternatives is 0.012 ECB-like units,
  below the 0.02 minimum useful gain.
- Feedback on the B5 prior still helps: -16% MSE, balanced accuracy +0.028.
- `verify.py`: ALL OK.

| File | Content |
|---|---|
| `REPORT.md` | Deliverables A-H: audit, corrected interpretation, decomposition, residuals, decision opportunity, data qualification, recommendation, decision |
| `PROTOCOL.md`, `FREEZE.json` | Frozen P0 protocol, with hashes of own and imported files |
| `AUDIT.json` | Entities, family definitions, coverage, replicate independence, decision confusion, refinement arithmetic |
| `P0_RESULT.json` | Write-once result |
| `p0_units_S.csv`, `p0b_units.csv`, `p0c_sets.csv` | Unit tables behind P0-A, P0-B and P0-C |

Code (`/d/anaconda/envs/maestro/python.exe`; run from this folder):

```
python audit.py        # AUDIT.json (reads the action-substitution records; no new outcome)
python freeze.py       # FREEZE.json (refuses if P0_RESULT.json exists)
python p0.py [--smoke] # P0_RESULT.json + unit tables (write-once)
python verify.py       # hashes + recomputation
```

No LLM or paid call, no new download, no sealed tier. Nothing committed.
