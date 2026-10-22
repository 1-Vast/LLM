# Pre-outcome engineering correction: sanitise standardised molecules

The first synthetic salt/stereoisomer invariant failed: RDKit reported RingInfo
not initialised after FragmentParent/Uncharger. This same software fault wrongly
quarantined 51 known source structures. It is not biological/identity evidence.
Five other initial invariants passed. Full failure output is test_reservation.txt.

No functional, morphological or count value has entered split construction or
development. Add Chem.SanitizeMol after uncharging, before scaffold/fingerprint
calculation. Do not alter the fixed salt, ratios, scaffold rule or similarity
threshold. This is an engineering repair before outcome opening, not a reroll.

The first RESERVATION.json, SPLIT_STATUS.json and console remain unchanged and
are INVALID_FOR_EVALUATION. Exact first code is preserved as
research/oasis_evaluation_contract_20261021/reserve_chemistry_initial_failed.py.
Its SHA256 is 2327a3720d03dbb0477bec1c4b0fe161f6446395c366014b7550155a5c5b41a3.
The repaired code writes RESERVATION_v2.json and SPLIT_STATUS_v2.json only; the
existing-map refusal still applies. v2 cannot be used until repaired invariants
and source/protocol/role integrity are verified. No old study is changed.
