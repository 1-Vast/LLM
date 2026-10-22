# Registered logic audit: does memory prove a world model advantage?

2026-10-22. Before running the code, freeze the skeptical four-row construction.
Two equally frequent histories A/B share exactly the same current size and
slope. Each allows actions C/D. Outcomes are XOR(history, action); there is no
measurement noise or hidden run factor. This is a synthetic logical diagnostic,
not a simulated biological benchmark, data fit, novelty proof or RSI experiment.

Compare (1) the optimal current-state/action-only prediction, (2) minimal
one-bit history state refinement, and (3) a direct conditional table receiving
the same history and action. Use all four exact cells, with equal weight; report
exhaustive squared error, not statistical confidence or out-of-sample accuracy.
Expected: 0.25, 0, 0 respectively. The objective is to **falsify the inference**
that improvement over current-state prediction alone identifies a world-model
contribution. A separate mutation checks that adding an accurate current marker
removes the current-state insufficiency. Another removes the two common-action
comparisons and must refuse to certify a collision from nonoverlapping actions.

Stop if the fair direct table matches the proposed minimal refinement. Do not
grow a learner or tune this example for a candidate win. Biological history
effects, empirical sample efficiency, agent benefit and RSI remain NOT_TESTED.
