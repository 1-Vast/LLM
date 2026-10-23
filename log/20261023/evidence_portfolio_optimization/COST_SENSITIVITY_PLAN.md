# Post-result cost-aware sensitivity

The result reviewer noted that resampling fixed choices by SIDM may change each arm's total cost differently in a bootstrap draw. This separate post-result sensitivity divides each arm's sampled success count by its own sampled paid-read cost before taking differences. It reuses observed artifacts, changes no nomination or primary result, and remains conditional fixed-policy uncertainty rather than prospective reallocation inference. It is not a new test gate.
