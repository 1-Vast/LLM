# Static pre-access implementation review

2026-10-23. Read reciprocity.py and test_reciprocity.py; did not run the real-data command, load NPZ values or inspect outputs. Algebra, feature orientation, graph log-ratio sign and source-only path restrictions inspected.

Initial version has one blocking classification issue: the prospective exact incompatibility status uses a diagonal <=1e-12 and one-sided numerical zeros. A positive diagonal below that tolerance is compatible with SPD, and two nonzero reciprocal entries on opposite sides of the numerical-zero threshold can be exactly compatible under extreme positive force scales. Thus these tolerance categories cannot themselves prove exact incompatibility of saved numbers. They are valid descriptive accounting.

Requested root fix before access: retain tolerance categories, add exact nonpositive diagonals, exact one-sided zero patterns, exact opposite-sign reciprocal pairs, and base exact incompatibility only on actual exact sign/support conditions (sign comparison avoids product underflow). A tiny-positive SPD positive-amplitude synthetic example must not be rejected. Add distinct near-zero-diagonal accounting so readers do not confuse it with nonpositive entries.

Other inspected logic is reasonable: R[:,j] orientation, exact alias mapping, all 103 targets, no response-dependent selection, source hash binding, no auto repeat, normalized triple defects, and graph cycle checks beyond triangles. Triangle inconsistency is currently descriptive, not an additional tolerance significance gate. Necessary-only output when exact signs/support do not fail is conservative and does not certify symmetrizability or SPD. The synthetic nonlinear-potential example correctly limits an overbroad interpretation.

Await corrected static version before lifting this implementation blocker. This is a code classification issue, not an observed biological result or candidate failure.
