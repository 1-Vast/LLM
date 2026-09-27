"""External-validation firewall, frozen baseline ladder and decision-focused evaluation for MAESTRO.

A package rather than a script folder, so its `statistics` module never shadows the standard
library for code it imports (`src/maestro/tool_analysis.py` and `src/virtual_cell/pathway_readout.py`
use the standard one). Run its entry points from the repository root with `python -m`.
"""
