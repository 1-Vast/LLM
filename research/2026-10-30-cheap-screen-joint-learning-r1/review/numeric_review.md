# Independent numeric review: E001

Independent implementation was frozen before primary results or implementation were read. Primary implementation was never imported or read. The frozen result SHA256 is 91ba1ba7d035b63b4ec21b1467a74480b9293886963274f94ccbde831a46496a.

1205 scalar/hash/Boolean comparisons, 0 discrepancies at relative 1e-9 or absolute 1e-7 tolerance. All 192 wells, raw/retained event counts, control calibration quantities, 20 target calibrations and outcomes, 80 predictions and signed/absolute normalized errors, final technical envelopes and overlaps, all four preparation MAEs, and gain-minus-constant contrasts are covered. All 48 groups per export are retained. Detailed per-well calculation outputs remain in the local independent result artifact and are omitted from this publication; the aggregate values below are descriptive only.

| Preparation | Gain MAE | Add MAE | Constant MAE | Control MAE | Gain − constant MAE | Envelope overlap |
|---|---:|---:|---:|---:|---:|---:|
| E3CA | 0.907222 | 0.332121 | 0.447514 | 0.571891 | +0.459708 | 2/5 |
| E3CB | 0.403401 | 0.635928 | 0.376609 | 0.495609 | +0.026792 | 2/5 |
| E3DA | 0.489592 | 0.669859 | 0.499654 | 0.743594 | -0.010062 | 3/5 |
| E3DB | 1.237203 | 1.338385 | 1.207022 | 1.289832 | +0.030181 | 2/5 |

The exact common-gain restriction is not supported as a general predictive replacement across these five interventions and preparations. Gain is worse than constant interaction in three preparations; its small advantage in E3DA does not repeat in E3DB. Eleven of twenty gain prediction envelopes do not overlap observed technical-well ranges. Taselisib departs in both BxPC3 preparations, while trametinib departs in both AsPC1 preparations. These are descriptive observations about the prespecified full set, not selected validation subgroups. All qualifying controls merely make the denominator well defined; they do not validate common gain.

This is calibration-conditioned target holdout in one existing assay, with two source-described independent screenings/preparations per line. Original Par18 already exposes inhibitor-dependent response patterns. Par57 gives different cytokine doses by line (AsPC1 10 ng/mL; BxPC3 1 ng/mL); Par59–60 describes capture-bead sandwich-assay PE readout and APC-based capture-bead gating. The exported PE-only channel cannot verify that original gate. MFI is not secretion concentration without a calibrated mapping. Source minmax scaling and apoptosis correction were deliberately not used, per protocol. This computation yields no cell/molecular mechanism, external validation, biological-noise guarantee, CI, p-value, new algorithm, or acquisition advantage.

B_const is the scientifically relevant competing restriction; B_add alone is inadequate for establishing common gain. The gain restriction is ordinary proportional response/rank-one structure, and even arithmetic agreement cannot establish its scientific validity. Negative/crossing drug effects were retained and interval multiplication used all endpoint products. Broad technical envelopes can leave some target discrimination uninformative; overlap cannot be read as confirmation. In particular, the all-control kappa ranges were E3CA [2.2020, 4.5193], E3CB [2.7484, 3.4867], E3DA [2.4592, 3.1408], E3DB [2.1984, 3.6071].

Independent numeric execution: wall 0.6610702000034507 seconds; process CPU 0.59375 seconds; zero network calls, external science API calls, or monetary cost. Review/comparison scripts are confined to review/.
